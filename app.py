from flask import Flask, render_template, request, redirect, url_for
import os
import webbrowser

app = Flask(__name__)

PASSWORD = "jaanu@123"  # sabka same password
WHATSAPP_URL = "https://wa.me/918340514701?text=hello%20avii%20bhaii%20mera%20user%20name%20aproble%20krdo%20ok"

def is_user_allowed(username):
    if not os.path.exists("aproble.txt"):
        return False
    with open("aproble.txt", "r") as f:
        allowed_users = [line.strip() for line in f.readlines()]
    return username in allowed_users

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if password == PASSWORD:
            if is_user_allowed(username):
                return redirect(url_for("dashboard"))
            else:
                try:
                    # On Render this will be ignored, but locally it works
                    webbrowser.open(WHATSAPP_URL)
                except:
                    pass
                return "<h3 style='color:red;'>Username not approved. WhatsApp message prefilled. Please contact Avii Bhai.</h3>"
        else:
            return "<h3 style='color:red;'>Wrong password.</h3>"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=20761)