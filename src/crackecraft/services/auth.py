from __future__ import annotations

import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable, cast
import minecraft_launcher_lib

from crackecraft.services.credential_store import CredentialStore


class _CallbackServer(HTTPServer):
    callback_url = ""
    event: threading.Event
    callback_port: int


class _CallbackHandler(BaseHTTPRequestHandler):
    server: _CallbackServer

    def do_GET(self) -> None:  # noqa: N802
        server = self.server
        server.callback_url = f"http://localhost:{server.callback_port}{self.path}"
        server.event.set()
        body = b"<html><body style='font:16px sans-serif;background:#101218;color:#eef'>CrackeCraft sign-in complete. You can close this tab and return to the launcher.</body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        return


class MicrosoftAuth:
    REDIRECT_URI_TEMPLATE = "http://localhost:{port}"

    def __init__(self, credentials: CredentialStore) -> None:
        self.credentials = credentials

    def login(self, client_id: str) -> dict[str, str]:
        if not client_id.strip():
            raise ValueError("Configura el Client ID de tu aplicación Microsoft en Ajustes antes de iniciar sesión.")
        handler_factory = cast(Callable[[Any, Any, _CallbackServer], BaseHTTPRequestHandler], _CallbackHandler)
        server = _CallbackServer(("127.0.0.1", 0), handler_factory)
        server.timeout = 1
        server.event = threading.Event()
        server.callback_port = int(server.server_address[1])
        redirect_uri = self.REDIRECT_URI_TEMPLATE.format(port=server.callback_port)
        login_url, state, verifier = minecraft_launcher_lib.microsoft_account.get_secure_login_data(client_id, redirect_uri)
        if not webbrowser.open(login_url):
            server.server_close()
            raise RuntimeError("No se pudo abrir el navegador predeterminado.")
        try:
            deadline = 300
            while deadline > 0 and not server.event.is_set():
                server.handle_request()
                deadline -= 1
            if not server.event.is_set():
                raise TimeoutError("Se agotó el tiempo de espera de inicio de sesión.")
            code = minecraft_launcher_lib.microsoft_account.parse_auth_code_url(server.callback_url, state)
            response = minecraft_launcher_lib.microsoft_account.complete_login(client_id, None, redirect_uri, code, verifier)
            return {str(k): str(v) for k, v in response.items() if k in {"id", "name", "access_token", "refresh_token"}}
        finally:
            server.server_close()

    def refresh(self, client_id: str, account_id: str) -> dict[str, str]:
        saved = self.credentials.load(account_id)
        if not saved or not saved.get("refresh_token"):
            raise RuntimeError("No hay una sesión guardada. Inicia sesión de nuevo.")
        response = minecraft_launcher_lib.microsoft_account.complete_refresh(client_id, None, None, saved["refresh_token"])
        updated = {str(k): str(v) for k, v in response.items() if k in {"id", "name", "access_token", "refresh_token"}}
        self.credentials.save(account_id, updated)
        return updated
