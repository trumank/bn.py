# Binary Ninja Plugin: Python Eval HTTP Server
# Save this file to your Binary Ninja plugins folder

from binaryninja import PluginCommand, log_info, log_error
import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

SERVER_PORT = 31337
_server_instance = None
_server_thread = None
_bv = None


class EvalHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        log_info(f"[EvalServer] {args[0]}")

    def do_POST(self):
        if self.path != "/eval":
            self.send_error(404, "Not Found")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")

        try:
            data = json.loads(body)
            code = data.get("code", "")
        except json.JSONDecodeError:
            code = body

        try:
            result = eval(code, {"bv": _bv})
            response = {"success": True, "result": repr(result)}
        except SyntaxError:
            try:
                exec_globals = {"bv": _bv}
                exec(code, exec_globals)
                result = exec_globals.get("result", None)
                response = {"success": True, "result": repr(result)}
            except Exception as e:
                response = {"success": False, "error": str(e)}
        except Exception as e:
            response = {"success": False, "error": str(e)}

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(response).encode("utf-8"))

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))
        else:
            self.send_error(404, "Not Found")


def start_server(bv):
    global _server_instance, _server_thread, _bv

    _bv = bv
    if _server_instance is not None:
        log_info(f"[EvalServer] Server already running on port {SERVER_PORT}")
        return

    try:
        _server_instance = HTTPServer(("127.0.0.1", SERVER_PORT), EvalHandler)
        _server_thread = threading.Thread(target=_server_instance.serve_forever, daemon=True)
        _server_thread.start()
        log_info(f"[EvalServer] Started on http://127.0.0.1:{SERVER_PORT}")
        log_info(f"[EvalServer] POST /eval with JSON {{\"code\": \"<python>\"}} to evaluate")
    except Exception as e:
        log_error(f"[EvalServer] Failed to start: {e}")
        _server_instance = None


def stop_server(bv):
    global _server_instance, _server_thread

    if _server_instance is None:
        log_info("[EvalServer] Server not running")
        return

    _server_instance.shutdown()
    _server_instance = None
    _server_thread = None
    log_info("[EvalServer] Server stopped")


PluginCommand.register(
    "Eval Server\\Start Server",
    "Start the Python eval HTTP server",
    start_server
)

PluginCommand.register(
    "Eval Server\\Stop Server",
    "Stop the Python eval HTTP server",
    stop_server
)
