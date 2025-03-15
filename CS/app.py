from flask import Flask, flash, render_template, request, redirect, url_for, session
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Google Apps Script Web App URL
GOOGLE_SHEET_API_URL = 'https://script.google.com/macros/s/AKfycby7OhtekKwoSj5e-B23e12ioZSkx-SSArRXGNHjIxWvzcrxbbzuemWl54NqTpootMEIFQ/exec'

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/auth', methods=['POST'])
def auth():
    username = request.form['username']
    password = request.form['password']
    if username == 'admin' and password == '1':  # Dummy authentication
        session['user'] = username
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    response = requests.get(GOOGLE_SHEET_API_URL, params={'action': 'get_stock'})
    if response.status_code == 200:
        stock_data = response.json()
    else:
        stock_data = []  # Default empty list in case of failure

    return render_template('dashboard.html', stock_data=stock_data)
@app.route('/add_stock', methods=['GET', 'POST'])
def add_stock():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    stock_data = []  # Ensure stock_data is always initialized
    try:
        response = requests.get(GOOGLE_SHEET_API_URL, params={'action': 'get_stock'})
        if response.status_code == 200:
            stock_data = response.json()
    except Exception as e:
        print("Error fetching stock data:", e)

    stock_names = [item[1] for item in stock_data[1:]] if stock_data else []  # Extract stock names
    
    message = ""
    if request.method == 'POST':
        stock_name = request.form['stock_name']
        quantity = int(request.form['quantity'])
        
        if stock_name in stock_names:
            data = {'action': 'add_stock', 'stock_name': stock_name, 'quantity': quantity}
            post_response = requests.post(GOOGLE_SHEET_API_URL, json=data)
            message = "Stock updated successfully!" if post_response.status_code == 200 else "Failed to update stock."
        else:
            confirm_add = request.form.get('confirm_add')
            if confirm_add == 'yes':
                data = {'action': 'add_stock', 'stock_name': stock_name, 'quantity': quantity}
                post_response = requests.post(GOOGLE_SHEET_API_URL, json=data)
                message = "New stock added successfully!" if post_response.status_code == 200 else "Failed to add stock."
            else:
                message = f"Stock '{stock_name}' not found. Do you want to add it as a new stock?"
    
    return render_template('add_stock.html', stock_data=stock_data, message=message)
GOOGLE_SHEET_API_URL1 ='https://script.google.com/macros/s/AKfycbzIj-nexniMgE6mby9GMBShJUaMHIhzxTZZyFw4oUrarsHjcG4ZkLc2GpduxCMkN0uuLQ/exec'
@app.route('/stock_out', methods=['GET', 'POST'])
def stock_out():
    if 'user' not in session:
        return redirect(url_for('login'))

    # Fetch existing stock data
    response = requests.get(GOOGLE_SHEET_API_URL, params={'action': 'get_stock'})
    stock_data = response.json() if response.status_code == 200 else []
    stock_names = {}

    for item in stock_data[1:]:  # Skip header row
        try:
            if isinstance(item, list) and len(item) > 2:
                quantity = int(item[2]) if str(item[2]).strip().isdigit() else 0
                stock_names[item[1].strip()] = quantity
        except (IndexError, ValueError, AttributeError):
            continue

    if request.method == 'POST':
        stock_entries = request.form.getlist('stock_name[]')
        quantities = request.form.getlist('quantity[]')

        error_flag = False

        for stock_name, quantity in zip(stock_entries, quantities):
            stock_name = stock_name.strip()
            quantity = quantity.strip()

            if not quantity.isdigit():
                flash(f'Invalid quantity for {stock_name}. Please enter a number.', 'error')
                error_flag = True
                continue

            quantity = int(quantity)

            if stock_name in stock_names:
                current_stock = stock_names[stock_name]
                if current_stock >= quantity:
                    data = {'action': 'stock_out', 'stock_name': stock_name, 'quantity': quantity}
                    post_response = requests.post(GOOGLE_SHEET_API_URL1, json=data)
                    if post_response.status_code != 200:
                        flash(f'Failed to remove stock for {stock_name}.', 'error')
                        error_flag = True
                    else:
                        flash(f'{quantity} units of {stock_name} removed successfully!', 'success')
                else:
                    flash(f'Insufficient stock for {stock_name}. (Available: {current_stock})', 'error')
                    error_flag = True
            else:
                flash(f'Stock item "{stock_name}" not found.', 'error')
                error_flag = True

        if not error_flag:
            return redirect(url_for('stock_out'))

    return render_template('stock_out.html', stock_data=stock_data, stock_names=stock_names)
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)    