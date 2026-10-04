import json
from datetime import datetime

from app.config.config import TICKETS_PATH , RESOLVED_TICKETS_FILE
from app.agents.tools.persist import save_json
        
class TicketTool:
    
    def __init__(self):
        with open(TICKETS_PATH,"r") as f:
            self.tickets = json.load(f)
            
        with open(RESOLVED_TICKETS_FILE,"r") as f:
            self.resolved_tickets_list = json.load(f)
            self.resolved_tickets = {t["ticket_id"]: t for t in self.resolved_tickets_list}

    def save_tickets(self):
        save_json(TICKETS_PATH, self.tickets)
        
    def get_tickets(self, ticket_id: str):
        
        ticket = self.tickets.get(ticket_id)
        
        if ticket is None:
            resolved = self.resolved_tickets.get(ticket_id)
            if resolved:
                return {
                    "success": True,
                    "ticket": resolved,
                    "message": "This is a past resolved case.",
                }
                
            return {
                "success" : False,
                "message" : "Case Not Found"
            }
            
        ticket_copy = ticket.copy()
        ticket_copy["ticket_id"] = ticket_id
        return {
            "success": True,
            "ticket": ticket_copy
        }
    
    def check_ticket_status(self,ticket_id: str):
        
        ticket = self.tickets.get(ticket_id)
        
        if ticket is None:
            resolved = self.resolved_tickets.get(ticket_id)
            if resolved:
                return {
                    "success": True,
                    "status": "resolved",
                    "ticket": resolved
                }
                
            return {
                "success": False,
                "message": "Case not found."
            }

        ticket_copy = ticket.copy()
        ticket_copy["ticket_id"] = ticket_id
        return {
            "success": True,
            "status": ticket["status"],
            "ticket": ticket_copy
        }

    def create_dispute_case(self, user_id: str, account_id: str = None, txn_id: str = None):
        if not user_id or not str(user_id).strip():
            return {
                "success": False,
                "needs_clarification": True,
                "message": "Please confirm your customer ID to raise a dispute case.",
            }
        next_num = 9000 + len(self.tickets) + 1
        case_id = f"CASE-NEW-{next_num}"
        record = {
            "ticket_id": case_id,
            "case_id": case_id,
            "user_id": user_id.strip(),
            "account_id": account_id,
            "status": "open",
            "category": "dispute",
            "sub_category": "customer_initiated",
            "priority": "medium",
            "channel": "chat",
            "subject": "Dispute raised via banking assistant",
            "txn_id": txn_id,
            "created_on": datetime.now().strftime("%Y-%m-%d"),
            "assigned_team": "disputes_desk",
        }
        self.tickets[case_id] = record
        self.save_tickets()
        return {
            "success": True,
            "mutation": True,
            "message": "Dispute case created.",
            "case_id": case_id,
            "user_id": user_id.strip(),
            "account_id": account_id,
            "txn_id": txn_id,
            "status": "open",
            "ticket": record,
        }
        
