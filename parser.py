
from ollama import chat
from pydantic import BaseModel, Field
from typing import Literal

# The Ollama model
MODEL = "qwen3:4b-instruct"


class OrderItem(BaseModel):
    item: str
    quantity: int = Field(ge=1)


class Order(BaseModel):
    order: list[OrderItem]
    customer: str | None
    customer_payment_claim: Literal["Paid", "Unpaid", "Unknown"]


# Function Developer 1 will use
def parse_order_with_ai(raw_text):

    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ValueError("Order message cannot be empty")

    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """
You extract orders for a Malaysian food stall.

Understand Malay, English and Manglish.

Extract:
- All ordered item names
- Exact quantities
- Customer name if mentioned
- Customer payment claim

PAYMENT RULES:
1. If customer says "dah bayar" or "already paid",
   customer_payment_claim = "Paid".

2. If customer says "belum bayar" or "not paid",
   customer_payment_claim = "Unpaid".

3. If payment is not mentioned,
   customer_payment_claim = "Unknown".

4. Never verify actual payments.
5. Customer statements are not payment proof.

OTHER RULES:
- Extract every requested item.
- Do not invent missing information.
- Use positive quantities only.
- If customer name is missing, use null.
- Return structured data.
"""
            },
            {
                "role": "user",
                "content": raw_text
            }
        ],
        format=Order.model_json_schema(),
        options={"temperature": 0}
    )

    # Validate AI response
    result = Order.model_validate_json(
        response.message.content
    )

    order_data = result.model_dump()

    # Format required by Developer 1
    formatted_order = {
        "customer_name": order_data["customer"],
        "items": [
            {
                "name": item["item"],
                "quantity": item["quantity"]
            }
            for item in order_data["order"]
        ],
        "payment_status": "Pending"
    }

    return formatted_order


# Test your parser
if __name__ == "__main__":

    message = (
        "Boss nak 2 nasi lemak ayam and 1 teh ais. "
        "Nama Ali, dah bayar."
    )

    print(parse_order_with_ai(message))
