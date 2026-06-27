from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from models.db import get_db_connection

user = Blueprint('user', __name__)

# FOOD MENU
@user.route('/menu')
def menu():

    from flask import request

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    search = request.args.get('search', '')
    category = request.args.get('category', '')
    price = request.args.get('price', '')
    sort = request.args.get('sort', '')

    query = """
        SELECT 
            food_items.id,
            food_items.name,
            food_items.description,
            food_items.price,
            food_items.image,
            categories.name AS category,
            ROUND(AVG(feedback.rating),1) AS avg_rating

        FROM food_items

        LEFT JOIN categories 
            ON food_items.category_id = categories.id

        LEFT JOIN feedback 
            ON food_items.id = feedback.food_id
    """

    conditions = []
    values = []

    # 🔍 SEARCH
    if search:
        conditions.append("food_items.name LIKE %s")
        values.append('%' + search + '%')

    # 📂 CATEGORY
    if category:
        conditions.append("categories.name = %s")
        values.append(category)

    # 💰 PRICE FILTER
    if price == "low":
        conditions.append("food_items.price < 200")

    elif price == "mid":
        conditions.append("food_items.price BETWEEN 200 AND 500")

    elif price == "high":
        conditions.append("food_items.price > 500")

    # ✅ APPLY WHERE
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    # ✅ PREVENT DUPLICATES
    query += """
        GROUP BY 
            food_items.id,
            food_items.name,
            food_items.description,
            food_items.price,
            food_items.image,
            categories.name
    """

    # 🔃 SORTING
    if sort == "price_low":
        query += " ORDER BY food_items.price ASC"

    elif sort == "price_high":
        query += " ORDER BY food_items.price DESC"

    elif sort == "rating":
        query += " ORDER BY avg_rating DESC"

    else:
        query += " ORDER BY food_items.id DESC"

    cursor.execute(query, values)

    foods = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('menu.html', foods=foods)


# ADD TO CART
@user.route('/add_to_cart/<int:id>')
def add_to_cart(id):
    if 'cart' not in session:
        session['cart'] = {}

    cart = session['cart']

    if str(id) in cart:
        cart[str(id)] += 1
    else:
        cart[str(id)] = 1

    session['cart'] = cart
    return redirect(url_for('user.menu'))


# VIEW CART
@user.route('/cart')
def cart():

    if 'cart' not in session:
        return render_template('cart.html', items=[], total=0)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cart = session['cart']

    items = []
    total = 0

    for food_id, qty in cart.items():

        cursor.execute(
            "SELECT * FROM food_items WHERE id = %s",
            (food_id,)
        )

        item = cursor.fetchone()

        if item:

            # Store quantity
            item['quantity'] = qty

            # Calculate subtotal
            subtotal = item['price'] * item['quantity']

            # Store subtotal
            item['subtotal'] = subtotal

            # Add to total
            total += subtotal

            # Add item to list
            items.append(item)

    cursor.close()
    conn.close()

    return render_template(
        'cart.html',
        items=items,
        total=total
    )

# ✅ PLACE ORDER (NEW)
@user.route('/checkout')
def checkout():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if 'cart' not in session or not session['cart']:
        return redirect(url_for('user.menu'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cart = session['cart']
    user_id = session['user_id']

    total = 0

    # Calculate total
    for food_id, qty in cart.items():
        cursor.execute("SELECT price FROM food_items WHERE id = %s", (food_id,))
        result = cursor.fetchone()

        if result:
            price = result[0]
            total += float(price) * qty

    # Insert into orders
    cursor.execute(
        "INSERT INTO orders (user_id, total_amount) VALUES (%s, %s)",
        (user_id, total)
    )
    order_id = cursor.lastrowid

    # Insert order details
    for food_id, qty in cart.items():
        cursor.execute(
            "INSERT INTO order_details (order_id, food_id, quantity) VALUES (%s, %s, %s)",
            (order_id, food_id, qty)
        )

    conn.commit()
    cursor.close()
    conn.close()

    # Clear cart
    session.pop('cart', None)

    return render_template('order_success.html', order_id=order_id)
@user.route('/orders')
def orders():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM orders WHERE user_id = %s ORDER BY order_date DESC",
        (session['user_id'],)
    )
    orders = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('orders.html', orders=orders)

# ADD FEEDBACK
@user.route('/feedback/<int:food_id>', methods=['GET', 'POST'])
def feedback(food_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        rating = request.form['rating']
        comment = request.form['comment']
        user_id = session['user_id']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO feedback (user_id, food_id, rating, comment) VALUES (%s, %s, %s, %s)",
            (user_id, food_id, rating, comment)
        )
        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for('user.menu'))

    return render_template('feedback.html', food_id=food_id)


