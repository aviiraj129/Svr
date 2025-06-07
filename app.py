from flask import Flask, request, render_template_string, session, redirect, url_for
import threading
import os
import requests
import time
import json
import urllib.parse

app = Flask(__name__)
app.secret_key = "avii_secret_key_123"

# Folder & file setup
RUNNING_SCRIPTS_FOLDER = "running_scripts"
USERS_FILE = "aproble.txt"  # Your GitHub file content can be saved here locally or fetched live (see note)
WHATSAPP_NUMBER = "918340514701"
WHATSAPP_MSG = "Hello%20Avii%20bhaiya,%20please%20approvel%20dedo%20apne%20servers%20me"

if not os.path.exists(RUNNING_SCRIPTS_FOLDER):
    os.makedirs(RUNNING_SCRIPTS_FOLDER)

# Load allowed users from aproble.txt (locally for simplicity)
def load_users():
    if not os.path.exists(USERS_FILE):
        return set()
    with open(USERS_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

ALLOWED_USERS = load_users()

# Login check: username must be in allowed users, password fixed 'aproble'
def check_login(username, password):
    return username in ALLOWED_USERS and password == "aproble"

# Save running script
def save_script(username, data):
    path = os.path.join(RUNNING_SCRIPTS_FOLDER, f"{username}_{data['id']}.json")
    with open(path, "w") as f:
        json.dump(data, f)

# Get running scripts for user
def get_scripts(username):
    scripts = []
    for f in os.listdir(RUNNING_SCRIPTS_FOLDER):
        if f.startswith(username):
            try:
                with open(os.path.join(RUNNING_SCRIPTS_FOLDER, f)) as file:
                    scripts.append(json.load(file))
            except: pass
    return scripts

# Delete script and related files
def delete_script(username, script_id):
    path = os.path.join(RUNNING_SCRIPTS_FOLDER, f"{username}_{script_id}.json")
    if os.path.exists(path):
        os.remove(path)
    user_folder = f"users/{username}"
    if os.path.exists(user_folder):
        for file in os.listdir(user_folder):
            if script_id in file:
                os.remove(os.path.join(user_folder, file))

# Message sending loop
def send_loop(data):
    convo_id = data["convo_id"]
    haters_name = data["haters_name"]
    speed = data["speed"]
    tokens_path = data["tokens_path"]
    messages_path = data["messages_path"]

    try:
        with open(tokens_path) as f:
            tokens = [line.strip() for line in f if line.strip()]
        with open(messages_path) as f:
            messages = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print("Error reading tokens/messages:", e)
        return

    if not tokens or not messages:
        print("Tokens ya messages file khali hai!")
        return

    i, j = 0, 0
    while True:
        token = tokens[i]
        message = messages[j]
        url = f"https://graph.facebook.com/v17.0/t_{convo_id}"
        payload = {"access_token": token, "message": f"{haters_name} {message}"}
        try:
            r = requests.post(url, json=payload)
            if r.status_code == 200:
                print(f"✅ Sent: {message}")
            else:
                print(f"❌ Failed: {r.text}")
        except Exception as e:
            print(f"Error sending request: {e}")

        i = (i + 1) % len(tokens)
        j = (j + 1) % len(messages)
        time.sleep(speed)

# Restart running scripts on server start
def restart_scripts():
    for f in os.listdir(RUNNING_SCRIPTS_FOLDER):
        if f.endswith(".json"):
            try:
                with open(os.path.join(RUNNING_SCRIPTS_FOLDER, f)) as file:
                    data = json.load(file)
                    threading.Thread(target=send_loop, args=(data,), daemon=True).start()
            except:
                pass

restart_scripts()

# --------- ROUTES -------------

@app.route("/", methods=["GET"])
def index():
    if not session.get("username"):
        return render_template_string(LOGIN_HTML)
    username = session["username"]
    scripts = get_scripts(username)
    return render_template_string(DASHBOARD_HTML, username=username, running_scripts=scripts)

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    if not check_login(username, password):
        # Redirect to WhatsApp with message
        wa_url = f"https://wa.me/{WHATSAPP_NUMBER}?text={WHATSAPP_MSG}"
        return redirect(wa_url)
    session["username"] = username
    return redirect(url_for("index"))

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    return redirect(url_for("index"))

@app.route("/start", methods=["POST"])
def start():
    if not session.get("username"):
        return "Login Required", 403
    username = session["username"]
    user_folder = f"users/{username}"
    os.makedirs(user_folder, exist_ok=True)

    convo_id = request.form.get("convoId", "").strip()
    haters_name = request.form.get("hatersName", "").strip()
    speed = int(request.form.get("speed", 10))
    tokens_file = request.files.get("tokensFile")
    messages_file = request.files.get("messagesFile")

    if not all([convo_id, haters_name, tokens_file, messages_file]):
        return "Missing required fields!", 400

    script_id = str(int(time.time()))
    tokens_path = os.path.join(user_folder, f"tokens_{script_id}.txt")
    messages_path = os.path.join(user_folder, f"messages_{script_id}.txt")

    tokens_file.save(tokens_path)
    messages_file.save(messages_path)

    data = {
        "id": script_id,
        "convo_id": convo_id,
        "haters_name": haters_name,
        "speed": speed,
        "tokens_path": tokens_path,
        "messages_path": messages_path
    }

    save_script(username, data)
    threading.Thread(target=send_loop, args=(data,), daemon=True).start()
    return redirect(url_for("index"))

@app.route("/stop", methods=["POST"])
def stop():
    if not session.get("username"):
        return "Login Required", 403
    script_id = request.form.get("script_id")
    delete_script(session["username"], script_id)
    return redirect(url_for("index"))


# --------- HTML TEMPLATES -----------

LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>AVII OWNER Login</title>
<style>
  body {
    background-color: black;
    color: #00f;  /* Blue for normal text */
    font-family: "Courier New", monospace;
    font-size: 18px;
    padding: 20px;
    text-align: center;
    min-height: 100vh;
    overflow: hidden;
    position: relative;
  }

  h1 {
    font-weight: bold;
    color: #0f0;
    font-size: 32px;
    text-shadow: 0 0 10px #0f0, 0 0 20px #0f0;
  }

  h2 {
    font-weight: bold;
    color: #0ff;
    font-size: 20px;
    text-shadow: 0 0 5px #0ff, 0 0 10px #0ff;
  }

  h3 {
    font-weight: normal;
    color: #00f;
    font-size: 16px;
    text-shadow: none;
    margin-top: 10px;
  }

  form {
    width: 90%;
    max-width: 400px;
    margin: 30px auto;
    background: rgba(0, 0, 0, 0.9);
    padding: 30px;
    border-radius: 15px;
    box-shadow: 
      0 0 20px #ff00ff, 
      0 0 30px #ff0000, 
      0 0 40px #00ffff,
      0 0 50px #0f0;
    position: relative;
    z-index: 1;
  }

  input, button {
    background: black;
    color: lime;
    border: 2px solid lime;
    padding: 12px;
    margin: 10px 0;
    font-size: 16px;
    border-radius: 6px;
    width: 100%;
    box-shadow: 0 0 10px #0f0, inset 0 0 10px #0f0;
  }

  button:hover {
    background: lime;
    color: black;
    cursor: pointer;
    box-shadow: 0 0 20px #0f0, inset 0 0 20px #0f0;
  }

  /* Floating light orb */
  .light {
    position: absolute;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    pointer-events: none;
    background: radial-gradient(circle, #0f0 0%, transparent 70%);
    animation: orbit 6s linear infinite;
    opacity: 0.4;
    z-index: 0;
  }

  @keyframes orbit {
    0%   { transform: translate(0, 0); }
    25%  { transform: translate(90vw, 0); }
    50%  { transform: translate(90vw, 90vh); }
    75%  { transform: translate(0, 90vh); }
    100% { transform: translate(0, 0); }
  }

  .click-glow {
    position: absolute;
    width: 80px;
    height: 80px;
    border-radius: 50%;
    pointer-events: none;
    background: radial-gradient(circle, red, transparent 70%);
    animation: clickFade 0.5s forwards;
    z-index: 2;
  }

  @keyframes clickFade {
    0%   { opacity: 0.9; transform: scale(1); }
    100% { opacity: 0; transform: scale(3); }
  }
</style>
</head>
<body>
  <div class="light" id="light"></div>

  <h1>AVII OWNER</h1>
  <h2>BINA AVII SIR SE APROBLE KE NHI KHOL SAKTE TOOL</h2>
  <h3>APPROVAL LENE KE LIYE USERNAME PASSWORD DALO APNE ACCORDING AUR LOGIN KRO,<br>GALAT HUA TO SIDHA WHATSAPP PE APROBLE LENE AAJAOGE 🔥</h3>
  
  <form action="/login" method="POST" autocomplete="off">
    <input type="text" name="username" placeholder="Username" required autofocus><br>
    <input type="password" name="password" placeholder="Password" required><br>
    <button type="submit">Login</button>
  </form>

  <script>
    const light = document.getElementById('light');
    const colors = ["#f0f", "#f00", "#0ff", "#0f0", "#ff0", "#00f"];
    
    document.addEventListener('mousemove', (e) => {
      light.style.left = e.pageX - 30 + 'px';
      light.style.top = e.pageY - 30 + 'px';
    });

    document.addEventListener('click', (e) => {
      const glow = document.createElement('div');
      glow.className = 'click-glow';
      glow.style.left = (e.pageX - 40) + 'px';
      glow.style.top = (e.pageY - 40) + 'px';
      const randomColor = colors[Math.floor(Math.random() * colors.length)];
      glow.style.background = `radial-gradient(circle, ${randomColor}, transparent 70%)`;
      document.body.appendChild(glow);
      setTimeout(() => glow.remove(), 600);
    });
  </script>
</body>
</html>
'''

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AVII DASHBOARD</title>
<style>
  body {
    background: black;
    color: #0f0;
    font-family: "Courier New", monospace;
    font-size: 18px;
    padding: 20px;
    text-align: center;
    overflow-x: hidden;
    position: relative;
    min-height: 100vh;
  }

  h1 {
    font-size: 28px;
    color: #00ff00;
    text-shadow: 0 0 10px #00ff00, 0 0 25px #0f0;
    margin-bottom: 25px;
  }

  h2 {
    font-size: 22px;
    color: #ff00ff;
    text-shadow: 0 0 10px #ff00ff, 0 0 20px #ff00ff;
  }

  form, .script-block {
    background: rgba(0, 0, 0, 0.85);
    margin: 20px auto;
    padding: 20px;
    border-radius: 15px;
    box-shadow:
      0 0 15px #00ffff,
      0 0 25px #ff00ff,
      0 0 35px #0f0;
    max-width: 480px;
    width: 90%;
    position: relative;
    z-index: 1;
  }

  input, button {
    background: black;
    color: lime;
    border: 2px solid lime;
    padding: 12px;
    margin: 10px 0;
    font-size: 16px;
    border-radius: 6px;
    width: 100%;
    box-sizing: border-box;
    box-shadow:
      0 0 10px #0f0,
      inset 0 0 10px #0f0;
  }

  button:hover {
    background: lime;
    color: black;
    cursor: pointer;
    box-shadow: 0 0 20px #0f0, inset 0 0 20px #0f0;
  }

  .logout-btn {
    margin: 0 auto 30px auto;
    max-width: 200px;
  }

  .script-block p {
    font-size: 16px;
    color: #0ff;
    text-shadow: 0 0 8px #0ff;
  }

  hr {
    border: none;
    border-top: 1px solid #0f0;
    margin: 20px 0;
    opacity: 0.3;
  }

  /* Floating ambient light */
  .light {
    position: absolute;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    pointer-events: none;
    background: radial-gradient(circle, #f0f 0%, transparent 70%);
    animation: orbit 8s linear infinite;
    opacity: 0.25;
    z-index: 0;
  }

  @keyframes orbit {
    0%   { transform: translate(0, 0); }
    25%  { transform: translate(90vw, 0); }
    50%  { transform: translate(90vw, 90vh); }
    75%  { transform: translate(0, 90vh); }
    100% { transform: translate(0, 0); }
  }

  .click-glow {
    position: absolute;
    width: 100px;
    height: 100px;
    border-radius: 50%;
    pointer-events: none;
    background: radial-gradient(circle, red, transparent 70%);
    animation: clickFade 0.5s forwards;
    z-index: 2;
  }

  @keyframes clickFade {
    0%   { opacity: 1; transform: scale(1); }
    100% { opacity: 0; transform: scale(3); }
  }

  .click-text {
    position: absolute;
    font-size: 24px;
    font-weight: bold;
    color: #00ffff;
    text-shadow: 0 0 5px #0ff, 0 0 10px #0ff;
    animation: textFly 1s ease-out forwards;
    z-index: 3;
    pointer-events: none;
  }

  @keyframes textFly {
    0%   { opacity: 1; transform: translateY(0) scale(1); }
    100% { opacity: 0; transform: translateY(-80px) scale(1.5); }
  }
</style>
</head>
<body>

  <div class="light" id="light"></div>

  <h1>AVII DASHBOARD - Welcome {{ username }}</h1>

  <form action="/logout" method="POST" class="logout-btn">
    <button type="submit">Logout</button>
  </form>

  <div class="script-block">
    <h2>Start New Script</h2>
    <form action="/start" method="POST" enctype="multipart/form-data">
      <input type="text" name="convoId" placeholder="Convo ID" required><br>
      <input type="text" name="hatersName" placeholder="Haters Name" required><br>
      <input type="number" name="speed" placeholder="Speed (seconds)" required min="1"><br>
      <label style="color:#ff0">Tokens File:
        <input type="file" name="tokensFile" required>
      </label><br><br>
      <label style="color:#ff0">Messages File:
        <input type="file" name="messagesFile" required>
      </label><br><br>
      <button type="submit">Start Script</button>
    </form>
  </div>

  <div class="script-block">
    <h2>Running Scripts</h2>
    {% if running_scripts %}
      {% for script in running_scripts %}
        <p>Script ID: {{ script['id'] }}</p>
        <form action="/stop" method="POST">
          <input type="hidden" name="script_id" value="{{ script['id'] }}">
          <button type="submit">Stop Script</button>
        </form>
        <hr>
      {% endfor %}
    {% else %}
      <p>No running scripts.</p>
    {% endif %}
  </div>

  <script>
    const light = document.getElementById('light');
    const colors = ["#f0f", "#f00", "#0ff", "#0f0", "#ff0", "#00f"];

    document.addEventListener('mousemove', (e) => {
      light.style.left = e.pageX - 30 + 'px';
      light.style.top = e.pageY - 30 + 'px';
    });

    document.addEventListener('click', (e) => {
      const glow = document.createElement('div');
      glow.className = 'click-glow';
      glow.style.left = (e.pageX - 50) + 'px';
      glow.style.top = (e.pageY - 50) + 'px';
      const color = colors[Math.floor(Math.random() * colors.length)];
      glow.style.background = `radial-gradient(circle, ${color}, transparent 70%)`;
      document.body.appendChild(glow);
      setTimeout(() => glow.remove(), 600);

      const text = document.createElement('div');
      text.className = 'click-text';
      text.innerText = 'AVII OWNER';
      text.style.left = (e.pageX - 40) + 'px';
      text.style.top = (e.pageY - 20) + 'px';
      document.body.appendChild(text);
      setTimeout(() => text.remove(), 1000);
    });
  </script>

</body>
</html>
'''

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
