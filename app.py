from flask import Flask, render_template
import webbrowser
from threading import Timer

from routes.auth import auth
from routes.user import user
from routes.admin import admin

app = Flask(__name__)

# 🔐 Secret Key (IMPORTANT)
app.config['SECRET_KEY'] = 'supersecretkey'

# 📁 Optional: Upload folder (for future image upload feature)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# 🔗 Register Blueprints
app.register_blueprint(auth)
app.register_blueprint(user)
app.register_blueprint(admin)


# 🏠 Home Route
@app.route("/")
def home():
    return render_template("index.html")


# 🚫 Handle 404 Errors (Professional touch)
@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


# 🚨 Handle 500 Errors
@app.errorhandler(500)
def server_error(error):
    return render_template("500.html"), 500


# 🌐 Auto Open Browser
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")


# ▶️ Run App
if __name__ == "__main__":
    Timer(1, open_browser).start()
    app.run(debug=True)



