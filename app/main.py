import streamlit as st
import requests
import uuid

import os
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/chat")
st.set_page_config(page_title="Intelligent Banking Assistant", page_icon="🤖")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}

if "thread_id" not in st.session_state:
    new_id = str(uuid.uuid4())
    st.session_state.thread_id = new_id
    chat_num = len(st.session_state.chat_history) + 1
    st.session_state.chat_history[new_id] = {"title": f"New Chat {chat_num}", "messages": []}

active_thread = st.session_state.thread_id
active_messages = st.session_state.chat_history[active_thread]["messages"]

with st.sidebar:
    if st.button("✨ New Chat", use_container_width=True, type="primary"):
        new_id = str(uuid.uuid4())
        st.session_state.thread_id = new_id
        chat_num = len(st.session_state.chat_history) + 1
        st.session_state.chat_history[new_id] = {"title": f"New Chat {chat_num}", "messages": []}
        st.rerun()

    st.divider()
    st.markdown("### Previous Conversations")
    
    for t_id, data in reversed(st.session_state.chat_history.items()):
        is_active = (t_id == st.session_state.thread_id)
        icon = "💬" if is_active else "🗨️"
        
        if st.button(f"{icon} {data['title']}", key=f"btn_{t_id}", use_container_width=True):
            st.session_state.thread_id = t_id
            st.rerun()

st.title("🤖 Intelligent Banking Assistant")
st.write("Welcome! I can help with account balance, cards, UPI/NEFT transactions, KYC, policies, and dispute cases.")

active_messages = st.session_state.chat_history[active_thread]["messages"]

for message in active_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("How can I help you today?"):
    if len(active_messages) == 0:
        snippet = prompt[:25] + "..." if len(prompt) > 25 else prompt
        st.session_state.chat_history[active_thread]["title"] = snippet

    st.chat_message("user").markdown(prompt)
    active_messages.append({"role": "user", "content": prompt})

    payload = {
        "ticket": prompt,
        "thread_id": active_thread
    }

    try:
        with st.chat_message("assistant"):
            def token_generator():
                with requests.post(
                    API_URL,
                    json=payload,
                    headers={"X-Thread-ID": active_thread},
                    stream=True,
                    timeout=60
                ) as r:
                    if r.status_code == 429:
                        yield "🚨 Too many requests! Please wait a minute before sending another message."
                        return
                    elif r.status_code == 500:
                        yield f"🚨 **Internal Server Error:**\n\n```\n{r.text}\n```"
                        return
                    elif r.status_code != 200:
                        yield f"🚨 **Error {r.status_code}:** {r.text}"
                        return
                        
                    for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
                        if chunk:
                            yield chunk

            final_response = st.write_stream(token_generator())

        active_messages.append({"role": "assistant", "content": final_response})

    except requests.exceptions.ConnectionError:
        st.error("🚨 Error: Could not connect to the FastAPI backend. Make sure you are running 'uvicorn app.api:app' in another terminal!")
    except Exception as e:
        st.error(f"🚨 An error occurred: {str(e)}")
