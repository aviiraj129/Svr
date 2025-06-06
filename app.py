from flask import Flask, request, session, redirect, url_for, render_template_string, jsonify
import os
import requests
import threading
import time
import json

app = Flask(__name__)
app.secret_key = "your_secret_key"

RUNNING_SCRIPTS_FOLDER = "running_scripts"

# GitHub Links
USER_LIST_URL = "https://raw.githubusercontent.com/aviiraj129/Svr/main/aproble.txt"
LOGIN_HTML_URL = "https://raw.githubusercontent.com/aviiraj129/Svr/main/login.html"
DASHBOARD_HTML_URL = "https://raw.githubusercontent.com/aviiraj129/Svr/main/dashboard.html"

# WhatsApp Redirect
WHATSAPP_LINK = "https://wa.me/qr/6E2NQM6I3SDQM1"
WHATSAPP_MESSAGE = "Hello Avii Bhaiya, mai apka server use krna chahta hu, please aproble dedo whatsapp ka jaruri hai."

# Cache
USER_LIST = set()
LOGIN_HTML = ""
DASHBOARD_HTML = ""

# Ensure required folders exist
if not os.path.exists(RUNNING_SCRIPTS_FOLDER):
    os.makedirs(RUNNING_SCRIPTS_FOLDER)

# Fetch GitHub resources
def fetch_users():
    global USER_LIST
    try:
        response = requests.get(USER_LIST_URL)
        if response.status_code == 200:
            USER_LIST = set(line.strip() for line in response.text.strip().splitlines() if line.strip())
        else:
            print("Failed to fetch users list.")
    except Exception as e:
        print(f"Error fetching user list: {e}")

def fetch_html_templates():
    global LOGIN_HTML, DASHBOARD_HTML
    try:
        login_resp = requests.get(LOGIN_HTML_URL)
        if login_resp.status_code == 200:
            LOGIN_HTML = login_resp.text
        else:
            LOGIN_HTML = "<h2>Login Page Failed to Load</h2>"

        dashboard_resp = requests.get(DASHBOARD_HTML_URL)
        if dashboard_resp.status_code == 200:
            DASHBOARD_HTML = dashboard_resp.text
        else:
            DASHBOARD_HTML = "<h2>Dashboard Failed to Load</h2>"

    except Exception as e:
        print(f"Error fetching HTML templates: {e}")

fetch_users()
fetch_html_templates()

# Validate login
def check_login(username, password):
    return username in USER_LIST and password == "aproble"

# Get running scripts
def get_running_scripts(username):
    running_scripts = []
    for file in os.listdir(RUNNING_SCRIPTS_FOLDER):
        if file.startswith(username):
            with open(os.path.join(RUNNING_SCRIPTS_FOLDER, file), "r") as f:
                script_data = json.load(f)
                running_scripts.append(script_data)
    return running_scripts

def save_running_script(username, script_data):
    script_id = script_data['id']
    script_file_path = os.path.join(RUNNING_SCRIPTS_FOLDER, f"{username}_{script_id}.json")
    with open(script_file_path, "w") as f:
        json.dump(script_data, f)

def remove_running_script(username, script_id):
    script_file_path = os.path.join(RUNNING_SCRIPTS_FOLDER, f"{username}_{script_id}.json")
    if os.path.exists(script_file_path):
        os.remove(script_file_path)
    user_folder = f"users/{username}"
    if os.path.exists(user_folder):
        for file in os.listdir(user_folder):
            if script_id in file:
                os.remove(os.path.join(user_folder, file))

# Message sending
def send_messages(script_data):
    convo_id = script_data["convo_id"]
    haters_name = script_data["haters_name"]
    speed = script_data["speed"]
    tokens_path = script_data["tokens_path"]
    messages_path = script_data["messages_path"]

    with open(tokens_path, 'r') as f:
        tokens = [line.strip() for line in f.readlines()]
    with open(messages_path, 'r') as f:
        messages = [line.strip() for line in f.readlines()]

    token_index = 0
    message_index = 0
    total_tokens = len(tokens)
    total_messages = len(messages)

    while True:
        if total_tokens == 0 or total_messages == 0:
            print("Tokens या Messages file खाली है!")
            break

        token = tokens[token_index]
        message = messages[message_index]

        url = f"https://graph.facebook.com/v17.0/t_{convo_id}"
        payload = {"access_token": token, "message": f"{haters_name} {message}"}
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            print(f"Message sent successfully: {message}")
        else:
            print(f"Failed to send message: {response.text}")

        token_index = (token_index + 1) % total_tokens
        message_index = (message_index + 1) % total_messages
        time.sleep(speed)

# Restart saved scripts on server reboot
def start_running_scripts_on_restart():
    for file in os.listdir(RUNNING_SCRIPTS_FOLDER):
        if file.endswith('.json'):
            with open(os.path.join(RUNNING_SCRIPTS_FOLDER, file), "r") as f:
                script_data = json.load(f)
                threading.Thread(target=send_messages, args=(script_data,), daemon=True).start()

start_running_scripts_on_restart()

@app.route('/')
def index():
    if not session.get("username"):
        return render_template_string(LOGIN_HTML)
    running_scripts = get_running_scripts(session.get("username"))
    dashboard_rendered = render_template_string(DASHBOARD_HTML, username=session.get("username"), running_scripts=running_scripts)
    return dashboard_rendered

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    if not check_login(username, password):
        redirect_url = f"{WHATSAPP_LINK}?text={WHATSAPP_MESSAGE.replace(' ', '%20')}"
        return redirect(redirect_url)

    session['username'] = username
    return redirect(url_for('index'))

@app.route('/logout', methods=['POST'])
def logout():
    session.pop("username", None)
    return redirect(url_for('index'))

@app.route('/start', methods=['POST'])
def start_messaging():
    if not session.get("username"):
        return jsonify({"message": "Login Required"}), 403

    username = session.get("username")
    user_folder = f"users/{username}"
    os.makedirs(user_folder, exist_ok=True)

    convo_id = request.form.get('convoId')
    haters_name = request.form.get('hatersName')
    speed = int(request.form.get('speed'))

    tokens_file = request.files['tokensFile']
    messages_file = request.files['messagesFile']

    script_id = str(int(time.time()))
    tokens_path = os.path.join(user_folder, f"tokens_{script_id}.txt")
    messages_path = os.path.join(user_folder, f"messages_{script_id}.txt")

    tokens_file.save(tokens_path)
    messages_file.save(messages_path)

    script_data = {
        "id": script_id,
        "convo_id": convo_id,
        "haters_name": haters_name,
        "speed": speed,
        "tokens_path": tokens_path,
        "messages_path": messages_path
    }

    save_running_script(username, script_data)
    threading.Thread(target=send_messages, args=(script_data,), daemon=True).start()
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop_script():
    if not session.get("username"):
        return jsonify({"message": "Login Required"}), 403

    script_id = request.form.get("script_id")
    remove_running_script(session.get("username"), script_id)
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 20761))
    app.run(host='0.0.0.0', port=port)
