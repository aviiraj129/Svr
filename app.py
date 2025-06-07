from flask import Flask, request, session, redirect, url_for, render_template_string, jsonify
import os, requests, threading, time, json

app = Flask(__name__)
app.secret_key = "secret"

# Remote GitHub resources
USER_LIST_URL = "https://raw.githubusercontent.com/aviiraj129/Svr/main/aproble.txt"
LOGIN_HTML_URL = "https://raw.githubusercontent.com/aviiraj129/Svr/main/login.html"
DASHBOARD_HTML_URL = "https://raw.githubusercontent.com/aviiraj129/Svr/main/dashboard.html"

# WhatsApp fallback
WHATSAPP_LINK = "https://wa.me/qr/6E2NQM6I3SDQM1"
WHATSAPP_MSG = "Hello Avii Bhaiya, mai apka server use krna chahta hu, please aproble dedo whatsapp ka jaruri hai."

# App folders
SCRIPT_DIR = "running_scripts"
USER_DIR = "users"
os.makedirs(SCRIPT_DIR, exist_ok=True)
os.makedirs(USER_DIR, exist_ok=True)

# In-memory data
USERS = set()
LOGIN_HTML = ""
DASHBOARD_HTML = ""

# Load GitHub content
def load_data():
    global USERS, LOGIN_HTML, DASHBOARD_HTML
    try:
        r = requests.get(USER_LIST_URL)
        if r.ok: USERS = set(r.text.strip().splitlines())
        LOGIN_HTML = requests.get(LOGIN_HTML_URL).text or "<h3>Login Fail</h3>"
        DASHBOARD_HTML = requests.get(DASHBOARD_HTML_URL).text or "<h3>Dashboard Fail</h3>"
    except: pass
load_data()

def is_valid_user(username, password):
    return username in USERS and password == "aproble"

def save_script(username, data):
    path = os.path.join(SCRIPT_DIR, f"{username}_{data['id']}.json")
    with open(path, "w") as f: json.dump(data, f)

def get_user_scripts(username):
    scripts = []
    for file in os.listdir(SCRIPT_DIR):
        if file.startswith(username):
            with open(os.path.join(SCRIPT_DIR, file)) as f:
                scripts.append(json.load(f))
    return scripts

def delete_script(username, script_id):
    path = os.path.join(SCRIPT_DIR, f"{username}_{script_id}.json")
    if os.path.exists(path): os.remove(path)
    udir = os.path.join(USER_DIR, username)
    if os.path.exists(udir):
        for f in os.listdir(udir):
            if script_id in f:
                os.remove(os.path.join(udir, f))

def send_loop(data):
    try:
        with open(data["tokens_path"]) as f: tokens = f.read().splitlines()
        with open(data["messages_path"]) as f: messages = f.read().splitlines()
        i, j = 0, 0
        while True:
            token = tokens[i % len(tokens)]
            msg = messages[j % len(messages)]
            r = requests.post(
                f"https://graph.facebook.com/v17.0/t_{data['convo_id']}",
                json={"access_token": token, "message": f"{data['haters_name']} {msg}"}
            )
            print("✅" if r.ok else f"❌ {r.text}")
            i += 1; j += 1
            time.sleep(data["speed"])
    except Exception as e:
        print("Error in send_loop:", e)

@app.route('/')
def home():
    user = session.get("username")
    if not user: return render_template_string(LOGIN_HTML)
    scripts = get_user_scripts(user)
    return render_template_string(DASHBOARD_HTML, username=user, running_scripts=scripts)

@app.route('/login', methods=['POST'])
def login():
    u, p = request.form['username'], request.form['password']
    if not is_valid_user(u, p):
        link = f"{WHATSAPP_LINK}?text={WHATSAPP_MSG.replace(' ', '%20')}"
        return redirect(link)
    session['username'] = u
    return redirect(url_for("home"))

@app.route('/logout', methods=['POST'])
def logout():
    session.pop("username", None)
    return redirect(url_for("home"))

@app.route('/start', methods=['POST'])
def start():
    user = session.get("username")
    if not user: return jsonify({"error": "Login required"}), 403
    uid = str(int(time.time()))
    udir = os.path.join(USER_DIR, user)
    os.makedirs(udir, exist_ok=True)
    convo_id = request.form['convoId']
    name = request.form['hatersName']
    speed = int(request.form['speed'])
    tokens_path = os.path.join(udir, f"tokens_{uid}.txt")
    messages_path = os.path.join(udir, f"messages_{uid}.txt")
    request.files['tokensFile'].save(tokens_path)
    request.files['messagesFile'].save(messages_path)
    data = {
        "id": uid, "convo_id": convo_id, "haters_name": name,
        "speed": speed, "tokens_path": tokens_path, "messages_path": messages_path
    }
    save_script(user, data)
    threading.Thread(target=send_loop, args=(data,), daemon=True).start()
    return redirect(url_for("home"))

@app.route('/stop', methods=['POST'])
def stop():
    user = session.get("username")
    if not user: return jsonify({"error": "Login required"}), 403
    sid = request.form["script_id"]
    delete_script(user, sid)
    return redirect(url_for("home"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
