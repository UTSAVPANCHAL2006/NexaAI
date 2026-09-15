import json
from app.config.config import ORDERS_PATH, TRACKING_PATH

class OrderTool:

    def __init__(self):
        with open(ORDERS_PATH, "r") as f:
            self.orders = json.load(f)
            
        with open(TRACKING_PATH, "r") as f:
            self.tracking_data = json.load(f)

    def track_order(self, order_id: str):
        if not order_id or not str(order_id).strip():
            return {
                "success": False,
                "needs_clarification": True,
                "message": "Please share your order ID (e.g. ORD-1011) or tracking ID (e.g. TRK-1001).",
            }
        order_id = order_id.strip().upper()
        
        # Check if the user passed a tracking ID instead of an order ID
        if order_id.startswith("TRK-"):
            for oid, order in self.orders.items():
                if order.get("tracking_id") == order_id:
                    order_copy = order.copy()
                    order_copy["order_id"] = oid
                    order_copy["tracking_history"] = self.tracking_data.get(order_id)
                    return {
                        "success": True,
                        "order": order_copy
                    }
            return {
                "success": False,
                "message": "Order not found."
            }

        order = self.orders.get(order_id)
        if order:
            order_copy = order.copy()
            order_copy["order_id"] = order_id
            tracking_id = order.get("tracking_id")
            if tracking_id:
                track_info = self.tracking_data.get(tracking_id)
                if track_info:
                    # Only provide a brief summary to avoid dumping the whole history
                    order_copy["carrier"] = track_info.get("carrier")
                    order_copy["current_location"] = track_info.get("current_location")
                
            return {
                "success": True,
                "order": order_copy
            }

        return {
            "success": False,
            "message": "Order not found."
        }
        
    
    
    def cancel_order(self,order_id:str):
        order = self.orders.get(order_id)
        
        if order is None:
            return {
                "success": False,
                "message":"Order not found."
            }
        
        if order.get("status") == "processing":
            
            order["status"] = "cancelled"
            return {
                "success" : True,
                "message" : "Order Cancelled Successfully",
                "order" : order
        
            }
            
        return {
            "success": False,
            "message": f"Order cannot be cancelled because its current status is '{order['status']}'."
        }

    def check_return_eligibility(self, order_id: str):
        order = self.orders.get(order_id.upper().strip())

        if order is None:
            return {
                "success": False,
                "message": "Order Not Found"
            }

        order_info = {**order, "order_id": order_id.upper().strip()}

        if order["status"] != "delivered":
            return {
                "success": False,
                "message": f"Order is not eligible for return because its status is '{order['status']}'. Only delivered orders can be returned.",
                "order": order_info
            }

        if order.get("return_eligible"):
            return {
                "success": True,
                "message": "Order is eligible for return.",
                "order": order_info
            }

        return {
            "success": False,
            "message": "Return window has expired.",
            "order": order_info
        }
    

