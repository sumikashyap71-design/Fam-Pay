from http.server import BaseHTTPRequestHandler
import urllib.parse
import json
import imaplib
import email
import re
from datetime import datetime, timedelta

# ================= CONFIG =================
GMAIL_USER = "sumiikashyap16@gmail.com"
GMAIL_PASS = "amwd iint zotw usvo"
MY_API_KEY = "FAMAPPAPI"
# ==========================================

def check_fampay(amount, utr_input):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select('"[Gmail]/All Mail"')
        date = (datetime.now() - timedelta(days=2)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, f'(SINCE "{date}")')

        if status != "OK" or not messages[0]:
            return False, "No recent emails found"

        for num in reversed(messages[0].split()):
            status, data = mail.fetch(num, "(RFC822)")
            if status != "OK": continue

            msg = email.message_from_bytes(data[0][1])
            subject = str(msg.get("Subject", "")).lower()

            if "famapp" in subject or "received" in subject or "payment" in subject:
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body += part.get_payload(decode=True).decode(errors="ignore") + "\n"
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")

                amount_str = str(amount)
                amount_pattern = rf'(?:₹|Rs\.?|INR)?\s*{re.escape(amount_str)}\b'

                if re.search(amount_pattern, body, re.IGNORECASE):
                    if utr_input in body:
                        mail.logout()
                        return True, "Payment verified"
        mail.logout()
        return False, "Payment not found or UTR mismatch"
    except Exception as e:
        return False, str(e)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # URL Parse karo
        parsed_path = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed_path.query)

        if parsed_path.path != '/api':
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Use /api route"}).encode())
            return

        api_key = query.get('api_key', [None])[0]
        utr = query.get('utr', [None])[0]
        amount = query.get('amount', [None])[0]

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        if api_key != MY_API_KEY:
            self.wfile.write(json.dumps({"status": "error", "message": "Invalid API Key"}).encode())
            return

        if not utr or not amount:
            self.wfile.write(json.dumps({"status": "error", "message": "UTR and Amount required"}).encode())
            return

        success, message = check_fampay(float(amount), utr)

        if success:
            self.wfile.write(json.dumps({
                "status": "success",
                "message": "Payment verified",
                "utr": utr,
                "amount": amount
            }).encode())
        else:
            self.wfile.write(json.dumps({
                "status": "error",
                "message": message
            }).encode())
