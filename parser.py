
from ollama import ResponseError, chat
from pydantic import BaseModel, Field
import re
from typing import Literal

# The Ollama model
MODEL = "qwen3.5:4b"


class OrderItem(BaseModel):
    item: str
    quantity: int = Field(ge=1)


class Order(BaseModel):
    order: list[OrderItem]
    customer: str | None
    customer_payment_claim: Literal["Paid", "Unpaid", "Unknown"]


_PAID_HINTS = ("dah bayar", "already paid", "paid")
_UNPAID_HINTS = ("belum bayar", "not paid", "unpaid")
_SIMPLE_QTY_ITEM_RE = re.compile(r"^\s*(\d+)\s+([A-Za-z][A-Za-z0-9\s&'/-]+?)\s*$")
_SIMPLE_ITEM_ONLY_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9\s&'/-]+?)\s*$")
_COMPLEX_MARKERS = (" and ", " dan ", " nama ", " nak ", " dengan ", " with ")
_ITEM_SEPARATORS = re.compile(r"\s*(?:,| and | dan | dengan | with )\s*")


def _looks_simple_item(text):
    lowered = f" {text.lower().strip()} "
    if any(marker in lowered for marker in _COMPLEX_MARKERS):
        return False
    if re.search(r"\d", text):
        return False
    if len(text.split()) > 4:
        return False
    return True


def _simple_parse(raw_text):
    text = raw_text.strip()
    lowered = text.lower()

    payment = "Unknown"
    for hint in _PAID_HINTS:
        if hint in lowered:
            payment = "Paid"
            break
    if payment == "Unknown":
        for hint in _UNPAID_HINTS:
            if hint in lowered:
                payment = "Unpaid"
                break

    cleaned = lowered
    for hint in _PAID_HINTS + _UNPAID_HINTS:
        cleaned = cleaned.replace(hint, " ")
    cleaned = re.sub(r"[,.;:!?]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return None

    parts = [part for part in _ITEM_SEPARATORS.split(cleaned) if part]
    if len(parts) > 1:
        items = []
        for part in parts:
            match = _SIMPLE_QTY_ITEM_RE.match(part)
            if not match or not _looks_simple_item(match.group(2)):
                return None
            items.append({
                "name": match.group(2).strip().title(),
                "quantity": int(match.group(1)),
            })
        return {
            "customer_name": None,
            "items": items,
            "payment_status": "Unpaid" if payment == "Unknown" else payment,
        }

    qty_item = _SIMPLE_QTY_ITEM_RE.match(cleaned)
    if qty_item:
        qty = int(qty_item.group(1))
        item_raw = qty_item.group(2).strip()
        if not _looks_simple_item(item_raw):
            return None
        item = item_raw.title()
        return {
            "customer_name": None,
            "items": [{"name": item, "quantity": qty}],
            "payment_status": "Unpaid" if payment == "Unknown" else payment,
        }

    item_only = _SIMPLE_ITEM_ONLY_RE.match(cleaned)
    if item_only:
        item_raw = item_only.group(1).strip()
        if not _looks_simple_item(item_raw):
            return None
        item = item_raw.title()
        return {
            "customer_name": None,
            "items": [{"name": item, "quantity": 1}],
            "payment_status": "Unpaid" if payment == "Unknown" else payment,
        }
    return None


# Function Developer 1 will use
def parse_order_with_ai(raw_text):

    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ValueError("Order message cannot be empty")

    simple = _simple_parse(raw_text)
    if simple is not None:
        return simple

    response = chat(
        model=MODEL,
        think=False,
        keep_alive="10m",
        messages=[
            {
                "role": "system",
                "content": (
                    "Extract a Malaysian food-stall order from Malay, English, "
                    "or Manglish. Return every item and positive quantity, the "
                    "customer name or null, and payment claim: Paid only for "
                    "'dah bayar'/'already paid', Unpaid only for "
                    "'belum bayar'/'not paid', otherwise Unknown. Never verify "
                    "payment and never invent data."
                )
            },
            {
                "role": "user",
                "content": raw_text
            }
        ],
        format=Order.model_json_schema(),
        options={"temperature": 0, "num_predict": 256}
    )

    # Validate AI response
    if not response.message.content.strip():
        raise ValueError("The AI returned an empty response. Please try again.")
    result = Order.model_validate_json(
        response.message.content
    )

    order_data = result.model_dump()

    payment_status = result.customer_payment_claim
    if payment_status == "Unknown":
        payment_status = "Unpaid"

    formatted_order = {
        "customer_name": order_data["customer"],
        "items": [
            {
                "name": item["item"],
                "quantity": item["quantity"]
            }
            for item in order_data["order"]
        ],
        "payment_status": payment_status
    }

    return formatted_order


# Test your parser
if __name__ == "__main__":

    message = (
        "Boss nak 2 nasi lemak ayam and 1 teh ais. "
        "Nama Ali, dah bayar."
    )

    print(parse_order_with_ai(message))