# VIEW USER ORDERS
@user.route('/my_orders')
def my_orders():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM orders
        WHERE user_id = %s
        ORDER BY id DESC
    """, (session['user_id'],))

    orders = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('my_orders.html', orders=orders)


from flask import request

@user.route('/food_items')
def food_items():
    search = request.args.get('search')

    conn = get_db_connection()
    cursor = conn.cursor()

    if search:
        cursor.execute("""
            SELECT food_items.*, categories.name AS category,
            AVG(feedback.rating) AS avg_rating
            FROM food_items
            LEFT JOIN categories ON food_items.category_id = categories.id
            LEFT JOIN feedback ON food_items.id = feedback.food_id
            WHERE food_items.name LIKE %s
            GROUP BY food_items.id
        """, ('%' + search + '%',))
    else:
        cursor.execute("""
            SELECT food_items.*, categories.name AS category,
            AVG(feedback.rating) AS avg_rating
            FROM food_items
            LEFT JOIN categories ON food_items.category_id = categories.id
            LEFT JOIN feedback ON food_items.id = feedback.food_id
            GROUP BY food_items.id
        """)

    items = cursor.fetchall()

    return render_template("food_items.html", items=items)






# ORDER DETAILS
@user.route('/order_details/<int:order_id>')
def order_details(order_id):

    # 🔐 User login check
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 🧾 Get order information
    cursor.execute("""
        SELECT *
        FROM orders
        WHERE id = %s
        AND user_id = %s
    """, (order_id, session['user_id']))

    order = cursor.fetchone()

    # ❌ If order not found
    if not order:
        cursor.close()
        conn.close()
        return "Order not found"

    # 🍔 Get ordered food items
    cursor.execute("""
        SELECT
            food_items.name,
            food_items.price,
            food_items.image,
            order_details.quantity

        FROM order_details

        INNER JOIN food_items
        ON order_details.food_id = food_items.id

        WHERE order_details.order_id = %s
    """, (order_id,))

    items = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'order_details.html',
        order=order,
        items=items
    )



# TRACK ORDER
@user.route('/track_order/<int:order_id>')
def track_order(order_id):

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT *
        FROM orders
        WHERE id = %s
    """, (order_id,))

    order = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        'track_order.html',
        order=order
    )




# PAYMENT PAGE
@user.route('/payment', methods=['GET', 'POST'])
def payment():

    print("PAYMENT PAGE OPENED")

    # 🔐 LOGIN CHECK
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    # 🛒 CART CHECK
    if 'cart' not in session or not session['cart']:
        return redirect(url_for('user.menu'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cart = session['cart']

    total = 0

    # 💰 CALCULATE TOTAL AMOUNT
    for food_id, qty in cart.items():

        cursor.execute(
            "SELECT price FROM food_items WHERE id = %s",
            (food_id,)
        )

        result = cursor.fetchone()

        if result:
            total += float(result[0]) * qty

    # ✅ PAYMENT SUBMIT
    if request.method == 'POST':

        print("FORM SUBMITTED")
        print(request.form)

        payment_method = request.form.get('payment_method')

        user_id = session['user_id']

        # 🧾 INSERT ORDER
        cursor.execute("""
            INSERT INTO orders
            (user_id, total_amount, payment_method, payment_status)
            VALUES (%s, %s, %s, %s)
        """, (
            user_id,
            total,
            payment_method,
            'Paid'
        ))

        order_id = cursor.lastrowid

        # 🍔 INSERT ORDER DETAILS
        for food_id, qty in cart.items():

            cursor.execute("""
                INSERT INTO order_details
                (order_id, food_id, quantity)
                VALUES (%s, %s, %s)
            """, (
                order_id,
                food_id,
                qty
            ))

        conn.commit()

        cursor.close()
        conn.close()

        # 🗑️ CLEAR CART
        session.pop('cart', None)

        return render_template(
            'payment_success.html',
            order_id=order_id
        )

    cursor.close()
    conn.close()

    return render_template(
        'payment.html',
        total=total
    )


# REMOVE FROM CART

@user.route('/remove_from_cart/<int:cart_id>')
def remove_from_cart(cart_id):

    # Database Connection
    conn = get_db_connection()
    cursor = conn.cursor()

    # Delete item from cart
    cursor.execute(
        "DELETE FROM cart WHERE id=%s",
        (cart_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    flash("Item removed from cart successfully", "danger")

    return redirect(url_for('user.view_cart'))


# UPDATE QUANTITY IN CART 
# UPDATE QUANTITY IN CART
@user.route('/update_cart/<int:food_id>', methods=['POST'])
def update_cart(food_id):

    quantity = int(request.form['quantity'])

    cart = session.get('cart', {})

    if str(food_id) in cart:

        if quantity > 0:
            cart[str(food_id)] = quantity
        else:
            cart.pop(str(food_id), None)

    session['cart'] = cart

    flash("Cart updated successfully", "success")

    return redirect(url_for('user.cart'))



# CANCEL ORDER
@user.route('/cancel_order/<int:order_id>')
def cancel_order(order_id):

    conn = get_db_connection()

    cursor = conn.cursor(dictionary=True)

    # Get order
    cursor.execute(
        "SELECT * FROM orders WHERE id=%s",
        (order_id,)
    )

    order = cursor.fetchone()

    # Check if already delivered
    if order['status'] == 'Delivered':

        flash(
            "Delivered orders cannot be cancelled",
            "danger"
        )

        return redirect(url_for('user.my_orders'))

    # Cancel order
    cursor.execute("""
        UPDATE orders
        SET status='Cancelled'
        WHERE id=%s
    """, (order_id,))

    conn.commit()

    cursor.close()
    conn.close()

    flash(
        "Order cancelled successfully",
        "warning"
    )

    return redirect(url_for('user.my_orders'))