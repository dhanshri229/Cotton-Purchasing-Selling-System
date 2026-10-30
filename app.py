from flask import Flask, render_template, request, redirect, url_for
from db import get_db_connection

app = Flask(__name__)

# Ensure Expenses table exists
def ensure_expense_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            expense_type TEXT,
            mill_location TEXT,
            labor_count INTEGER DEFAULT 0,
            wage_per_person REAL DEFAULT 0,
            transport_fuel_cost REAL DEFAULT 0,
            total_expense REAL DEFAULT 0,
            vehicle_number TEXT
        )
    ''')
    conn.commit()
    conn.close()

ensure_expense_table()

# --- 1. Dashboard / Home Route ---
@app.route('/')
def home():
    conn = get_db_connection()
    total_farmers = conn.execute('SELECT COUNT(*) as count FROM farmers').fetchone()['count']
    
    p_data = conn.execute('SELECT SUM(weight) as p_wt, SUM(total_amount) as p_amt FROM purchases').fetchone()
    s_data = conn.execute('SELECT SUM(weight) as s_wt, SUM(total_amount) as s_amt FROM sales').fetchone()
    
    total_purchases = p_data['p_amt'] or 0.0
    total_sales = s_data['s_amt'] or 0.0
    stock = (p_data['p_wt'] or 0.0) - (s_data['s_wt'] or 0.0)
    
    conn.close()
    return render_template('index.html',
                           total_farmers=total_farmers,
                           total_purchases=total_purchases,
                           total_sales=total_sales,
                           stock=stock)

# --- 2. Farmer Routes ---
@app.route('/farmer', methods=['GET', 'POST'])
def farmer():
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form.get('name')
        mobile = request.form.get('mobile')
        aadhar_number = request.form.get('aadhar_number')
        village = request.form.get('village')

        if name:
            conn.execute('INSERT INTO farmers (name, mobile, aadhar_number, village) VALUES (?, ?, ?, ?)',
                         (name, mobile, aadhar_number, village))
            conn.commit()
            conn.close()
            return redirect(url_for('farmer'))

    farmers = conn.execute('SELECT * FROM farmers').fetchall()
    conn.close()
    return render_template('farmer.html', farmers=farmers)

@app.route('/delete_farmer/<int:id>')
def delete_farmer(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM farmers WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('farmer'))

# --- 3. Vehicle Routes ---
@app.route('/vehicle', methods=['GET', 'POST'])
def vehicle():
    conn = get_db_connection()
    if request.method == 'POST':
        vehicle_number = request.form.get('vehicle_number')
        driver_name = request.form.get('driver_name')
        driver_mobile = request.form.get('driver_mobile')

        if vehicle_number:
            conn.execute('INSERT INTO vehicles (vehicle_number, driver_name, driver_mobile) VALUES (?, ?, ?)',
                         (vehicle_number, driver_name, driver_mobile))
            conn.commit()
            conn.close()
            return redirect(url_for('vehicle'))

    vehicles = conn.execute('SELECT * FROM vehicles').fetchall()
    conn.close()
    return render_template('vehicle.html', vehicles=vehicles)

@app.route('/delete_vehicle/<int:id>')
def delete_vehicle(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM vehicles WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('vehicle'))

# --- 4. Purchase Routes ---
@app.route('/purchase', methods=['GET', 'POST'])
def purchase():
    conn = get_db_connection()
    if request.method == 'POST':
        farmer_id = request.form.get('farmer_id')
        vehicle_id = request.form.get('vehicle_id') or None
        date = request.form.get('date')
        weight = float(request.form.get('weight') or 0)
        rate = float(request.form.get('rate') or 0)
        total_amount = float(request.form.get('total_amount') or 0)
        paid_amount = float(request.form.get('paid_amount') or 0)

        conn.execute('''
            INSERT INTO purchases (farmer_id, vehicle_id, date, weight, rate, total_amount, paid_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (farmer_id, vehicle_id, date, weight, rate, total_amount, paid_amount))
        conn.commit()
        conn.close()
        return redirect(url_for('purchase'))

    farmers = conn.execute('SELECT id, name, village FROM farmers').fetchall()
    vehicles = conn.execute('SELECT id, vehicle_number, driver_name FROM vehicles').fetchall()
    
    purchases = conn.execute('''
        SELECT p.*, f.name as farmer_name, v.vehicle_number 
        FROM purchases p
        LEFT JOIN farmers f ON p.farmer_id = f.id
        LEFT JOIN vehicles v ON p.vehicle_id = v.id
        ORDER BY p.id DESC
    ''').fetchall()

    total_purchase_sum = sum((p['total_amount'] or 0) for p in purchases)
    total_paid_sum = sum((p['paid_amount'] or 0) for p in purchases)
    total_due_sum = total_purchase_sum - total_paid_sum
    
    conn.close()
    return render_template('purchase.html', 
                           farmers=farmers, 
                           vehicles=vehicles, 
                           purchases=purchases,
                           total_purchase_sum=total_purchase_sum,
                           total_paid_sum=total_paid_sum,
                           total_due_sum=total_due_sum)

