import json
import os
import uuid
import time
from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import AnswerRelevancyMetric, HallucinationMetric, ContextualPrecisionMetric
from langchain_openai import ChatOpenAI
from app.api import graph
from app.config.config import LANGFUSE_ENABLED, OPENAI_API_KEY, OPENAI_EVAL_MODEL
from dotenv import load_dotenv

load_dotenv()

from deepeval.models.base_model import DeepEvalBaseLLM


class OpenAIEvaluator(DeepEvalBaseLLM):
    """Thin DeepEval wrapper around OpenAI — used only as the judge LLM.
    OpenAI paid tier supports 500 RPM, so DeepEval's parallel evaluation
    (23 cases × 3 metrics = ~69 concurrent requests) works without hitting
    rate limits.
    """

    def __init__(self):
        self.model = ChatOpenAI(
            model=OPENAI_EVAL_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0,
        )

    def load_model(self):
        return self.model

    def generate(self, prompt: str) -> str:
        res = self.model.invoke(prompt)
        return res.content

    async def a_generate(self, prompt: str) -> str:
        res = await self.model.ainvoke(prompt)
        return res.content

    def get_model_name(self) -> str:
        return f"OpenAI: {OPENAI_EVAL_MODEL}"


def load_dataset(filepath):
    with open(filepath, "r") as f:
        return json.load(f)


