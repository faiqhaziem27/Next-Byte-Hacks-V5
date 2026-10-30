# Stall Manager

Stall Manager is a small web app we built for **Next Byte Hacks V5** to help food stall owners keep track of orders.

Running a stall is busy. Orders come in fast, people ask in Malay, English, or a mix of both, and it's easy to lose track of who paid and what's left in stock. With Stall Manager, you just type the order the way you'd say it, like `Nama Ali, 2 nasi lemak ayam and 1 teh ais, dah bayar`, and the app works out the rest.

## What it does

- **Understands normal messages.** Type an order in Malay, English, or Manglish and the app pulls out the customer name, items, quantities, and whether they said they paid.
- **Two ways of reading orders.** Simple orders (like `1 nasi lemak`) are handled by our own fast parser. Longer or trickier ones are sent to a local AI model (Ollama running `qwen3.5:4b`).
- **Handles short forms and typos.** Things like `th tarik` or `nsi lm` still match the right menu item. If a name is too unclear, the app rejects it instead of guessing wrong.
- **Manages stock.** It checks there's enough stock before saving an order, then deducts it automatically. Items at 10 or below are flagged as low stock.
- **Inventory page.** Add, edit, and delete menu items.
- **Dashboard.** Shows today's revenue, today's order count, total unpaid money, best sellers, recent orders, and a 7-day sales chart.
- **Mark as paid.** Orders with no payment claim are saved as Unpaid. Press **Mark paid** once the customer actually pays.

## Tech we used

- Python and Flask for the web app
- SQLite for the database
- pandas for the analytics
- Ollama (`qwen3.5:4b`) and pydantic for the AI order parsing
- Chart.js for the weekly sales chart

## How to run it

You need to set this up on every laptop that runs the app, since the AI model runs locally.

### 1. Install the basics

- Python 3.10 or newer: <https://www.python.org/downloads/>
- Ollama: <https://ollama.com/download>

Once Ollama is installed and running, download the model:

```
ollama pull qwen3.5:4b
```

### 2. Get the code

```
git clone https://github.com/faiqhaziem27/Next-Byte-Hacks-V5.git
cd Next-Byte-Hacks-V5
```

If you got the project as a ZIP, just extract it and open a terminal inside the folder.

### 3. Install the Python packages

```
py -m pip install -r requirements.txt
```

If `py` doesn't work on your computer, use `python` instead:

```
python -m pip install -r requirements.txt
```

### 4. Add sample data (optional)

```
py seed_data.py
```

This gives you a starter menu (Nasi Lemak Special, Teh Tarik, Chicken Chop, Mee Goreng, Sirap Bandung, Roti Canai) and 18 fake orders from the past week, so the dashboard isn't empty. Chicken Chop is set to low stock on purpose so you can see the warning.

**Careful:** this wipes `stall.db`. Don't run it if you already have real orders you want to keep.

If you skip this step, the app still creates the tables for you, but the menu will be empty. You'd need to add items on the Inventory page first.

### 5. Start the app

```
py app.py
```

Then open <http://127.0.0.1:5000> in your browser. Press `Ctrl+C` in the terminal to stop it.

## How to use it

### Adding an order

Type the order into the box on the dashboard. Some examples:

```
Nama Ali, 2 nasi lemak ayam and 1 teh ais, dah bayar
1 nasi lemak
1 th tarik and 2 nasi lm
```

A few things to know:

- The item has to exist in the inventory, and there has to be enough stock, or the order is rejected with an error message.
- If you don't give a customer name, it's saved as **Walk-in**.
- If you don't say whether they paid, it's saved as **Unpaid**.
- The AI only reads what the customer *claims* about payment. It never checks if they really paid, so you can fix it with **Mark paid** later.

### Managing the menu

Go to <http://127.0.0.1:5000/inventory> to add, edit, or delete items. If you delete an item, old orders still keep its name and price, so your history doesn't break.

### Revenue

Only **Paid** orders count towards revenue, best sellers, and the weekly chart. Unpaid orders show up in the unpaid total until you mark them as paid.

## Project files

```
app.py            Flask routes (the pages and buttons)
db.py             Database code: inventory, saving orders, matching item names
parser.py         Fast local parser + Ollama AI fallback
analytics.py      Numbers for the dashboard (pandas)
schema.sql        Database tables
seed_data.py      Optional sample data (resets the database)
test_parser.py    Quick script to try some example orders
requirements.txt  Python packages
templates/        HTML pages
stall.db          The database (made when the app runs)
```

## Testing the parser

To try a few sample messages without opening the website:

```
py test_parser.py
```

Some of these go to the AI, so make sure Ollama is running first.

## Troubleshooting

- **"qwen3.5:4b" not found:** run `ollama pull qwen3.5:4b`.
- **`ModuleNotFoundError`:** run `py -m pip install -r requirements.txt` again.
- **"Item not found on the menu":** add the item on the Inventory page, then try the order again.
- **Some orders are slow:** simple orders are instant, but longer ones wait for the AI. Keep Ollama running and give it a few seconds.
- **Could not parse order with Ollama:** Ollama probably isn't running. Open it and try again.
