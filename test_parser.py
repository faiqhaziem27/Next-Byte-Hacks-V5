
from parser import parse_order_with_ai

tests = [
    "Ali nak 2 nasi lemak dan 1 teh ais",
    "Boss, 3 nasi lemak, 2 teh o ais",
    "Saya nak 1 buttermilk chicken",
    "Nama Siti, 2 nasi lemak ayam, dah bayar",
    "Can I get 2 air kosong and 1 teh ais?"
]

for number, message in enumerate(tests, 1):
    print(f"\nTEST {number}: {message}")

    try:
        result = parse_order_with_ai(message)
        print(result)
    except Exception as error:
        print("ERROR:", error)