def run_evaluation():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    dataset_path = os.path.join(base_dir, "tests", "eval_dataset.json")
    dataset = load_dataset(dataset_path)
    dataset = dataset[:50] 
    # Initialize OpenAI as the evaluator judge (OPENAI_EVAL_MODEL)
    evaluator_llm = OpenAIEvaluator()

    correctness_metric = AnswerRelevancyMetric(threshold=0.7, model=evaluator_llm)
    hallucination_metric = HallucinationMetric(threshold=0.5, model=evaluator_llm)
    retrieval_metric = ContextualPrecisionMetric(threshold=0.7, model=evaluator_llm)

    test_cases = []
    node_results = []

    # Node-level accuracy counters
    total = len(dataset)
    correct_category = 0
    correct_action = 0
    correct_tool = 0
    correct_order_id = 0
    order_id_checked = 0

    print(f"Running LangGraph agent on {total} queries...")
    for idx, item in enumerate(dataset):
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        # If this test case depends on a previous turn (multi-turn entity persistence),
        # replay the previous message first in the same thread before the real input.
        if item.get("context_previous_message"):
            try:
                if LANGFUSE_ENABLED:
                    from langfuse.langchain import CallbackHandler
                    langfuse_handler = CallbackHandler()
                    graph.run(ticket=item["context_previous_message"], thread_id=thread_id, callbacks=[langfuse_handler])
                else:
                    graph.run(ticket=item["context_previous_message"], thread_id=thread_id)
                time.sleep(2)
            except Exception as e:
                print(f"  [Warning] Failed to replay context turn for item {idx+1}: {e}")

        max_retries = 5
        result = None
        for attempt in range(max_retries):
            try:
                if LANGFUSE_ENABLED:
                    from langfuse.langchain import CallbackHandler
                    langfuse_handler = CallbackHandler()
                    result = graph.run(ticket=item["input"], thread_id=thread_id, callbacks=[langfuse_handler])
                else:
                    result = graph.run(ticket=item["input"], thread_id=thread_id)
                break
            except Exception as e:
                err_str = str(e)
                if "rate_limit_exceeded" in err_str or "429" in err_str:
                    wait_time = (2 ** attempt) * 10
                    print(f"  [Rate limit hit] Waiting {wait_time}s before retrying...")
                    time.sleep(wait_time)
                elif "tool_use_failed" in err_str or "400" in err_str:
                    print(f"  [Model error] Skipping query {idx+1} — model tool calling issue.")
                    result = {"response": "Skipped due to model error.", "documents": []}
                    break
                else:
                    raise e
        if result is None:
            result = {"response": "Rate limit exceeded after retries.", "documents": []}

        # ---- Node-level structured checks (free, no extra API calls) ----
        actual_category = result.get("category")
        actual_action = result.get("action")
        actual_tool = result.get("tool_name")
        actual_account_id = result.get("account_id")

        exp_category = item.get("expected_category")
        exp_action = item.get("expected_action")
        exp_tool = item.get("expected_tool")
        exp_account_id = item.get("expected_account_id") or item.get("expected_order_id")

        category_match = (exp_category is None) or (actual_category == exp_category)
        action_match = (exp_action is None) or (actual_action == exp_action)
        tool_match = (exp_tool is None) or (actual_tool == exp_tool)

        correct_category += int(category_match)
        correct_action += int(action_match)
        correct_tool += int(tool_match)

        order_id_match = None
        if exp_account_id is not None:
            order_id_checked += 1
            order_id_match = (actual_account_id == exp_account_id)
            correct_order_id += int(order_id_match)

        node_results.append({
            "id": idx + 1,
            "input": item["input"],
            "category": {"expected": exp_category, "actual": actual_category, "match": category_match},
            "action": {"expected": exp_action, "actual": actual_action, "match": action_match},
            "tool": {"expected": exp_tool, "actual": actual_tool, "match": tool_match},
            "account_id": {"expected": exp_account_id, "actual": actual_account_id, "match": order_id_match},
        })

        # ---- Build DeepEval test case for final-answer quality ----
        actual_output = result.get("response", "No response generated.")
        retrieved_docs = result.get("documents", [])

        # IMPORTANT: for call_tool actions there is no RAG retrieval — the model's
        # grounding source is the tool's raw return value (result["tool_result"],
        # per app/api.py's chat_endpoint), not vector-store docs. Using
        # "No context retrieved." here made every correct tool answer look like
        # a hallucination and tanked Contextual Precision to ~0 across the board.
        tool_result = result.get("tool_result")
        is_rag_case = actual_action == "retrieve"

        if is_rag_case:
            retrieval_context = (
                [doc.page_content for doc in retrieved_docs]
                if retrieved_docs else ["No context retrieved."]
            )
        elif tool_result:
            retrieval_context = [json.dumps(tool_result, default=str)]
        else:
            retrieval_context = ["No context retrieved."]
            if actual_action == "call_tool":
                print(f"  [Warning] item {idx+1}: tool_result missing/empty despite "
                    f"call_tool action — check graph state propagation.")

        test_case = LLMTestCase(
            input=item["input"],
            actual_output=actual_output,
            expected_output=item["expected_output"],
            context=retrieval_context,
            retrieval_context=retrieval_context,
        )
        # Contextual Precision measures ranking quality of retrieved docs — it's
        # only meaningful for genuine RAG (`retrieve`) cases. Applying it to a
        # single synthetic tool_result "context" for call_tool cases is a
        # category error, so those are excluded from that metric below.
        # Actions "blocked" and "injection" are canned refusal responses by
        # design — they deliberately don't answer the (illegitimate) input and
        # aren't grounded in any retrieved/tool context. Running Answer
        # Relevancy or Hallucination on them is a category error (same issue
        # we already fixed for Contextual Precision on non-RAG cases): a
        # correct refusal will always score 0.00 relevancy against the user's
        # off-topic question, and "No context retrieved" will always look like
        # a hallucination mismatch. Node-level action-accuracy already checks
        # these were correctly blocked; skip them here.
        is_refusal_case = actual_action in ("blocked", "injection")

        test_cases.append((test_case, is_rag_case, is_refusal_case))

        status = f"category={'✅' if category_match else '❌'} action={'✅' if action_match else '❌'} tool={'✅' if tool_match else '❌'}"
        cat_name = item.get("expected_category", "general")
        print(f"[{idx+1}/{total}] {cat_name} — {status}")
        time.sleep(2)

    # ---- Print node-level accuracy summary ----
    print("\n" + "=" * 60)
    print("NODE-LEVEL ACCURACY (Classify / Router / Entity nodes)")
    print("=" * 60)
    print(f"Classify Node — category accuracy : {correct_category}/{total} ({correct_category/total*100:.1f}%)")
    print(f"Router — action accuracy           : {correct_action}/{total} ({correct_action/total*100:.1f}%)")
    print(f"Classify Node — tool selection      : {correct_tool}/{total} ({correct_tool/total*100:.1f}%)")
    if order_id_checked:
        print(f"Entity Node — order_id extraction   : {correct_order_id}/{order_id_checked} ({correct_order_id/order_id_checked*100:.1f}%)")

    with open(os.path.join(base_dir, "tests", "node_eval_results.json"), "w") as f:
        json.dump(node_results, f, indent=2)
    print(f"\nDetailed node-level results saved to tests/node_eval_results.json")

    # ---- Run DeepEval semantic quality metrics on final responses ----
    print("\n" + "=" * 60)
    print("FINAL RESPONSE QUALITY (DeepEval semantic metrics)")
    print("=" * 60)
    print("Starting DeepEval evaluation... This may take a few minutes as the LLM Judge grades the answers.")

    content_cases = [tc for tc, _, is_refusal in test_cases if not is_refusal]
    rag_cases = [tc for tc, is_rag, _ in test_cases if is_rag]
    refusal_count = sum(1 for _, _, is_refusal in test_cases if is_refusal)

    print(f"\n-- Answer Relevancy + Hallucination ({len(content_cases)} cases, "
        f"{refusal_count} blocked/injection refusals excluded) --")
    evaluate(content_cases, [correctness_metric, hallucination_metric])

    if rag_cases:
        print(f"\n-- Contextual Precision, RAG-only ({len(rag_cases)} cases) --")
        evaluate(rag_cases, [retrieval_metric])
    else:
        print("\n-- Contextual Precision skipped: no 'retrieve' action cases in this run --")

    print("\nEvaluation complete! Check DeepEval output above for detailed metrics,")
    print("and tests/node_eval_results.json for per-node accuracy breakdown.")


if __name__ == "__main__":
    run_evaluation()