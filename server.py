"""
server.py — Flask local dev server
Serves public/index.html and handles POST /api/contact via Brevo.

Run:
    pip install flask python-dotenv requests
    python server.py
"""

import os
import re
import requests
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

# ── Load .env
load_dotenv()

app = Flask(__name__, static_folder="public")

# ── Config — change TO_EMAIL if needed
TO_EMAIL = "mayoukhmodak.01@gmail.com"
TO_NAME  = "Mayoukh Modak"


# ─────────────────────────────────────────
#  Static files  →  serve public/ folder
# ─────────────────────────────────────────
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_static(path):
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


# ─────────────────────────────────────────
#  POST /api/contact  →  send via Brevo
# ─────────────────────────────────────────
@app.route("/api/contact", methods=["POST", "OPTIONS"])
def contact():
    # Handle CORS preflight
    if request.method == "OPTIONS":
        return _cors("", 204)

    data = request.get_json(silent=True) or {}

    name    = (data.get("name")    or "").strip()
    email   = (data.get("email")   or "").strip()
    message = (data.get("message") or "").strip()

    # ── Validate
    if not name or not email or not message:
        return _cors(jsonify(error="All fields are required."), 400)

    if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
        return _cors(jsonify(error="Invalid email address."), 400)

    if len(message) > 5000:
        return _cors(jsonify(error="Message too long (max 5000 chars)."), 400)

    # ── Read secrets from .env
    api_key    = os.getenv("BREVO_API_KEY")
    from_email = os.getenv("BREVO_FROM")

    if not api_key or not from_email:
        app.logger.error("Missing BREVO_API_KEY or BREVO_FROM in .env")
        return _cors(jsonify(error="Server misconfiguration — check .env file."), 500)

    # ── Build Brevo payload
    payload = {
        "sender":      {"name": "Portfolio Contact Form", "email": from_email},
        "to":          [{"email": TO_EMAIL, "name": TO_NAME}],
        "replyTo":     {"email": email, "name": name},
        "subject":     f"[Portfolio] New message from {name}",
        "htmlContent": f"""
        <div style="font-family:monospace;background:#0b0c0e;color:#e8e6de;
                    padding:2rem;border-left:3px solid #f5a623;max-width:600px">
            <p style="color:#f5a623;font-size:11px;letter-spacing:3px;margin:0 0 1.5rem">
                PORTFOLIO CONTACT FORM
            </p>
            <table style="width:100%;border-collapse:collapse;margin-bottom:1.5rem">
                <tr>
                    <td style="color:#6a6660;font-size:11px;padding:.5rem 0;width:70px">FROM</td>
                    <td style="color:#e8e6de;font-size:13px">{_esc(name)}</td>
                </tr>
                <tr>
                    <td style="color:#6a6660;font-size:11px;padding:.5rem 0">REPLY TO</td>
                    <td>
                        <a href="mailto:{_esc(email)}"
                           style="color:#f5a623;text-decoration:none;font-size:13px">
                            {_esc(email)}
                        </a>
                    </td>
                </tr>
            </table>
            <hr style="border:none;border-top:1px solid #2a2d35;margin:0 0 1.5rem"/>
            <p style="color:#6a6660;font-size:11px;letter-spacing:2px;margin:0 0 .6rem">MESSAGE</p>
            <p style="color:#e8e6de;font-size:13px;line-height:1.9;
                      white-space:pre-wrap;margin:0">{_esc(message)}</p>
        </div>
        """,
    }

    # ── Call Brevo
    try:
        resp = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            json=payload,
            headers={
                "api-key":      api_key,
                "Content-Type": "application/json",
            },
            timeout=10,
        )

        if resp.ok:
            app.logger.info(f"✉  Email sent — from: {name} <{email}>")
            return _cors(jsonify(ok=True), 200)
        else:
            err = resp.json().get("message", f"Brevo returned {resp.status_code}")
            app.logger.error(f"Brevo error: {err}")
            return _cors(jsonify(error=err), 502)

    except requests.exceptions.Timeout:
        return _cors(jsonify(error="Mail service timed out. Try again."), 504)
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Request to Brevo failed: {e}")
        return _cors(jsonify(error="Could not reach mail service."), 500)


# ─────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────
def _esc(text):
    """Escape HTML special characters."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _cors(body, status):
    """Attach CORS headers for local dev."""
    if isinstance(body, str):
        resp = app.make_response((body, status))
    else:
        resp = app.make_response((body, status))
    resp.headers["Access-Control-Allow-Origin"]  = "*"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


# ─────────────────────────────────────────
#  Start
# ─────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))

    print("")
    print("  ┌─────────────────────────────────────────┐")
    print(f"  │  🟢  Flask server running                │")
    print(f"  │      http://localhost:{port}               │")
    print("  │                                         │")
    print("  │  POST /api/contact  →  Brevo email      │")
    print("  │  GET  /             →  portfolio         │")
    print("  │                                         │")
    print("  │  Ctrl+C to stop                         │")
    print("  └─────────────────────────────────────────┘")
    print("")

    app.run(host="0.0.0.0", port=port, debug=True)
