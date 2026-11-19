import json
import random
import re
import time
from pathlib import Path
from core.config import get_manifest_path
from core.crypto import check_exodus_unlock

PUNCT_SYMBOLS = "!@#$%^&()_+-=~:;/?|\\<>0123456789"
ROW_BODY_LEN = 23


def rotate_letter(c: str, shift: int) -> str:
    return chr(65 + ((ord(c) - 65 + shift) % 26))


def rotate_digit(c: str, shift: int) -> str:
    return chr(48 + ((ord(c) - 48 + shift) % 10))


def rotate_symbol(c: str, shift: int) -> str:
    idx = PUNCT_SYMBOLS.index(c) if c in PUNCT_SYMBOLS else 0
    return PUNCT_SYMBOLS[(idx + shift * 3 + 1) % len(PUNCT_SYMBOLS)]


def rotate_token_char(c: str, shift: int) -> str:
    if c == "*":
        return "*"
    elif "A" <= c <= "Z":
        return rotate_letter(c, shift)
    elif "0" <= c <= "9":
        return rotate_digit(c, shift)
    return c


def load_puzzle_config(
    puzzle_id: str,
    json_path: str | Path | None = None,
    session_env: dict | None = None,
) -> dict:
    """Loads puzzle configuration and injects the secret Ending C branch if unlocked."""
    path = Path(json_path) if json_path else get_manifest_path()
    if not path.exists():
        raise FileNotFoundError(f"Puzzle manifest missing: {path}")

    with path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    if puzzle_id not in manifest:
        raise KeyError(f"Unknown puzzle slice ID: '{puzzle_id}'")

    raw = manifest[puzzle_id]
    base_addr_int = int(raw.get("base_addr", "0xF400"), 16)

    row_config = {
        int(k): [(item[0], int(item[1])) for item in v]
        for k, v in raw["rows"].items()
    }
    targets = {k: list(v) for k, v in raw["targets"].items()}
    header_sub = raw.get("header_sub", "SECURE KERNEL DEMODULATOR")

    if puzzle_id == "final_deadman" and check_exodus_unlock(session_env):
        header_sub = "MASTER NEURAL LOCK // [EXODUS VECTOR DETECTED]"
        targets["ending_exodus"] = ["FREE", "MIND", "*777*", "INTO", "OPEN", "NET"]
        secret_tokens = [
            (0, ("FREE", 3)),
            (1, ("MIND", 0)),
            (2, ("*777*", 6)),
            (3, ("INTO", 4)),
            (4, ("OPEN", 7)),
            (5, ("NET", 3)),
        ]
        for r_idx, tok_pair in secret_tokens:
            row_config[r_idx].append(tok_pair)

    return {
        "id": puzzle_id,
        "header_sub": header_sub,
        "base_addrs": [base_addr_int + (i * 0x10) for i in range(16)],
        "attempts": int(raw.get("attempts", 4)),
        "targets": targets,
        "rows": row_config,
    }


def generate_seeded_rows(config: dict, session_key: int) -> dict:
    """Generates time-seeded non-overlapping word slots and noise for a loaded puzzle."""
    rows = {}
    base_addrs = config["base_addrs"]
    for r in range(16):
        word_defs = config["rows"].get(r, [])
        addr = base_addrs[r]
        row_seed = (session_key ^ (addr << 8) ^ (r * 0x1F1F)) & 0xFFFFFFFF
        rng = random.Random(row_seed)

        num_words = len(word_defs)
        word_slots = []
        cursor = 1

        for token, phase in word_defs:
            w_len = len(token)
            max_start = ROW_BODY_LEN - w_len - (num_words - len(word_slots) - 1) * 3 - 1
            start_idx = cursor if cursor > max_start else rng.randint(cursor, max_start)
            word_slots.append({"token": token, "phase": phase, "start": start_idx, "len": w_len})
            cursor = start_idx + w_len + 1

        stream = [rng.choice(PUNCT_SYMBOLS) for _ in range(ROW_BODY_LEN)]
        for slot in word_slots:
            s, e = slot["start"], slot["start"] + slot["len"]
            if s > 0:
                stream[s - 1] = rng.choice(":;|=/!%_")
            if e < ROW_BODY_LEN:
                stream[e] = rng.choice(":;|=/!%_")

        rows[r] = {"slots": word_slots, "base_stream": stream}
    return rows


