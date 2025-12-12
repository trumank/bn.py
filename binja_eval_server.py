#!/usr/bin/env python3
"""Binary Ninja Python Eval HTTP Server.

Can be used as:
  1. Binary Ninja plugin: Copy to plugins folder, use Plugins menu
  2. Headless server: python binja_eval_server.py <binary> [--port PORT]
"""
import sys
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

SERVER_PORT = 31337
_server_instance = None
_server_thread = None
_bv = None
_headless = False


def _log(msg):
    """Log message to appropriate output."""
    if _headless:
        print(msg)
    else:
        from binaryninja import log_info
        log_info(msg)


def _log_error(msg):
    """Log error to appropriate output."""
    if _headless:
        print(msg, file=sys.stderr)
    else:
        from binaryninja import log_error
        log_error(msg)


class EvalHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        _log(f"[EvalServer] {args[0]}")

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

        import binaryninja
        exec_globals = {"bv": _bv, "binaryninja": binaryninja}

        try:
            result = eval(code, exec_globals)
            response = {"success": True, "result": repr(result)}
        except SyntaxError:
            try:
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
            response = {
                "status": "ok",
                "binary": _bv.file.filename if _bv else None,
                "functions": len(list(_bv.functions)) if _bv else 0,
            }
            self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
            self.send_error(404, "Not Found")


def start_server(bv, port=SERVER_PORT):
    """Start the eval server with given BinaryView."""
    global _server_instance, _server_thread, _bv

    _bv = bv
    if _server_instance is not None:
        _log(f"[EvalServer] Server already running on port {port}")
        return

    try:
        _server_instance = HTTPServer(("127.0.0.1", port), EvalHandler)
        _server_thread = threading.Thread(target=_server_instance.serve_forever, daemon=True)
        _server_thread.start()
        _log(f"[EvalServer] Started on http://127.0.0.1:{port}")
        _log("[EvalServer] POST /eval with JSON {\"code\": \"<python>\"} to evaluate")
    except Exception as e:
        _log_error(f"[EvalServer] Failed to start: {e}")
        _server_instance = None


def stop_server(bv=None):
    """Stop the eval server."""
    global _server_instance, _server_thread

    if _server_instance is None:
        _log("[EvalServer] Server not running")
        return

    _server_instance.shutdown()
    _server_instance = None
    _server_thread = None
    _log("[EvalServer] Server stopped")


def _run_headless():
    """Run as standalone headless server."""
    global _headless
    _headless = True

    import argparse
    import binaryninja

    parser = argparse.ArgumentParser(description="Headless Binary Ninja eval server")
    parser.add_argument("binary", help="Path to binary file to analyze")
    parser.add_argument("-p", "--port", type=int, default=SERVER_PORT, help="Server port")
    parser.add_argument("--no-wait", action="store_true", help="Don't wait for full analysis")
    args = parser.parse_args()

    print(f"[*] Loading {args.binary}...")
    bv = binaryninja.load(args.binary)

    if bv is None:
        print(f"[!] Failed to load binary: {args.binary}", file=sys.stderr)
        sys.exit(1)

    if not args.no_wait:
        print("[*] Waiting for analysis to complete...")
        bv.update_analysis_and_wait()

    print(f"[+] Analysis complete: {len(list(bv.functions))} functions found")

    start_server(bv, args.port)
    print("[*] Press Ctrl+C to stop")

    try:
        _server_thread.join()
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
        stop_server()


# Plugin registration (only when loaded as plugin, not as script)
if __name__ != "__main__":
    from binaryninja import PluginCommand

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
else:
    _run_headless()
