#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "======================================"
echo " Mraprguild Termux Website Firewall"
echo "======================================"

pkg update -y
pkg upgrade -y
pkg install -y python git nano

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if [ ! -f config.yml ]; then
  cp config.example.yml config.yml
fi

mkdir -p logs rules
touch logs/blocked.log rules/blocked_ips.txt rules/allowed_ips.txt rules/bad_bots.txt

chmod +x start.sh demo_backend.sh

echo ""
echo "Install complete."
echo "Edit config: nano config.yml"
echo "Start: bash start.sh"
