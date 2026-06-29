#!/data/data/com.termux/files/usr/bin/bash
set -e

BASE="${1:-http://127.0.0.1:8080}"

echo "Testing Mraprguild Termux Website Firewall"
echo "Target: $BASE"
echo ""

test_case() {
  NAME="$1"
  URL="$2"
  EXPECT="$3"

  CODE=$(curl -s -o /tmp/waf_test_body.txt -w "%{http_code}" "$URL" || true)
  BODY=$(cat /tmp/waf_test_body.txt | head -c 160)

  if [ "$CODE" = "$EXPECT" ]; then
    echo "✅ $NAME -> HTTP $CODE"
  else
    echo "❌ $NAME -> HTTP $CODE expected $EXPECT"
    echo "$BODY"
  fi
}

test_case "Clean homepage" "$BASE/" "200"
test_case "SQL injection blocked" "$BASE/?id=1%20union%20select%20password%20from%20users" "403"
test_case "XSS blocked" "$BASE/?q=%3Cscript%3Ealert(1)%3C/script%3E" "403"
test_case "Sensitive file blocked" "$BASE/.env" "403"
test_case "Path traversal blocked" "$BASE/download?file=../../etc/passwd" "403"

echo ""
echo "Done. Check logs:"
echo "tail -f logs/blocked.log"
