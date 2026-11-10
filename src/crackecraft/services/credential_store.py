from __future__ import annotations

import json

import keyring
from keyring.errors import PasswordDeleteError


class CredentialStore:
    """Keep refresh tokens in the operating system credential store."""

    SERVICE = "CrackeCraft.MicrosoftAccount"

    @staticmethod
    def _backend() -> None:
        backend = keyring.get_keyring()
        module = type(backend).__module__
        if module.startswith("keyrings.alt") or getattr(backend, "priority", 0) <= 0:
            raise RuntimeError("No hay un almacén seguro del sistema disponible. Configura Windows Credential Manager o Secret Service en Linux.")

    def save(self, account_id: str, payload: dict[str, str]) -> None:
        self._backend()
        keyring.set_password(self.SERVICE, account_id, json.dumps(payload, separators=(",", ":")))

    def load(self, account_id: str) -> dict[str, str] | None:
        self._backend()
        raw = keyring.get_password(self.SERVICE, account_id)
        if not raw:
            return None
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise RuntimeError("La credencial guardada no tiene un formato válido.")
        return {str(k): str(v) for k, v in value.items()}

    def delete(self, account_id: str) -> None:
        self._backend()
        try:
            keyring.delete_password(self.SERVICE, account_id)
        except PasswordDeleteError:
            pass