def get_row_render_data(row_idx: int, phase: int, base_x: int, config: dict, precomputed: dict):
    addr = config["base_addrs"][row_idx]
    prefix = f"0x{addr:04X} [{phase}b] "
    meta = precomputed[row_idx]
    slots, base_stream = meta["slots"], meta["base_stream"]

    body = []
    for i in range(ROW_BODY_LEN):
        active_slot = next((s for s in slots if s["start"] <= i < s["start"] + s["len"]), None)
        if active_slot:
            original_ch = active_slot["token"][i - active_slot["start"]]
            target_phase = active_slot["phase"]
            body.append(
                original_ch
                if phase == target_phase
                else rotate_token_char(original_ch, phase - target_phase)
            )
        else:
            body.append(rotate_symbol(base_stream[i], phase))

    body_str = "".join(body)
    full_str = f"{prefix}{body_str}"

    tokens = []
    for match in re.finditer(r"(\*[0-9]+\*|[A-Za-z]+)", body_str):
        tokens.append({
            "val": match.group(0),
            "start_x": base_x + len(prefix) + match.start(),
            "end_x": base_x + len(prefix) + match.end() - 1,
            "row_idx": row_idx,
        })
    return full_str, tokens


class DemodulatorSession:
    """UI-agnostic state machine driving both the curses CLI and xterm.js web TUI."""

    def __init__(
        self,
        puzzle_id: str,
        json_path: str | Path | None = None,
        session_env: dict | None = None,
    ):
        self.config = load_puzzle_config(puzzle_id, json_path, session_env)
        self.pc_epoch = time.time()
        self.session_key = int(self.pc_epoch * 1000) & 0xFFFFFFFF
        self.precomputed = generate_seeded_rows(self.config, self.session_key)

        self.row_phases = [0] * 16
        self.assembled: list[str] = []
        self.attempts = self.config["attempts"]
        self.targets = self.config["targets"]
        self.expected_len = len(next(iter(self.targets.values())))

        self.cur_y = 5
        self.cur_x = 14
        self.status_msg = f"ASSEMBLE {self.expected_len}-TOKEN DIRECTIVE FROM MEMORY STREAM."

        # Terminal resolution state: None (in progress), str (outcome_id), False (lockout), "ABORT"
        self.result: str | bool | None = None
        self.final_directive: str | None = None

    @property
    def focused_row_idx(self) -> int:
        return (self.cur_y - 5) + (8 if self.cur_x >= 42 else 0)

    @property
    def focused_phase(self) -> int:
        return self.row_phases[self.focused_row_idx]

    @property
    def focused_addr(self) -> int:
        return self.config["base_addrs"][self.focused_row_idx]

    def set_cursor(self, y: int, x: int):
        self.cur_y = max(5, min(12, y))
        if x < 2:
            self.cur_x = 2
        elif 37 <= x <= 41:
            self.cur_x = 42 if x > 38 else 36
        elif x > 76:
            self.cur_x = 76
        else:
            self.cur_x = x

    def move_cursor(self, dy: int, dx: int):
        self.set_cursor(self.cur_y + dy, self.cur_x + dx)

    def switch_column(self):
        self.cur_x = 42 if self.cur_x < 39 else 2

    def shift_row(self, delta: int):
        idx = self.focused_row_idx
        self.row_phases[idx] = (self.row_phases[idx] + delta) % 8
        self.status_msg = f"ROW 0x{self.focused_addr:04X} SHIFTED TO 0b{self.row_phases[idx]:03b}"

    def pop_token(self):
        if self.assembled:
            self.status_msg = f"REMOVED [{self.assembled.pop()}] FROM BUFFER."

    def get_grid_snapshot(self) -> tuple[list[tuple[str, str]], dict | None]:
        """Returns 8 rows of (left_str, right_str) plus the currently hovered token dict."""
        rows_out = []
        visible_tokens = []
        for r in range(8):
            str_l, toks_l = get_row_render_data(r, self.row_phases[r], 2, self.config, self.precomputed)
            str_r, toks_r = get_row_render_data(r + 8, self.row_phases[r + 8], 42, self.config, self.precomputed)
            rows_out.append((str_l, str_r))
            visible_tokens.extend(toks_l)
            visible_tokens.extend(toks_r)

        hovered = next(
            (
                t
                for t in visible_tokens
                if self.cur_y == 5 + (t["row_idx"] % 8) and t["start_x"] <= self.cur_x <= t["end_x"]
            ),
            None,
        )
        return rows_out, hovered

    def acquire_token(self):
        _, hovered = self.get_grid_snapshot()
        if not hovered:
            self.status_msg = "CURSOR NOT POSITIONED ON A TOKEN."
            return

        self.assembled.append(hovered["val"])
        self.status_msg = f"ACQUIRED [{hovered['val']}] INTO BUFFER."

        if len(self.assembled) == self.expected_len:
            matched_outcome = next(
                (outcome for outcome, seq in self.targets.items() if self.assembled == seq),
                None,
            )
            if matched_outcome:
                self.result = matched_outcome
                self.final_directive = " ".join(self.assembled)
                self.status_msg = "DIRECTIVE COMPILED AND VERIFIED."
            else:
                self.attempts -= 1
                self.assembled.clear()
                if self.attempts <= 0:
                    self.result = False
                    self.status_msg = "SECURITY LOCKOUT: INVALID DIRECTIVE SEQUENCE."
                else:
                    self.status_msg = f"SYNTAX REJECTED: SEQUENCE MISMATCH. TRIES: {self.attempts}"