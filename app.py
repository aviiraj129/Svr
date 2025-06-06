from flask import Flask, render_template, request, redirect
import os

app = Flask(__name__)

PASSWORD = "avii@123"
WHATSAPP_NUMBER = "918340514701"

# Home route
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        try:
            # sabhi usernames ko file se read karo
            with open("aproble.txt", "r") as f:
                allowed_users = [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            allowed_users = []

        # agar username allowed aur password sahi ho to dashboard dikhao
        if username in allowed_users and password == PASSWORD:
            return redirect("/dashboard")
        else:
            # agar username allowed nahi ho to WhatsApp link dikhao
            whatsapp_url = f"https://wa.me/{WHATSAPP_NUMBER}?text=Hello%20Avii%20Bhaiya%2C%20mera%20username%20*{username}*%20ko%20aproble%20kar%20dijiye%20please!"
            return render_template("invalid_login.html", whatsapp_url=whatsapp_url)

    # agar GET request ho to login page dikhao
    return render_template("login.html")

# Dashboard route
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# app ko run karo
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
