<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>AVII OWNER Login</title>
<style>
  body {
    background: black;
    color: lime;
    font-family: "Courier New", monospace;
    font-size: 24px;
    padding: 40px;
    text-align: center;
  }
  h1, h2, h3 {
    font-weight: bold;
    text-shadow:
      0 0 5px #0f0,
      0 0 10px #0f0,
      0 0 20px #0f0,
      0 0 40px #0f0;
  }
  form {
    margin-top: 30px;
  }
  input, button {
    background: black;
    color: lime;
    border: 2px solid lime;
    padding: 12px 20px;
    margin: 10px 0;
    font-size: 20px;
    border-radius: 6px;
    box-shadow:
      0 0 10px #0f0,
      inset 0 0 10px #0f0;
  }
  button:hover {
    background: lime;
    color: black;
    cursor: pointer;
    box-shadow:
      0 0 20px #0f0,
      inset 0 0 20px #0f0;
  }
</style>
</head>
<body>
  <h1>AVII OWNER</h1>
  <h2>BINA AVII SIR SE APROBLE KE NHI KHOL SAKTE TOOL</h2>
  <h3>KUCHH BHI USER NAME PASSWORD DALO AND CONTINUE TO WP CHAT KRKE BHEJ DO DONE KR DI JAYEGI APROBLE</h3>
  <form action="/login" method="POST" autocomplete="off">
    <input type="text" name="username" placeholder="Username" required autofocus><br>
    <input type="password" name="password" placeholder="Password" required><br>
    <button type="submit">Login</button>
  </form>
</body>
</html>
