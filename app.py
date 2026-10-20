import os

from flask import Flask, flash, request, render_template, redirect, url_for

import analytics
import db
from ollama import ResponseError
from parser import parse_order_with_ai

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'local-development-key')
db.ensure_db()

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
        customer_balances=db.get_customer_balances(),
    )

@app.route('/inventory')
def inventory():
    items = db.get_all_items()
    low = [item for item in items if item['low_stock']]
    return render_template(
        'inventory.html',
        items=items,
        inventory=items,
        low=low,
        low_stock_count=db.get_low_stock_count(),
    )

@app.route('/add_order', methods=['POST'])
def add_order():
    raw_text = request.form.get("order_text", "").strip()

    if not raw_text:
        return "Order text is required.", 400

    try:
        parsed_data = parse_order_with_ai(raw_text)
    except ValueError as error:
        return f"Could not parse order: {error}", 400
    except ResponseError as error:
        app.logger.exception("Ollama order parsing failed")
        return f"Could not parse order with Ollama: {error}", 502

    success, message = db.save_order(parsed_data)

    if not success:
        return f"Error: {message}", 400

    return redirect(url_for("index"))


@app.route('/add_balance', methods=['POST'])
def add_balance():
    success, message = db.add_customer_balance(
        request.form.get("customer_name"),
        request.form.get("amount"),
    )
    if not success:
        return message, 400
    return redirect(url_for("index"))


@app.route('/mark_paid/<int:order_id>', methods=['POST'])
def mark_paid(order_id):
    success, message = db.mark_order_paid(order_id)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for("index"))


@app.route('/pay_from_balance/<int:order_id>', methods=['POST'])
def pay_from_balance(order_id):
    success, message = db.pay_order_from_balance(order_id)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)