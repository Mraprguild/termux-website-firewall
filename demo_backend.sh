#!/data/data/com.termux/files/usr/bin/bash
set -e
mkdir -p demo_site
cat > demo_site/index.html <<'HTML'
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Mraprguild Protected Website</title>
  <style>
    body{font-family:Arial;background:#0b1020;color:white;text-align:center;padding:50px}
    .card{max-width:700px;margin:auto;background:#151b33;border-radius:20px;padding:30px;box-shadow:0 20px 60px #0008}
    h1{color:#ff3040}
  </style>
</head>
<body>
  <div class="card">
    <h1>Protected by Mraprguild Termux Website Firewall</h1>
    <p>Your demo backend is working.</p>
  </div>
</body>
</html>
HTML
cd demo_site
python -m http.server 8000