@app.route('/delete_purchase/<int:id>')
def delete_purchase(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM purchases WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('purchase'))

# --- Bill / Receipt Route ---
@app.route('/bill/<int:id>')
def bill(id):
    conn = get_db_connection()
    bill_data = conn.execute('''
        SELECT p.*, f.name as farmer_name, f.mobile, f.aadhar_number, f.village, v.vehicle_number
        FROM purchases p
        JOIN farmers f ON p.farmer_id = f.id
        LEFT JOIN vehicles v ON p.vehicle_id = v.id
        WHERE p.id = ?
    ''', (id,)).fetchone()
    conn.close()
    
    if not bill_data:
        return "Bill not found", 404
        
    return render_template('bill.html', bill=bill_data)

# --- 5. Payment Routes ---
@app.route('/payment', methods=['GET', 'POST'])
def payment():
    conn = get_db_connection()
    if request.method == 'POST':
        farmer_id = request.form.get('farmer_id')
        date = request.form.get('date')
        amount = float(request.form.get('amount') or 0)
        payment_mode = request.form.get('payment_mode')

        if farmer_id and amount > 0:
            conn.execute('''
                INSERT INTO payments (farmer_id, date, amount, payment_mode)
                VALUES (?, ?, ?, ?)
            ''', (farmer_id, date, amount, payment_mode))
            conn.commit()
            conn.close()
            return redirect(url_for('payment'))

    farmers = conn.execute('SELECT id, name, village FROM farmers').fetchall()
    payments = conn.execute('''
        SELECT pay.*, f.name as farmer_name, f.village
        FROM payments pay
        JOIN farmers f ON pay.farmer_id = f.id
        ORDER BY pay.id DESC
    ''').fetchall()
    
    conn.close()
    return render_template('payment.html', farmers=farmers, payments=payments)

@app.route('/delete_payment/<int:id>')
def delete_payment(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM payments WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('payment'))

# --- 6. Selling Routes ---
@app.route('/selling', methods=['GET', 'POST'])
def selling():
    conn = get_db_connection()
    if request.method == 'POST':
        buyer_name = request.form.get('buyer_name')
        date = request.form.get('date')
        weight = float(request.form.get('weight') or 0)
        rate = float(request.form.get('rate') or 0)
        total_amount = float(request.form.get('total_amount') or 0)

        if buyer_name and weight > 0:
            conn.execute('''
                INSERT INTO sales (buyer_name, date, weight, rate, total_amount)
                VALUES (?, ?, ?, ?, ?)
            ''', (buyer_name, date, weight, rate, total_amount))
            conn.commit()
            conn.close()
            return redirect(url_for('selling'))

    sales = conn.execute('SELECT * FROM sales ORDER BY id DESC').fetchall()
    total_sold_weight = sum((s['weight'] or 0) for s in sales)
    total_sales_amount = sum((s['total_amount'] or 0) for s in sales)
    
    conn.close()
    return render_template('selling.html', 
                           sales=sales, 
                           total_sold_weight=total_sold_weight, 
                           total_sales_amount=total_sales_amount)

@app.route('/delete_selling/<int:id>')
def delete_selling(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM sales WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('selling'))

# --- 7. Stock Route ---
@app.route('/stock')
def stock():
    conn = get_db_connection()
    purchase_data = conn.execute('SELECT SUM(weight) as total_p_weight FROM purchases').fetchone()
    total_purchased_weight = purchase_data['total_p_weight'] or 0.0

    sales_data = conn.execute('SELECT SUM(weight) as total_s_weight FROM sales').fetchone()
    total_sold_weight = sales_data['total_s_weight'] or 0.0

    current_stock = total_purchased_weight - total_sold_weight
    conn.close()

    return render_template('stock.html', 
                           total_purchased_weight=total_purchased_weight,
                           total_sold_weight=total_sold_weight,
                           current_stock=current_stock)

