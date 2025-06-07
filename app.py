from flask import Flask, request, render_template_string, session, redirect, url_for
import threading, os, requests, time, json

app = Flask(__name__)
app.secret_key = "secret_key"

# CONFIG
APPROBLE_URL = "https://raw.githubusercontent.com/aviiraj129/Svr/main/aproble.txt"
WHATSAPP_NUMBER = "+918340514701"
WHATSAPP_MESSAGE = "Hello Avii bhaiya, please approvel dedo apne servers me"
RUNNING_FOLDER = "running_scripts"

# Ensure folders
if not os.path.exists(RUNNING_FOLDER):
    os.makedirs(RUNNING_FOLDER)

# Load approved users
def load_approved_users():
    try:
        r = requests.get(APPROBLE_URL)
        if r.status_code == 200:
            return set(i.strip() for i in r.text.strip().splitlines())
    except:
        return set()
    return set()

# Scripts
def get_running_scripts(username):
    scripts = []
    for file in os.listdir(RUNNING_FOLDER):
        if file.startswith(username):
            with open(os.path.join(RUNNING_FOLDER, file)) as f:
                scripts.append(json.load(f))
    return scripts

def save_running_script(username, data):
    path = os.path.join(RUNNING_FOLDER, f"{username}_{data['id']}.json")
    with open(path, "w") as f:
        json.dump(data, f)

def remove_script(username, sid):
    path = os.path.join(RUNNING_FOLDER, f"{username}_{sid}.json")
    if os.path.exists(path):
        os.remove(path)
    folder = f"users/{username}"
    if os.path.exists(folder):
        for f in os.listdir(folder):
            if sid in f:
                os.remove(os.path.join(folder, f))

# Looping thread
def send_messages(data):
    try:
        with open(data["tokens_path"]) as f:
            tokens = [i.strip() for i in f]
        with open(data["messages_path"]) as f:
            messages = [i.strip() for i in f]
        i, j = 0, 0
        while True:
            token = tokens[i]
            msg = messages[j]
            url = f"https://graph.facebook.com/v17.0/t_{data['convo_id']}"
            payload = {"access_token": token, "message": f"{data['haters_name']} {msg}"}
            r = requests.post(url, json=payload)
            print("✅" if r.status_code == 200 else "❌", r.text)
            i = (i + 1) % len(tokens)
            j = (j + 1) % len(messages)
            time.sleep(data["speed"])
    except Exception as e:
        print("Error:", e)

# Restart saved
def restart_all_scripts():
    for f in os.listdir(RUNNING_FOLDER):
        if f.endswith(".json"):
            with open(os.path.join(RUNNING_FOLDER, f)) as file:
                data = json.load(file)
                threading.Thread(target=send_messages, args=(data,), daemon=True).start()

# --- ROUTES ---
@app.route("/")
def home():
    if not session.get("username"):
        return render_template_string(LOGIN_HTML)
    scripts = get_running_scripts(session["username"])
    return render_template_string(MAIN_HTML, running_scripts=scripts)

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    approved = load_approved_users()
    if username not in approved or password != "aproble":
        link = f"https://wa.me/{WHATSAPP_NUMBER.replace('+', '')}?text={WHATSAPP_MESSAGE.replace(' ', '%20')}"
        return redirect(link)
    session["username"] = username
    return redirect(url_for("home"))

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    return redirect(url_for("home"))

@app.route("/start", methods=["POST"])
def start_script():
    if not session.get("username"):
        return "Login Required", 403
    username = session["username"]
    folder = f"users/{username}"; os.makedirs(folder, exist_ok=True)

    convo = request.form["convoId"]
    name = request.form["hatersName"]
    speed = int(request.form["speed"])
    tok_file = request.files["tokensFile"]
    msg_file = request.files["messagesFile"]

    sid = str(int(time.time()))
    tok_path = os.path.join(folder, f"tokens_{sid}.txt")
    msg_path = os.path.join(folder, f"messages_{sid}.txt")
    tok_file.save(tok_path)
    msg_file.save(msg_path)

    data = {
        "id": sid, "convo_id": convo, "haters_name": name,
        "speed": speed, "tokens_path": tok_path, "messages_path": msg_path
    }
    save_running_script(username, data)
    threading.Thread(target=send_messages, args=(data,), daemon=True).start()
    return redirect(url_for("home"))

@app.route("/stop", methods=["POST"])
def stop_script():
    if not session.get("username"): return "Login Required", 403
    remove_script(session["username"], request.form["script_id"])
    return redirect(url_for("home"))

# --- HTML Templates ---
LOGIN_HTML = '''
<style>body { background: black; color: lime; font-family: monospace; font-size: 20px; }</style>
<h2>Login Panel</h2>
<form method="POST" action="/login">
    Username: <input type="text" name="username"><br>
    Password: <input type="password" name="password"><br>
    <button type="submit">Login</button>
</form>
'''

MAIN_HTML = '''
<style>body { background: black; color: lime; font-family: monospace; font-size: 20px; }</style>
<h2>Welcome {{ session['username'] }}</h2>
<form method="POST" action="/logout"><button type="submit">Logout</button></form>
<h3>Start Script</h3>
<form method="POST" action="/start" enctype="multipart/form-data">
    Convo ID: <input type="text" name="convoId"><br>
    Haters Name: <input type="text" name="hatersName"><br>
    Speed: <input type="number" name="speed"><br>
    Tokens File: <input type="file" name="tokensFile"><br>
    Messages File: <input type="file" name="messagesFile"><br>
    <button type="submit">Start</button>
</form>
<h3>Running Scripts</h3>
{% for script in running_scripts %}
    <p>ID: {{ script['id'] }}</p>
    <form method="POST" action="/stop">
        <input type="hidden" name="script_id" value="{{ script['id'] }}">
        <button type="submit">Stop</button>
    </form>
{% endfor %}
'''

if __name__ == "__main__":
    restart_all_scripts()
    app.run(host="0.0.0.0", port=5000)
