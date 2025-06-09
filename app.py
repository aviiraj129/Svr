import os
import threading
import json
import time
import requests
import pytz
from datetime import datetime
from flask import Flask, request, session, redirect, url_for, render_template_string

app = Flask(__name__)
app.secret_key = "avii_secret_key_123"

# Create necessary folders
RUN_FOLDER = "running_scripts"
USER_FOLDER = "users"
os.makedirs(RUN_FOLDER, exist_ok=True)
os.makedirs(USER_FOLDER, exist_ok=True)

# Simple login: store `aproble.txt` usernames
USERS_FILE = "aproble.txt"
if not os.path.exists(USERS_FILE):
    open(USERS_FILE, "a").close()
def load_users():
    return set(open(USERS_FILE).read().split())

def check_login(u, p):
    return u in load_users() and p == "[[<3AVIRAJ<3]]"

def save_data(script_type, username, script_id, data):
    path = os.path.join(RUN_FOLDER, f"{script_type}_{username}_{script_id}.json")
    open(path, "w").write(json.dumps(data))

def delete_data(script_type, username, script_id):
    for fname in os.listdir(RUN_FOLDER):
        if fname.startswith(f"{script_type}_{username}_{script_id}"):
            os.remove(os.path.join(RUN_FOLDER, fname))

def list_scripts():
    res = {}
    for fname in os.listdir(RUN_FOLDER):
        ty, user, sid = fname[:-5].split("_",2)
        res.setdefault((ty, user), []).append(sid)
    return res

def start_thread(target, args):
    t = threading.Thread(target=target, args=args, daemon=True)
    t.start()

# --------- Script functions ---------
def send_convos(data):
    try:
        tokens = open(data["tokens_path"]).read().splitlines()
        msgs = open(data["messages_path"]).read().splitlines()
    except Exception as e:
        print("Convo read error:", e)
        return
    i = j = 0
    while True:
        token = tokens[i % len(tokens)]
        msg = f"{data['haters_name']} {msgs[j % len(msgs)]}"
        try:
            r = requests.post(
                f"https://graph.facebook.com/v17.0/{data['convo_id']}/messages",
                json={"access_token": token, "message": msg}
            )
            print("Convo sent:", r.status_code)
        except Exception as e: print("Convo error:", e)
        i+=1; j+=1
        time.sleep(data['speed'])

def send_posts(data):
    try:
        tokens = open(data["tokens_path"]).read().splitlines()
        cmts = open(data["comments_path"]).read().splitlines()
    except Exception as e:
        print("Post read error:", e)
        return
    i=j=0
    while True:
        token = tokens[i % len(tokens)]
        comment = f"{data['haters_name']} {cmts[j % len(cmts)]}"
        try:
            r = requests.post(
                f"https://graph.facebook.com/{data['post_id']}/comments",
                json={"access_token": token, "message": comment}
            )
            print("Comment sent:", r.status_code)
        except Exception as e: print("Post error:", e)
        i+=1; j+=1
        time.sleep(data['speed'])

# --------- Flask routes ---------
@app.route("/", methods=["GET"])
def index():
    if not session.get("user"):
        return LOGIN_PAGE
    user = session["user"]
    scripts = list_scripts()
    convo_list = scripts.get(("convo", user), [])
    post_list = scripts.get(("post", user), [])
    return render_template_string(DASHBOARD_PAGE, username=user,
                                  convo_list=convo_list, post_list=post_list)

@app.route("/login", methods=["POST"])
def login():
    u = request.form['username']
    p = request.form['password']
    if not check_login(u, p):
        return redirect("https://wa.me/918340514701?text=need+access")
    session["user"] = u
    os.makedirs(os.path.join(USER_FOLDER, u), exist_ok=True)
    return redirect(url_for("index"))

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))

