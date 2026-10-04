import json
from app.config.config import CARDS_PATH
from app.agents.tools.persist import save_json

class CardTool:

    def __init__(self):
        with open(CARDS_PATH, "r") as f:
            self.cards = json.load(f)

    def save_cards(self):
        save_json(CARDS_PATH, self.cards)

    def find_by_last4(self, card_last4: str):
        card_last4 = str(card_last4).strip()
        for card_id, card in self.cards.items():
            if card.get("last4") == card_last4:
                return card_id, card
        return None, None

    def cards_for_account(self, account_id: str):
        account_id = str(account_id).strip().upper()
        results = []
        for card_id, card in self.cards.items():
            if card.get("account_id") == account_id:
                row = card.copy()
                row["card_id"] = card_id
                results.append(row)
        return results

    def find_card(self, card_id: str = None, card_last4: str = None):
        if card_id and str(card_id).strip():
            cid = str(card_id).strip().upper()
            if cid in self.cards:
                return cid, self.cards[cid]
        if card_last4:
            return self.find_by_last4(card_last4)
        return None, None

    def card_status(self, card_id: str = None, card_last4: str = None):
        cid, card = self.find_card(card_id, card_last4)
        if card is None:
            return {
                "success": False,
                "needs_clarification": True,
                "message": "Please share your card last 4 digits (e.g. 4521) or card ID (e.g. CRD-7001).",
            }
        card_copy = card.copy()
        card_copy["card_id"] = cid
        return {
            "success": True,
            "card": card_copy,
        }

    def block_card(self, card_id: str = None, card_last4: str = None):
        cid, card = self.find_card(card_id, card_last4)
        if card is None:
            return {
                "success": False,
                "needs_clarification": True,
                "message": "Please share the card last 4 digits to block (e.g. 4521).",
            }
        card["status"] = "blocked"
        card["blocked_on"] = "2026-09-15"
        self.cards[cid] = card
        self.save_cards()
        return {
            "success": True,
            "mutation": True,
            "message": f"Card ending {card['last4']} has been blocked.",
            "card_id": cid,
            "status": "blocked",
        }

    def report_lost_stolen(self, card_id: str = None, card_last4: str = None):
        cid, card = self.find_card(card_id, card_last4)
        if card is None:
            return {
                "success": False,
                "needs_clarification": True,
                "message": "Please share the card last 4 digits for lost/stolen reporting.",
            }
        card["status"] = "blocked"
        card["reported_lost_stolen"] = True
        card["blocked_on"] = "2026-09-15"
        self.cards[cid] = card
        self.save_cards()
        return {
            "success": True,
            "mutation": True,
            "message": f"Card ending {card['last4']} reported lost/stolen and blocked.",
            "card_id": cid,
            "case_reference": f"CASE-LS-{card['last4']}",
        }

    def card_replacement(self, card_id: str = None, card_last4: str = None):
        cid, card = self.find_card(card_id, card_last4)
        if card is None:
            return {
                "success": False,
                "needs_clarification": True,
                "message": "Please share the card last 4 digits for replacement.",
            }
        card["replacement_status"] = "requested"
        card["replacement_requested_on"] = "2026-09-15"
        self.cards[cid] = card
        self.save_cards()
        return {
            "success": True,
            "mutation": True,
            "message": f"Replacement card requested for card ending {card['last4']}. Delivery in 5-7 business days.",
            "card_id": cid,
            "replacement_status": "requested",
        }
