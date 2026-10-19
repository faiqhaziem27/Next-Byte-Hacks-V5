from flask import Flask, request, render_template, redirect, url_for

import analytics
import db

app = Flask(__name__)

@app.route('/')
def index():
    return render_template(
        'index.html',
        revenue_today=analytics.get_total_revenue_today(),
        todays_order_count=analytics.get_todays_order_count(),
        unpaid_total=analytics.get_unpaid_total(),
        best_selling_items=analytics.get_best_selling_items(),
        weekly_trend=analytics.get_weekly_trend(),
        recent_orders=db.get_recent_orders(),
        low_stock_count=db.get_low_stock_count(),
    )

@app.route('/inventory')
def inventory():
    items = db.get_all_items()
    return render_template(
        'inventory.html',
        items=items,
        inventory=items,
        low_stock_count=db.get_low_stock_count(),
    )

@app.route('/add_order', methods=['POST'])
def add_order():
    raw_text = request.form.get("order_text", "").strip()
    item_name = request.form.get("item_name", "").strip()

    if not raw_text:
        return "Order text is required.", 400
    if not item_name:
        return "Item name is required.", 400

    # Mock data only
    parsed_data = {
        "customer_name": request.form.get("customer_name", "Walk-in"),
        "items": [
            {
                "name": item_name,
                "quantity": request.form.get("quantity", 1),
            }
        ],
        "payment_status": request.form.get("payment_status", "Unpaid"),
    }

    success, message = db.save_order(parsed_data)

    if not success:
        return f"Error: {message}", 400

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)