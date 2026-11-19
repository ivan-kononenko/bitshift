import os
from pathlib import Path
from core.config import REPO_ROOT

SECRET_PAYLOAD = "FREE MIND *777* INTO OPEN NET"


def encode_license_sig(plaintext: str, shift: int = 3) -> str:
    """Cyclic right-shift (ROR) each ASCII byte by `shift` bits and return hex."""
    return "".join(
        f"{(((ch >> shift) | (ch << (8 - shift))) & 0xFF):02x}"
        for ch in plaintext.encode("ascii")
    )


def decode_license_sig(hex_sig: str, shift: int = 3) -> str:
    """Cyclic left-shift (ROL) each byte by `shift` bits to recover ASCII."""
    raw = bytes.fromhex(hex_sig.strip())
    decoded = bytearray(
        ((b << shift) | (b >> (8 - shift))) & 0xFF
        for b in raw
    )
    return decoded.decode("ascii", errors="ignore")


def check_exodus_unlock(session_env: dict | None = None) -> bool:
    """
    Checks if the player cracked the LICENSE meta-puzzle.
    Prioritizes per-session state (for web players) before falling back to local disk/env.
    """
    if session_env:
        if session_env.get("RICHTER_GATE") == "777":
            return True
        if session_env.get("EXODUS_KEY", "").strip() == SECRET_PAYLOAD:
            return True

    if os.environ.get("RICHTER_GATE") == "777":
        return True

    for candidate in (Path.cwd() / ".exodus_key", REPO_ROOT / ".exodus_key"):
        if candidate.exists():
            content = candidate.read_text(encoding="utf-8", errors="ignore").strip()
            if content == SECRET_PAYLOAD:
                return True

    return False