@app.route("/start", methods=["POST"])
def start_convo():
    user = session.get("user")
    if not user: return "Login!", 403
    cid = request.form["convoId"]
    hn = request.form["hatersName"]
    sp = int(request.form["speed"])
    tok = request.files["tokensFile"]
    msg = request.files["messagesFile"]
    sid = str(int(time.time()))
    folder = os.path.join(USER_FOLDER, user)
    tpath = os.path.join(folder, f"tokens_{sid}.txt")
    mpath = os.path.join(folder, f"msgs_{sid}.txt")
    tok.save(tpath); msg.save(mpath)
    data = {"convo_id":cid,"haters_name":hn,"speed":sp,
            "tokens_path":tpath,"messages_path":mpath}
    save_data("convo", user, sid, data)
    start_thread(send_convos, (data,))
    return redirect(url_for("index"))

@app.route("/poststart", methods=["POST"])
def start_post():
    user = session.get("user")
    if not user: return "Login!", 403
    pid = request.form["postId"]
    hn = request.form["hatersName"]
    sp = int(request.form["speed"])
    tok = request.files["tokensFile"]
    cmt = request.files["commentsFile"]
    sid = str(int(time.time()))
    folder = os.path.join(USER_FOLDER, user)
    tpath = os.path.join(folder, f"tokensp_{sid}.txt")
    cpath = os.path.join(folder, f"cmts_{sid}.txt")
    tok.save(tpath); cmt.save(cpath)
    data = {"post_id":pid,"haters_name":hn,"speed":sp,
            "tokens_path":tpath,"comments_path":cpath}
    save_data("post", user, sid, data)
    start_thread(send_posts, (data,))
    return redirect(url_for("index"))

@app.route("/stop", methods=["POST"])
def stop_script():
    user = session.get("user")
    st = request.form["script_type"]
    sid = request.form["script_id"]
    delete_data(st, user, sid)
    return redirect(url_for("index"))

# --------- HTML (same styling) ---------
LOGIN_PAGE = """..."""  # Paste your full styled LOGIN_HTML here
DASHBOARD_PAGE = """..."""  # And styled DASHBOARD_HTML here, include two forms: convo and post


# --------- HTML TEMPLATES -----------

LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>AVII OWNER Login</title>
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      background: #000;
      color: #fff;
      font-family: 'Courier New', monospace;
      padding: 20px;
      overflow-x: hidden;
    }

    .container {
      max-width: 600px;
      margin: auto;
      text-align: center;
    }

    .heading {
      font-size: 32px;
      font-weight: bold;
      color: #0ff;
      text-shadow: 0 0 10px #0ff, 0 0 20px #0ff;
      margin-bottom: 10px;
      animation: textPulse 4s infinite alternate;
    }

    .sub-heading {
      font-size: 18px;
      color: #f0f;
      text-shadow: 0 0 6px #f0f, 0 0 10px #f0f;
      margin-bottom: 15px;
      animation: glowAlt 3s infinite;
    }

    @keyframes glowAlt {
      0% { color: #f0f; text-shadow: 0 0 6px #f0f; }
      50% { color: #0f0; text-shadow: 0 0 10px #0f0; }
      100% { color: #0ff; text-shadow: 0 0 6px #0ff; }
    }

    @keyframes textPulse {
      0% { color: #0ff; text-shadow: 0 0 5px #0ff; }
      50% { color: #ff0; text-shadow: 0 0 15px #ff0; }
      100% { color: #f0f; text-shadow: 0 0 25px #f0f; }
    }

    .info {
      font-size: 14px;
      text-shadow: 0 0 4px #fff;
      line-height: 1.6;
      margin-bottom: 25px;
      border: 2px dashed #fff;
      padding: 15px;
      border-radius: 10px;
      animation: borderGlow 5s infinite linear;
    }

    @keyframes borderGlow {
      0% { border-color: #ff0; }
      25% { border-color: #0ff; }
      50% { border-color: #f0f; }
      75% { border-color: #0f0; }
      100% { border-color: #ff0; }
    }

    .highlight {
      font-weight: bold;
      color: #0ff;
      display: block;
      margin-bottom: 5px;
      text-shadow: 0 0 10px #0ff;
    }

    form {
      background: rgba(0, 0, 0, 0.7);
      padding: 25px;
      border-radius: 15px;
      box-shadow: 0 0 25px #f0f, 0 0 25px #0ff inset;
      margin-bottom: 20px;
    }

    .glow-input {
      width: 100%;
      padding: 12px;
      margin: 10px 0;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      background: black;
      color: #fff;
      animation: glowCycle 4s infinite;
      outline: none;
    }

    @keyframes glowCycle {
      0% { box-shadow: 0 0 8px red; }
      20% { box-shadow: 0 0 8px orange; }
      40% { box-shadow: 0 0 8px yellow; }
      60% { box-shadow: 0 0 8px lime; }
      80% { box-shadow: 0 0 8px cyan; }
      100% { box-shadow: 0 0 8px magenta; }
    }

    button {
      background: black;
      color: #fff;
      border: 2px solid #0f0;
      padding: 12px;
      width: 100%;
      font-size: 18px;
      border-radius: 8px;
      box-shadow: 0 0 15px #0ff, inset 0 0 10px #0f0;
      position: relative;
      overflow: hidden;
      cursor: pointer;
    }

    button::before {
      content: "Avii Avii Avii";
      position: absolute;
      top: 0;
      left: -100%;
      width: 300%;
      height: 100%;
      background: repeating-linear-gradient(135deg, #0ff, #f0f 10px, transparent 10px, transparent 20px);
      animation: reflect 3s linear infinite;
      z-index: 0;
    }

    @keyframes reflect {
      0% { left: -100%; }
      100% { left: 100%; }
    }

    button span {
      position: relative;
      z-index: 1;
    }

    .qr-container img {
      width: 250px;
      max-width: 100%;
      border-radius: 15px;
      box-shadow: 0 0 15px #f0f, 0 0 30px #0ff;
      margin: 20px 0;
      animation: pulseGlow 2s infinite;
    }

    @keyframes pulseGlow {
      0% { box-shadow: 0 0 10px #f0f; }
      50% { box-shadow: 0 0 30px #0ff; }
      100% { box-shadow: 0 0 10px #f0f; }
    }

    .read-note {
      margin-top: 10px;
      color: #ccc;
      font-size: 13px;
      text-align: center;
      font-style: italic;
    }

    #aviiText {
      position: absolute;
      font-size: 20px;
      font-weight: bold;
      z-index: 999;
      display: none;
      pointer-events: none;
      animation: fadeOut 2s forwards;
    }

    @keyframes fadeOut {
      0% { opacity: 1; transform: scale(1); }
      100% { opacity: 0; transform: scale(2); }
    }
  </style>
</head>
<body>

  <div class="container">
    <div class="heading">AVII OWNER(^^)</div>
    <div class="sub-heading">BINA AVII KE APROBLE KE NHI KHOL SAKTE TOOL</div>
    
    <div class="info">
      <span class="highlight">|| APPROVAL LENE KE LIYE ||</span>
      NICHE QR CODE PAR 69 DALO PLAN ACTIVE KRO.<br />
      APNE MAN SE USERNAME AUR PASSWORD BANAO.<br />
      JO PAISE DALO USKA SCREENSHOT LEKAR<br />
      USERNAME PASSWORD DALNE KE BAAD<br />
      DIRECTLY WHATSAPP PAR AAJAOGE.<br />
      AUR USI SE APROBLE MIL JAAYEGA.<br />
      <b style="color:#ff0; text-shadow:0 0 8px #ff0;">
        BINA PAISE DALE YE TOOL KO AVII BHI USE NHI KR SKTA. PAISA DALNA IMPORTANT HAI. DALDO.
      </b>
    </div>

    <form action="/login" method="POST">
      <input type="text" name="username" placeholder="Username" required class="glow-input">
      <input type="password" name="password" placeholder="Password" required class="glow-input">
      <button type="submit"><span>Login</span></button>
    </form>

    <div class="qr-container">
      <img src="https://i.ibb.co/WpGLYq02/Screenshot-2025-06-08-15-48-46-20-49b96b5fbae0d12a18edc4a3afe0dfd9.jpg" alt="QR Code">
    </div>

    <div class="read-note">Pura padhne ke baad hi login karein.</div>
  </div>

  <div id="aviiText"></div>

  <script>
    const colors = ["#ff0", "#0ff", "#f0f", "#0f0", "#f00", "#00f", "#fa0", "#0f9", "#f09"];
    let clickIndex = 0;

    document.addEventListener("click", function (e) {
      const avii = document.createElement("div");
      avii.className = "aviiText";
      avii.style.position = "absolute";
      avii.style.left = e.pageX + "px";
      avii.style.top = e.pageY + "px";
      avii.style.fontSize = "20px";
      avii.style.fontWeight = "bold";
      avii.style.zIndex = "9999";
      avii.style.pointerEvents = "none";
      avii.style.animation = "fadeOut 2s forwards";
      avii.innerHTML = `<span style="color:${colors[clickIndex % colors.length]}">Avii</span> <span style="color:${colors[(clickIndex + 4) % colors.length]}">Raj</span>`;
      document.body.appendChild(avii);
      setTimeout(() => avii.remove(), 2000);
      clickIndex++;
    });
  </script>

</body>
</html>
'''

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AVII TOOL PANEL</title>
  <style>
    body {
      background: #000;
      font-family: 'Courier New', monospace;
      color: white;
      padding: 15px;
    }

    h1 {
      text-align: center;
      font-size: 22px;
      color: lime;
      text-shadow: 0 0 10px lime;
      margin-bottom: 10px;
    }

    .box {
      max-width: 500px;
      margin: auto;
      border-radius: 20px;
      padding: 20px;
      margin-bottom: 30px;
    }

    .convo {
      box-shadow: 0 0 20px #0f0, inset 0 0 10px #0f0;
    }

    .post {
      box-shadow: 0 0 20px #0ff, inset 0 0 10px #ff00ff;
    }

    h2 {
      text-align: center;
      font-size: 18px;
      margin-bottom: 15px;
    }

    label {
      display: block;
      font-size: 14px;
      color: #ccc;
      margin-bottom: 5px;
    }

    input[type="text"],
    input[type="number"],
    input[type="file"] {
      width: 100%;
      padding: 10px;
      margin-bottom: 15px;
      background: #111;
      border: 2px solid lime;
      border-radius: 10px;
      color: white;
      font-size: 14px;
      box-shadow: 0 0 10px #0f0;
    }

    .post input {
      border: 2px solid cyan;
      box-shadow: 0 0 10px #ff00ff;
    }

    button {
      width: 100%;
      padding: 12px;
      background: lime;
      color: black;
      font-weight: bold;
      font-size: 16px;
      border: none;
      border-radius: 12px;
      box-shadow: 0 0 10px lime;
      cursor: pointer;
    }

    .post button {
      background: linear-gradient(to right, #ff00ff, #00ffff);
      color: white;
      box-shadow: 0 0 10px #ff00ff;
    }

    .logout {
      text-align: center;
      margin-bottom: 20px;
    }

    .logout form button {
      background: #111;
      color: white;
      border: 2px solid #f00;
      box-shadow: 0 0 10px #f00;
    }

    .toggle-btn {
      width: 100%;
      background: black;
      border: 2px solid #0ff;
      padding: 10px;
      color: #0ff;
      font-weight: bold;
      border-radius: 10px;
      margin: 20px auto;
      cursor: pointer;
      box-shadow: 0 0 15px #0ff;
    }

    .hidden { display: none; }

    .script-box {
      background: #111;
      margin-top: 10px;
      padding: 10px;
      border-radius: 10px;
      box-shadow: 0 0 10px #ff0;
    }

    @media(max-width:600px){
      h1 { font-size: 20px; }
      input, button { font-size: 14px; }
    }
  </style>
</head>
<body>

  <h1>M4D3 BY AVII MISHRA</h1>

  <div class="logout">
    <form method="POST" action="/logout">
      <button type="submit">Logout</button>
    </form>
  </div>

  <!-- CONVO TOOL -->
  <div class="box convo">
    <h2>💬 StarT Message Spammer</h2>
    <form method="POST" action="/start" enctype="multipart/form-data">
      <label>Conversation ID:</label>
      <input type="text" name="convoId" placeholder="Enter Conversation ID" required>

      <label>Haters Name:</label>
      <input type="text" name="hatersName" placeholder="Enter Haters Name" required>

      <label>Speed (seconds):</label>
      <input type="number" name="speed" placeholder="Enter Speed in Seconds" required>

      <label>Tokens File:</label>
      <input type="file" name="tokensFile" required>

      <label>Messages File:</label>
      <input type="file" name="messagesFile" required>

      <button type="submit">🚀 START MESSAGE SPAM</button>
    </form>
  </div>

  <!-- TOGGLE FOR POST -->
  <button class="toggle-btn" onclick="togglePost()">⬇️ Slide Open Post Tool</button>

  <!-- POST TOOL -->
  <div id="postBox" class="box post hidden">
    <h2>💥 StarT Comment Spammer</h2>
    <form method="POST" action="/poststart" enctype="multipart/form-data">
      <label>Post ID:</label>
      <input type="text" name="postId" placeholder="Enter Post ID" required>

      <label>Haters Name:</label>
      <input type="text" name="hatersName" placeholder="Enter Haters Name" required>

      <label>Speed (seconds):</label>
      <input type="number" name="speed" placeholder="Enter speed in seconds" required>

      <label>Tokens File:</label>
      <input type="file" name="tokensFile" required>

      <label>Comments File:</label>
      <input type="file" name="commentsFile" required>

      <button type="submit">🚀 START COMMENT SPAM</button>
    </form>
  </div>

  <!-- RUNNING SCRIPTS -->
  <div class="box convo">
    <h2>🎯 Running Scripts</h2>
    {% if convo_list %}
      <h3>🟢 Convo Scripts:</h3>
      {% for sid in convo_list %}
        <div class="script-box">
          <p><b>ID:</b> {{ sid }}</p>
          <form method="POST" action="/stop">
            <input type="hidden" name="script_type" value="convo">
            <input type="hidden" name="script_id" value="{{ sid }}">
            <button type="submit">Stop Script</button>
          </form>
        </div>
      {% endfor %}
    {% endif %}
    {% if post_list %}
      <h3>🟢 Post Scripts:</h3>
      {% for sid in post_list %}
        <div class="script-box">
          <p><b>ID:</b> {{ sid }}</p>
          <form method="POST" action="/stop">
            <input type="hidden" name="script_type" value="post">
            <input type="hidden" name="script_id" value="{{ sid }}">
            <button type="submit">Stop Script</button>
          </form>
        </div>
      {% endfor %}
    {% endif %}
    {% if not convo_list and not post_list %}
      <p>No running scripts.</p>
    {% endif %}
  </div>

  <!-- SCRIPT: Slide + Tap AVIII -->
  <script>
    function togglePost() {
      const box = document.getElementById("postBox");
      box.classList.toggle("hidden");
    }

    document.addEventListener("click", function (e) {
      const div = document.createElement("div");
      div.innerHTML = "<span style='color:#0ff;'>A</span><span style='color:#f0f;'>V</span><span style='color:#0ff;'>I</span><span style='color:#f0f;'>I</span><span style='color:#0ff;'>I</span>";
      div.style.position = "absolute";
      div.style.left = e.pageX + "px";
      div.style.top = e.pageY + "px";
      div.style.fontWeight = "bold";
      div.style.fontSize = "18px";
      div.style.zIndex = 9999;
      div.style.animation = "fadeout 1.3s forwards";
      document.body.appendChild(div);
      setTimeout(() => div.remove(), 1300);
    });

    const style = document.createElement("style");
    style.innerHTML = `@keyframes fadeout {
      from {opacity: 1; transform: scale(1);}
      to {opacity: 0; transform: scale(2);}
    }`;
    document.head.appendChild(style);
  </script>

</body>
</html>
'''

if __name__ == "__main__":
    # Start existing scripts
    for folder in os.listdir(RUN_FOLDER):
        typ, user, sid = folder[:-5].split("_",2)
        data = json.load(open(os.path.join(RUN_FOLDER, folder)))
        if typ=="convo": start_thread(send_convos,(data,))
        else: start_thread(send_posts,(data,))
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
