#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "GitHub project setup"
echo "1) Create repo on GitHub: termux-website-firewall"
echo "2) Then run these commands:"
echo ""
echo "git init"
echo "git add ."
echo "git commit -m 'Initial Mraprguild Termux Website Firewall project'"
echo "git branch -M main"
echo "git remote add origin https://github.com/Mraprguild/termux-website-firewall.git"
echo "git push -u origin main"
echo ""
echo "Single command install after upload:"
echo "pkg update -y && pkg upgrade -y && pkg install -y git python unzip nano && git clone https://github.com/Mraprguild/termux-website-firewall.git && cd termux-website-firewall && bash install.sh"