# --- 8. Purchase Report Route ---
@app.route('/purchase_report')
def purchase_report():
    conn = get_db_connection()
    purchases = conn.execute('''
        SELECT p.*, f.name as farmer_name, f.mobile, f.village 
        FROM purchases p 
        LEFT JOIN farmers f ON p.farmer_id = f.id 
        ORDER BY p.id DESC
    ''').fetchall()
    
    total_purchase_amt = sum((p['total_amount'] or 0) for p in purchases)
    total_paid_amt = sum((p['paid_amount'] or 0) for p in purchases)
    conn.close()

    return render_template('purchase_report.html', 
                           purchases=purchases,
                           total_purchase_amt=total_purchase_amt,
                           total_paid_amt=total_paid_amt)

# --- 9. Sales Report Route ---
@app.route('/sales_report')
def sales_report():
    conn = get_db_connection()
    sales = conn.execute('SELECT * FROM sales ORDER BY id DESC').fetchall()
    total_sold_weight = sum((s['weight'] or 0) for s in sales)
    total_sales_amt = sum((s['total_amount'] or 0) for s in sales)
    conn.close()

    return render_template('sales_report.html', 
                           sales=sales,
                           total_sold_weight=total_sold_weight,
                           total_sales_amt=total_sales_amt)

# --- 10. Expenses & Net Profit Tracker Routes ---
@app.route('/expense', methods=['GET', 'POST'])
def expense():
    conn = get_db_connection()
    if request.method == 'POST':
        date = request.form.get('date')
        expense_type = request.form.get('expense_type')
        mill_location = request.form.get('mill_location')
        labor_count = int(request.form.get('labor_count') or 0)
        wage_per_person = float(request.form.get('wage_per_person') or 0)
        transport_fuel_cost = float(request.form.get('transport_fuel_cost') or 0)
        total_expense = float(request.form.get('total_expense') or 0)
        vehicle_number = request.form.get('vehicle_number')

        conn.execute('''
            INSERT INTO expenses (date, expense_type, mill_location, labor_count, wage_per_person, transport_fuel_cost, total_expense, vehicle_number)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date, expense_type, mill_location, labor_count, wage_per_person, transport_fuel_cost, total_expense, vehicle_number))
        conn.commit()
        conn.close()
        return redirect(url_for('expense'))

    expenses = conn.execute('SELECT * FROM expenses ORDER BY id DESC').fetchall()
    
    p_data = conn.execute('SELECT SUM(total_amount) as p_amt FROM purchases').fetchone()
    s_data = conn.execute('SELECT SUM(total_amount) as s_amt FROM sales').fetchone()
    e_data = conn.execute('SELECT SUM(total_expense) as e_amt FROM expenses').fetchone()

    total_purchases = p_data['p_amt'] or 0.0
    total_sales = s_data['s_amt'] or 0.0
    total_expenses = e_data['e_amt'] or 0.0

    net_profit = total_sales - total_purchases - total_expenses

    conn.close()
    return render_template('expense.html', 
                           expenses=expenses,
                           total_purchases=total_purchases,
                           total_sales=total_sales,
                           total_expenses=total_expenses,
                           net_profit=net_profit)

# --- Edit Expense Route ---
@app.route('/edit_expense/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):
    conn = get_db_connection()
    if request.method == 'POST':
        date = request.form.get('date')
        expense_type = request.form.get('expense_type')
        mill_location = request.form.get('mill_location')
        labor_count = int(request.form.get('labor_count') or 0)
        wage_per_person = float(request.form.get('wage_per_person') or 0)
        transport_fuel_cost = float(request.form.get('transport_fuel_cost') or 0)
        total_expense = float(request.form.get('total_expense') or 0)

        conn.execute('''
            UPDATE expenses 
            SET date = ?, expense_type = ?, mill_location = ?, labor_count = ?, wage_per_person = ?, transport_fuel_cost = ?, total_expense = ?
            WHERE id = ?
        ''', (date, expense_type, mill_location, labor_count, wage_per_person, transport_fuel_cost, total_expense, id))
        conn.commit()
        conn.close()
        return redirect(url_for('expense'))

    expense_data = conn.execute('SELECT * FROM expenses WHERE id = ?', (id,)).fetchone()
    conn.close()
    if not expense_data:
        return "Expense record not found", 404
        
    return render_template('edit_expense.html', expense=expense_data)

# --- Delete Expense Route ---
@app.route('/delete_expense/<int:id>')
def delete_expense(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM expenses WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('expense'))

if __name__ == '__main__':
    app.run(debug=True)