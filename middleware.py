"""Minimal HTTP-to-ChatScript TCP bridge using only the standard library."""

import json
import os
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler

CS_HOST = os.environ.get("CS_HOST", "chatscript")
CS_PORT = int(os.environ.get("CS_PORT", "1024"))
PORT = int(os.environ.get("PORT", "8000"))


def query_chatscript(user: str, message: str) -> str:
    """Send a message to ChatScript over TCP and return the reply."""
    frame = f"{user}\0bot\0{message}\0"
    with socket.create_connection((CS_HOST, CS_PORT), timeout=5) as sock:
        sock.sendall(frame.encode("utf-8"))
        data = sock.recv(4096)
    return data.decode("utf-8").strip("\x00").strip()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/chat":
            self._respond(404, {"error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            user = body["user"]
            message = body["message"]
        except (json.JSONDecodeError, KeyError, ValueError):
            self._respond(400, {"error": "expected JSON with 'user' and 'message'"})
            return
        try:
            reply = query_chatscript(user, message)
        except (socket.error, OSError) as exc:
            self._respond(502, {"error": f"chatscript unavailable: {exc}"})
            return
        self._respond(200, {"reply": reply})

    def _respond(self, code: int, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[middleware] {args[0]} {args[1]} {args[2]}")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[middleware] listening on port {PORT}, forwarding to {CS_HOST}:{CS_PORT}")
    server.serve_forever()
