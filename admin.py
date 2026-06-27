from flask import Blueprint, render_template, request, redirect, url_for, session
from models.db import get_db_connection

admin = Blueprint('admin', __name__)

# ADMIN LOGIN
@admin.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM admins WHERE username=%s AND password=%s",
                       (username, password))
        admin_user = cursor.fetchone()

        cursor.close()
        conn.close()

        if admin_user:
            session['admin'] = admin_user['username']
            return redirect(url_for('admin.dashboard'))

    return render_template('admin_login.html')


# DASHBOARD
@admin.route('/admin/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin.admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # 👥 Total Users
    cursor.execute("SELECT COUNT(*) FROM users")
    users_count = cursor.fetchone()[0]

    # 📦 Total Orders
    cursor.execute("SELECT COUNT(*) FROM orders")
    orders_count = cursor.fetchone()[0]

    # 💰 Revenue
    cursor.execute("SELECT SUM(total_amount) FROM orders")
    revenue = cursor.fetchone()[0]
    if revenue is None:
        revenue = 0

    cursor.close()
    conn.close()

    return render_template(
        'admin_dashboard.html',
        users_count=users_count,
        orders_count=orders_count,
        revenue=revenue
    )


# ADD FOOD
@admin.route('/admin/add_food', methods=['GET', 'POST'])
def add_food():
    if 'admin' not in session:
        return redirect(url_for('admin.admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['name']
        category_id = request.form['category']
        price = request.form['price']
        image = request.form['image']
        description = request.form['description']

        cursor.execute(
            "INSERT INTO food_items (name, category_id, price, image, description) VALUES (%s, %s, %s, %s, %s)",
            (name, category_id, price, image, description)
        )
        conn.commit()
        return redirect(url_for('admin.dashboard'))

    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('add_food.html', categories=categories)


# VIEW ORDERS
@admin.route('/admin/orders')
def view_orders():
    print("Admin orders route working")

    if 'admin' not in session:
        return redirect(url_for('admin.admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT orders.*, users.name 
        FROM orders 
        JOIN users ON orders.user_id = users.id
        ORDER BY order_date DESC
    """)
    orders = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('admin_orders.html', orders=orders)



#view users 
@admin.route('/admin/users')
def view_users():
    if 'admin' not in session:
        return redirect(url_for('admin.admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    return render_template('admin_users.html', users=users)





# LOGOUT
@admin.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin.admin_login'))



# ORDERS
@admin.route('/admin/orders')
def admin_orders():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT orders.*, users.name
        FROM orders
        JOIN users
        ON orders.user_id = users.id
        ORDER BY orders.id DESC
    """)

    orders = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'admin_orders.html',
        orders=orders
    )



# UPDATE ORDER STATUS
@admin.route('/update_order_status/<int:order_id>/<status>')
def update_order_status(order_id, status):

    # 🔐 Admin Login Check
    if 'admin' not in session:
        return redirect(url_for('admin.admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # ✅ UPDATE STATUS
    cursor.execute("""
        UPDATE orders
        SET status = %s
        WHERE id = %s
    """, (
        status,
        order_id
    ))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect(url_for('admin.admin_orders'))


# VIEW ALL ORDERS
@admin.route('/admin/orders')
def all_orders():

    # 🔐 Admin Login Check
    if 'admin' not in session:
        return redirect(url_for('admin.admin_login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 🧾 GET ALL ORDERS
    cursor.execute("""
        SELECT
            orders.*,
            users.name

        FROM orders

        INNER JOIN users
        ON orders.user_id = users.id

        ORDER BY orders.id DESC
    """)

    orders = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'admin_orders.html',
        orders=orders
    )