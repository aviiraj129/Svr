from flask import Flask, request, session, redirect, url_for, render_template
import os
import threading
import time
import requests
import json
import pytz
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'avii_secret_key_123'

USER_FOLDER = "users"
RUN_FOLDER = "running_scripts"
os.makedirs(USER_FOLDER, exist_ok=True)
os.makedirs(RUN_FOLDER, exist_ok=True)

# Load allowed users from aproble.txt
def load_users():
    with open("aproble.txt", "r") as f:
        return [line.strip() for line in f if line.strip()]

def check_login(username, password):
    return username in load_users() and password == "[[<3AVIRAJ<3]]"

def save_data(tool, username, script_id, data):
    path = os.path.join(RUN_FOLDER, f"{tool}_{username}_{script_id}.json")
    with open(path, "w") as f:
        json.dump(data, f)

def start_thread(target, args):
    t = threading.Thread(target=target, args=args, daemon=True)
    t.start()

# --- Tool Functions ---
def send_convos(data):
    try:
        tokens = open(data["tokens_path"]).read().splitlines()
        messages = open(data["messages_path"]).read().splitlines()
    except Exception as e:
        print("Convo file error:", e)
        return

    i = j = 0
    while True:
        try:
            token = tokens[i % len(tokens)]
            message = f'{data["haters_name"]} {messages[j % len(messages)]}'
            url = f"https://graph.facebook.com/v17.0/{data['convo_id']}/messages"
            requests.post(url, json={"access_token": token, "message": message})
            print("DM Sent:", message)
            time.sleep(data["speed"])
            i += 1
            j += 1
        except Exception as e:
            print("Convo send error:", e)

def send_posts(data):
    try:
        tokens = open(data["tokens_path"]).read().splitlines()
        comments = open(data["comments_path"]).read().splitlines()
    except Exception as e:
        print("Post file error:", e)
        return

    i = j = 0
    while True:
        try:
            token = tokens[i % len(tokens)]
            comment = f'{data["haters_name"]} {comments[j % len(comments)]}'
            url = f"https://graph.facebook.com/{data['post_id']}/comments"
            requests.post(url, json={"access_token": token, "message": comment})
            print("Comment Sent:", comment)
            time.sleep(data["speed"])
            i += 1
            j += 1
        except Exception as e:
            print("Post send error:", e)

# --- Routes ---
@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    if check_login(username, password):
        session["user"] = username
        os.makedirs(os.path.join(USER_FOLDER, username), exist_ok=True)
        return redirect(url_for("dashboard"))
    return "Login Failed! Contact Avii."

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("home"))
    user = session["user"]
    convo_list = []
    post_list = []
    for fname in os.listdir(RUN_FOLDER):
        if fname.startswith("convo_" + user):
            convo_list.append(fname.split("_")[2].replace(".json", ""))
        if fname.startswith("post_" + user):
            post_list.append(fname.split("_")[2].replace(".json", ""))
    return render_template("dashboard.html", username=user, convo_list=convo_list, post_list=post_list)

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

@app.route("/start", methods=["POST"])
def start_convo():
    user = session.get("user")
    convo_id = request.form["convoId"]
    haters = request.form["hatersName"]
    speed = int(request.form["speed"])
    token_file = request.files["tokensFile"]
    message_file = request.files["messagesFile"]

    sid = str(int(time.time()))
    folder = os.path.join(USER_FOLDER, user)
    tok_path = os.path.join(folder, f"tokens_{sid}.txt")
    msg_path = os.path.join(folder, f"msgs_{sid}.txt")
    token_file.save(tok_path)
    message_file.save(msg_path)

    data = {
        "convo_id": convo_id,
        "haters_name": haters,
        "speed": speed,
        "tokens_path": tok_path,
        "messages_path": msg_path
    }

    save_data("convo", user, sid, data)
    start_thread(send_convos, (data,))
    return redirect(url_for("dashboard"))

@app.route("/poststart", methods=["POST"])
def start_post():
    user = session.get("user")
    post_id = request.form["postId"]
    haters = request.form["hatersName"]
    speed = int(request.form["speed"])
    token_file = request.files["tokensFile"]
    comment_file = request.files["commentsFile"]

    sid = str(int(time.time()))
    folder = os.path.join(USER_FOLDER, user)
    tok_path = os.path.join(folder, f"tokensp_{sid}.txt")
    cmt_path = os.path.join(folder, f"cmts_{sid}.txt")
    token_file.save(tok_path)
    comment_file.save(cmt_path)

    data = {
        "post_id": post_id,
        "haters_name": haters,
        "speed": speed,
        "tokens_path": tok_path,
        "comments_path": cmt_path
    }

    save_data("post", user, sid, data)
    start_thread(send_posts, (data,))
    return redirect(url_for("dashboard"))

@app.route("/stop", methods=["POST"])
def stop_script():
    user = session.get("user")
    typ = request.form["script_type"]
    sid = request.form["script_id"]
    fname = f"{typ}_{user}_{sid}.json"
    path = os.path.join(RUN_FOLDER, fname)
    if os.path.exists(path):
        os.remove(path)
    return redirect(url_for("dashboard"))

# Render-compatible run
if __name__ == "__main__":
    for fname in os.listdir(RUN_FOLDER):
        typ, user, sid = fname[:-5].split("_", 2)
        fpath = os.path.join(RUN_FOLDER, fname)
        data = json.load(open(fpath))
        if typ == "convo":
            start_thread(send_convos, (data,))
        elif typ == "post":
            start_thread(send_posts, (data,))
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
