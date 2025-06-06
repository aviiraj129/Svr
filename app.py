from flask import Flask, render_template, request, redirect
import webbrowser
import os

app = Flask(__name__)

# Universal password
PASSWORD = "avii@123"

# Indian WhatsApp number
WHATSAPP_NUMBER = "918340514701"

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        try:
            with open("aproble.txt", "r") as f:
                allowed_users = [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            allowed_users = []

        if username in allowed_users and password == PASSWORD:
            return redirect("/dashboard")
        else:
            # Only open WhatsApp if username is NOT in allowed list
            if username not in allowed_users:
                whatsapp_url = f"https://wa.me/{WHATSAPP_NUMBER}?text=Hello%20Avii%20Bhaiya%2C%20mera%20username%20*{username}*%20ko%20aproble%20kar%20dijiye%20please!"
                try:
                    webbrowser.open(whatsapp_url)
                except:
                    pass  # Render pe direct open nahi hoga, but user click kar sakta hai
            return "Invalid login. Please contact Avii Bhaiya."

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 20761))
    app.run(debug=True, host="0.0.0.0", port=port)
