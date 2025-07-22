from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Initialize database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Create bills table
    c.execute('''CREATE TABLE IF NOT EXISTS bills
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  customer_name TEXT NOT NULL,
                  customer_address TEXT,
                  customer_phone TEXT,
                  bill_date TEXT NOT NULL,
                  due_date TEXT,
                  items TEXT NOT NULL,
                  subtotal REAL NOT NULL,
                  tax REAL NOT NULL,
                  discount REAL NOT NULL,
                  total REAL NOT NULL,
                  notes TEXT)''')
    
    conn.commit()
    conn.close()

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_bill', methods=['GET', 'POST'])
def create_bill():
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        customer_address = request.form['customer_address']
        customer_phone = request.form['customer_phone']
        bill_date = request.form['bill_date'] or datetime.now().strftime('%Y-%m-%d')
        due_date = request.form['due_date']
        
        # Process items
        item_names = request.form.getlist('item_name[]')
        item_quantities = request.form.getlist('item_quantity[]')
        item_prices = request.form.getlist('item_price[]')
        
        items = []
        subtotal = 0
        
        for name, qty, price in zip(item_names, item_quantities, item_prices):
            if name and qty and price:
                qty = float(qty)
                price = float(price)
                total = qty * price
                items.append({
                    'name': name,
                    'quantity': qty,
                    'price': price,
                    'total': total
                })
                subtotal += total
        
        tax_rate = float(request.form.get('tax', 0))
        tax_amount = subtotal * (tax_rate / 100)
        
        discount_rate = float(request.form.get('discount', 0))
        discount_amount = subtotal * (discount_rate / 100)
        
        total = subtotal + tax_amount - discount_amount
        
        notes = request.form['notes']
        
        # Save to database
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''INSERT INTO bills 
                    (customer_name, customer_address, customer_phone, bill_date, due_date, 
                     items, subtotal, tax, discount, total, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (customer_name, customer_address, customer_phone, bill_date, due_date,
                     str(items), subtotal, tax_amount, discount_amount, total, notes))
        conn.commit()
        conn.close()
        
        flash('Bill created successfully!', 'success')
        return redirect(url_for('view_bills'))
    
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('create_bill.html', today=today)

@app.route('/view_bills')
def view_bills():
    conn = get_db_connection()
    bills = conn.execute('SELECT * FROM bills ORDER BY bill_date DESC').fetchall()
    conn.close()
    return render_template('view_bills.html', bills=bills)

@app.route('/bill/<int:bill_id>')
def bill_detail(bill_id):
    conn = get_db_connection()
    bill = conn.execute('SELECT * FROM bills WHERE id = ?', (bill_id,)).fetchone()
    conn.close()
    
    if bill is None:
        flash('Bill not found!', 'danger')
        return redirect(url_for('view_bills'))
    
    # Convert items string back to list
    import ast
    bill_items = ast.literal_eval(bill['items'])
    
    return render_template('bill_detail.html', bill=bill, items=bill_items)

@app.route('/edit_bill/<int:bill_id>', methods=['GET', 'POST'])
def edit_bill(bill_id):
    conn = get_db_connection()
    
    if request.method == 'POST':
        # Similar to create_bill but with UPDATE
        customer_name = request.form['customer_name']
        customer_address = request.form['customer_address']
        customer_phone = request.form['customer_phone']
        bill_date = request.form['bill_date']
        due_date = request.form['due_date']
        
        # Process items (same as create_bill)
        item_names = request.form.getlist('item_name[]')
        item_quantities = request.form.getlist('item_quantity[]')
        item_prices = request.form.getlist('item_price[]')
        
        items = []
        subtotal = 0
        
        for name, qty, price in zip(item_names, item_quantities, item_prices):
            if name and qty and price:
                qty = float(qty)
                price = float(price)
                total = qty * price
                items.append({
                    'name': name,
                    'quantity': qty,
                    'price': price,
                    'total': total
                })
                subtotal += total
        
        tax_rate = float(request.form.get('tax', 0))
        tax_amount = subtotal * (tax_rate / 100)
        
        discount_rate = float(request.form.get('discount', 0))
        discount_amount = subtotal * (discount_rate / 100)
        
        total = subtotal + tax_amount - discount_amount
        
        notes = request.form['notes']
        
        # Update database
        c = conn.cursor()
        c.execute('''UPDATE bills SET
                    customer_name = ?, customer_address = ?, customer_phone = ?,
                    bill_date = ?, due_date = ?, items = ?, subtotal = ?,
                    tax = ?, discount = ?, total = ?, notes = ?
                    WHERE id = ?''',
                    (customer_name, customer_address, customer_phone, bill_date, due_date,
                     str(items), subtotal, tax_amount, discount_amount, total, notes, bill_id))
        conn.commit()
        conn.close()
        
        flash('Bill updated successfully!', 'success')
        return redirect(url_for('bill_detail', bill_id=bill_id))
    
    # GET request - load existing bill data
    bill = conn.execute('SELECT * FROM bills WHERE id = ?', (bill_id,)).fetchone()
    conn.close()
    
    if bill is None:
        flash('Bill not found!', 'danger')
        return redirect(url_for('view_bills'))
    
    import ast
    bill_items = ast.literal_eval(bill['items'])
    
    return render_template('edit_bill.html', bill=bill, items=bill_items)

@app.route('/delete_bill/<int:bill_id>', methods=['POST'])
def delete_bill(bill_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM bills WHERE id = ?', (bill_id,))
    conn.commit()
    conn.close()
    
    flash('Bill deleted successfully!', 'success')
    return redirect(url_for('view_bills'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)