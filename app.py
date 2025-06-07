from flask import Flask, request, session, redirect, url_for, render_template_string, jsonify
import os, requests, json, time, threading

app = Flask(__name__)
app.secret_key = "secret_key"

# GitHub Hosted Files
USER_LIST_URL = "https://raw.githubusercontent.com/aviiraj129/Svr/main/aproble.txt"
LOGIN_HTML_URL = "https://raw.githubusercontent.com/aviiraj129/Svr/main/login.html"
DASHBOARD_HTML_URL = "https://raw.githubusercontent.com/aviiraj129/Svr/main/dashboard.html"

# WhatsApp Info
WHATSAPP_LINK = "https://wa.me/qr/6E2NQM6I3SDQM1"
WHATSAPP_MSG = "Hello Avii Bhaiya, mai apka server use krna chahta hu, please aproble dedo whatsapp ka jaruri hai."

# Folder Setup
RUNNING_FOLDER = "running_scripts"
if not os.path.exists(RUNNING_FOLDER):
    os.makedirs(RUNNING_FOLDER)

# Global Cache
USERS = set()
LOGIN_HTML = ""
DASHBOARD_HTML = ""

# --- GitHub Loaders ---
def load_users():
    global USERS
    try:
        r = requests.get(USER_LIST_URL)
        if r.status_code == 200:
            USERS = set(line.strip() for line in r.text.strip().splitlines())
    except: pass

def load_html():
    global LOGIN_HTML, DASHBOARD_HTML
    try:
        r1 = requests.get(LOGIN_HTML_URL)
        r2 = requests.get(DASHBOARD_HTML_URL)
        LOGIN_HTML = r1.text if r1.status_code == 200 else "<h3>Login Error</h3>"
        DASHBOARD_HTML = r2.text if r2.status_code == 200 else "<h3>Dashboard Error</h3>"
    except: pass

load_users()
load_html()

# --- Auth Check ---
def is_valid_user(username, password):
    return username in USERS and password == "aproble"

# --- File System Functions ---
def get_user_scripts(username):
    data = []
    for f in os.listdir(RUNNING_FOLDER):
        if f.startswith(username):
            with open(os.path.join(RUNNING_FOLDER, f)) as file:
                data.append(json.load(file))
    return data

def save_script(username, data):
    path = os.path.join(RUNNING_FOLDER, f"{username}_{data['id']}.json")
    with open(path, "w") as f:
        json.dump(data, f)

def delete_script(username, script_id):
    path = os.path.join(RUNNING_FOLDER, f"{username}_{script_id}.json")
    if os.path.exists(path): os.remove(path)

# --- Messaging Loop ---
def send_loop(data):
    convo = data["convo_id"]
    name = data["haters_name"]
    speed = data["speed"]
    with open(data["tokens_path"]) as f: tokens = [i.strip() for i in f]
    with open(data["messages_path"]) as f: messages = [i.strip() for i in f]
    i, j = 0, 0
    while True:
        if not tokens or not messages: break
        token = tokens[i]; msg = messages[j]
        url = f"https://graph.facebook.com/v17.0/t_{convo}"
        r = requests.post(url, json={"access_token": token, "message": f"{name} {msg}"})
        print("✅" if r.status_code == 200 else "❌", r.text)
        i = (i + 1) % len(tokens)
        j = (j + 1) % len(messages)
        time.sleep(speed)

# --- Restart on Reboot ---
def restart_scripts():
    for f in os.listdir(RUNNING_FOLDER):
        if f.endswith(".json"):
            with open(os.path.join(RUNNING_FOLDER, f)) as file:
                data = json.load(file)
                threading.Thread(target=send_loop, args=(data,), daemon=True).start()
restart_scripts()

# --- Routes ---
@app.route("/", methods=["GET"])
def index():
    if not session.get("username"):
        return render_template_string(LOGIN_HTML)
    scripts = get_user_scripts(session["username"])
    return render_template_string(DASHBOARD_HTML, username=session["username"], running_scripts=scripts)

@app.route("/login", methods=["POST"])
def login():
    u = request.form.get("username")
    p = request.form.get("password")
    if not is_valid_user(u, p):
        link = f"{WHATSAPP_LINK}?text={WHATSAPP_MSG.replace(' ', '%20')}"
        return redirect(link)
    session["username"] = u
    return redirect(url_for("index"))

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    return redirect(url_for("index"))

@app.route("/start", methods=["POST"])
def start():
    if not session.get("username"):
        return "Login Required", 403
    u = session["username"]
    folder = f"users/{u}"; os.makedirs(folder, exist_ok=True)

    convo_id = request.form["convoId"]
    haters_name = request.form["hatersName"]
    speed = int(request.form["speed"])
    token_file = request.files["tokensFile"]
    msg_file = request.files["messagesFile"]

    sid = str(int(time.time()))
    tok_path = os.path.join(folder, f"tokens_{sid}.txt")
    msg_path = os.path.join(folder, f"messages_{sid}.txt")
    token_file.save(tok_path)
    msg_file.save(msg_path)

    data = {
        "id": sid, "convo_id": convo_id, "haters_name": haters_name,
        "speed": speed, "tokens_path": tok_path, "messages_path": msg_path
    }
    save_script(u, data)
    threading.Thread(target=send_loop, args=(data,), daemon=True).start()
    return redirect(url_for("index"))

@app.route("/stop", methods=["POST"])
def stop():
    if not session.get("username"): return "Login Required", 403
    sid = request.form["script_id"]
    delete_script(session["username"], sid)
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
