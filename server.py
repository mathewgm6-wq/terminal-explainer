"""
Terminal-to-English MCP Server  (Gemini Edition)
-------------------------------------------------
SETUP:
  1. Get a free key: https://aistudio.google.com/app/apikey
  2. Git-Bash:   export GEMINI_API_KEY='your-key'
     PowerShell: $env:GEMINI_API_KEY='your-key'
  3. Run: python server.py
  4. In a NEW terminal, add hook.sh to ~/.bashrc
"""

import json, os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.request, urllib.error

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL   = "gemini-2.0-flash"
SERVER_PORT    = 7891
HISTORY_FILE   = os.path.join(os.path.expanduser("~"), ".terminal_error_history.json")

BANNER = """
+==========================================================+
|   Terminal-to-English       Powered by Gemini            |
|   Monitoring errors on  http://127.0.0.1:7891            |
|   Press Ctrl+C to stop                                   |
+==========================================================+
"""

def ask_gemini(command, error_output, exit_code):
    if not GEMINI_API_KEY:
        return (
            "GEMINI_API_KEY not set.\n"
            "  Git-Bash : export GEMINI_API_KEY='your-key'\n"
            "  PowerShell: $env:GEMINI_API_KEY='your-key'\n"
            "Get a free key: https://aistudio.google.com/app/apikey"
        )

    prompt = (
        "A terminal command just failed on Windows (Git-Bash or VS Code terminal).\n"
        "Explain in plain English and give a clear numbered fix.\n\n"
        "Command:\n" + command + "\n\n"
        "Exit code: " + str(exit_code) + "\n\n"
        "Error output:\n" + error_output + "\n\n"
        "Reply in EXACTLY this format:\n\n"
        "## What Happened\n"
        "(2-3 plain-English sentences)\n\n"
        "## How to Fix It\n"
        "(numbered steps with ```bash code blocks```)\n\n"
        "## Pro Tip\n"
        "(one short tip to prevent this in future)"
    )

    url  = ("https://generativelanguage.googleapis.com/v1beta/models/"
            + GEMINI_MODEL + ":generateContent?key=" + GEMINI_API_KEY)
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
    req  = urllib.request.Request(url, data=body,
               headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        return "Gemini API error " + str(e.code) + ": " + e.read().decode()
    except Exception as e:
        return "Request failed: " + str(e)


def save_history(entry):
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            history = json.load(open(HISTORY_FILE))
        except Exception:
            pass
    history.append(entry)
    json.dump(history[-100:], open(HISTORY_FILE, "w"), indent=2)


def load_history():
    try:
        return json.load(open(HISTORY_FILE))
    except Exception:
        return []


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _json(self, code, data):
        body = json.dumps(data, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"status": "ok", "model": GEMINI_MODEL})
        elif self.path == "/history":
            self._json(200, {"history": load_history()})
        else:
            self._json(200, {"endpoints": ["POST /explain","GET /history","GET /health"]})

    def do_POST(self):
        if self.path != "/explain":
            self._json(404, {"error": "not found"}); return
        try:
            n       = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(n))
        except Exception:
            self._json(400, {"error": "bad JSON"}); return

        cmd      = payload.get("command", "unknown")
        err      = payload.get("error", "")
        exitcode = int(payload.get("exit_code", 1))
        sep      = "=" * 60

        print("\n" + sep)
        print("  FAILED : " + cmd)
        print("  CODE   : " + str(exitcode))
        print("  Asking Gemini ...", flush=True)

        print("  Error received: " + repr(err[:100]), flush=True)
        print("  Asking Gemini ...", flush=True)

        explanation = ask_gemini(cmd, err, exitcode)

        print("\n" + explanation + "\n" + sep + "\n", flush=True)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": cmd, "exit_code": exitcode,
            "error": err, "explanation": explanation
        }
        save_history(entry)
        self._json(200, {"explanation": explanation, "timestamp": entry["timestamp"]})
#hello

if __name__ == "__main__":
    print(BANNER)
    if not GEMINI_API_KEY:
        print("  WARNING: GEMINI_API_KEY not set.")
        print("  Get a free key: https://aistudio.google.com/app/apikey\n")
    srv = HTTPServer(("127.0.0.1", SERVER_PORT), Handler)
    print("  Listening on http://127.0.0.1:" + str(SERVER_PORT))
    print("  History  -> " + HISTORY_FILE + "\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")