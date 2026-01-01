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
_servers = {}  # bv -> (server_instance, server_thread, port)
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


def _eval_code(code, globals_dict):
    """Evaluate code like a REPL - return last expression's value."""
    import ast

    try:
        tree = ast.parse(code)
    except SyntaxError:
        raise

    if not tree.body:
        return None

    # If last statement is an expression, eval it separately
    if isinstance(tree.body[-1], ast.Expr):
        last_expr = tree.body.pop()
        if tree.body:
            exec(compile(tree, "<eval>", "exec"), globals_dict)
        return eval(compile(ast.Expression(last_expr.value), "<eval>", "eval"), globals_dict)
    else:
        # No trailing expression - exec all and return 'result' if set
        exec(compile(tree, "<eval>", "exec"), globals_dict)
        return globals_dict.get("result")


def make_handler(bv):
    """Create a handler class bound to a specific BinaryView."""
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
            exec_globals = {"bv": bv, "binaryninja": binaryninja}

            try:
                result = _eval_code(code, exec_globals)
                response = {"success": True, "result": repr(result)}
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
                    "binary": bv.file.filename if bv else None,
                    "functions": len(list(bv.functions)) if bv else 0,
                }
                self.wfile.write(json.dumps(response).encode("utf-8"))
            else:
                self.send_error(404, "Not Found")
    return EvalHandler


def _get_bv_key(bv):
    """Get a hashable key for a BinaryView."""
    return id(bv)


def _find_free_port(start_port):
    """Find a free port starting from start_port."""
    import socket
    port = start_port
    while port < start_port + 100:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            port += 1
    return None


def get_server_for_bv(bv):
    """Get server info for a BinaryView, or None if not running."""
    if bv is None:
        return None
    return _servers.get(_get_bv_key(bv))


def start_server(bv, port=None):
    """Start the eval server with given BinaryView."""
    if bv is None:
        _log_error("[EvalServer] No BinaryView provided")
        return

    key = _get_bv_key(bv)
    if key in _servers:
        _, _, existing_port = _servers[key]
        _log(f"[EvalServer] Server already running on port {existing_port}")
        return

    # Find a free port
    if port is None:
        port = _find_free_port(SERVER_PORT)
    if port is None:
        _log_error("[EvalServer] No free port found")
        return

    try:
        server = HTTPServer(("127.0.0.1", port), make_handler(bv))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        _servers[key] = (server, thread, port)
        _log(f"[EvalServer] Started on http://127.0.0.1:{port}")
        _log("[EvalServer] POST /eval with JSON {\"code\": \"<python>\"} to evaluate")
    except Exception as e:
        _log_error(f"[EvalServer] Failed to start: {e}")


def stop_server(bv=None):
    """Stop the eval server for given BinaryView."""
    if bv is None:
        _log("[EvalServer] No BinaryView provided")
        return

    key = _get_bv_key(bv)
    if key not in _servers:
        _log("[EvalServer] Server not running for this view")
        return

    server, thread, port = _servers.pop(key)
    server.shutdown()
    _log(f"[EvalServer] Server stopped (port {port})")


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
        server_info = get_server_for_bv(bv)
        if server_info:
            server_info[1].join()  # join the thread
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
        stop_server(bv)


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

    # Status bar indicator
    _status_btn = None

    def _get_current_bv():
        """Get the current BinaryView from UI context."""
        from binaryninjaui import UIContext
        ctx = UIContext.activeContext()
        if not ctx:
            ctxs = UIContext.allContexts()
            ctx = ctxs[0] if ctxs else None
        if not ctx:
            return None
        vf = ctx.getCurrentViewFrame()
        if not vf:
            return None
        return vf.getCurrentBinaryView()

    def _toggle_from_status_bar():
        """Toggle server from status bar click."""
        bv = _get_current_bv()
        if bv is None:
            return
        server_info = get_server_for_bv(bv)
        if server_info is None:
            start_server(bv)
        else:
            stop_server(bv)
        _update_status_bar(bv)

    def _update_status_bar(bv):
        """Update the status bar button for current bv."""
        def do_update():
            if _status_btn is None:
                return
            server_info = get_server_for_bv(bv)
            if server_info is None:
                _status_btn.setText("Eval: OFF")
                _status_btn.setStyleSheet("")
            else:
                _, _, port = server_info
                _status_btn.setText(f"Eval: :{port}")
                _status_btn.setStyleSheet("color: #6a6;")
        import binaryninja
        binaryninja.execute_on_main_thread(do_update)

    def _init_status_bar():
        """Initialize the status bar widget."""
        global _status_btn
        from binaryninjaui import UIContext
        from PySide6.QtWidgets import QToolButton
        ctx = UIContext.allContexts()
        if not ctx:
            return
        mw = ctx[0].mainWindow()
        if not mw:
            return
        sb = mw.statusBar()
        _status_btn = QToolButton()
        _status_btn.setText("Eval: OFF")
        _status_btn.setAutoRaise(True)
        _status_btn.setObjectName("eval_server_status")
        _status_btn.clicked.connect(_toggle_from_status_bar)
        sb.addPermanentWidget(_status_btn)

    # View change notification to update status bar
    from binaryninjaui import UIContext, UIContextNotification

    class EvalServerNotification(UIContextNotification):
        def OnViewChange(self, context, frame, type):
            bv = _get_current_bv()
            _update_status_bar(bv)

    _notification = EvalServerNotification()
    UIContext.registerNotification(_notification)

    # Initialize status bar on main thread
    import binaryninja
    binaryninja.execute_on_main_thread(_init_status_bar)

else:
    _run_headless()
