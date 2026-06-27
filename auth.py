from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.db import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint('auth', __name__)

# REGISTER
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        print("Register form submitted")

        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        phone = request.form['phone']

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (name, email, password, phone) VALUES (%s, %s, %s, %s)",
                (name, email, password, phone)
            )
            conn.commit()

            print("User inserted successfully")

            flash("Registration Successful! Please login.")
            return redirect(url_for('auth.login'))   # ✅ better than '/login'

        except Exception as e:
            print("ERROR:", e)
            flash("Error occurred while registering")

        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')


# LOGIN
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        print("Login form submitted")

        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        print("User from DB:", user)

        cursor.close()
        conn.close()

        if user:

            # 🚫 BLOCK CHECK (ADD HERE)
            if user.get('is_blocked'):   # safer using .get()
                flash("Your account is blocked by admin")
                return redirect(url_for('auth.login'))

            # ✅ PASSWORD CHECK
            if check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['user_name'] = user['name']

                flash("Login Successful!")
                return redirect(url_for('home'))
            else:
                flash("Invalid email or password")

        else:
            flash("Invalid email or password")

    return render_template('login.html')


# LOGOUT
@auth.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully")
    return redirect(url_for('auth.login'))