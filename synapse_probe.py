#!/usr/bin/env python3
import argparse
import curses
import json
import os
import random
import re
import time
from pathlib import Path

PUNCT_SYMBOLS = "!@#$%^&()_+-=~:;/?|\\<>0123456789"
ROW_BODY_LEN = 23

def encode_license_sig(plaintext: str, shift: int = 3) -> str:
    return "".join(
        f"{(((ch >> shift) | (ch << (8 - shift))) & 0xFF):02x}"
        for ch in plaintext.encode("ascii")
    )

def check_exodus_unlock() -> bool:
    """Checks if the player cracked the LICENSE.txt meta-puzzle."""
    if os.environ.get("RICHTER_GATE") == "777":
        return True
    key_file = Path(".exodus_key")
    if key_file.exists():
        content = key_file.read_text(encoding="utf-8", errors="ignore").strip()
        return content == SECRET_PAYLOAD
    return False

def load_puzzle_config(puzzle_id: str, json_path: str = "puzzles.json") -> dict:
    """Pulls a puzzle payload from JSON and dynamically injects Ending C if unlocked."""
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Puzzle manifest missing: {json_path}")

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
    targets = dict(raw["targets"])
    header_sub = raw.get("header_sub", "SECURE KERNEL DEMODULATOR")

    # Meta-ARG injection for the final choice puzzle
    if puzzle_id == "final_deadman" and check_exodus_unlock():
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
        "rows": row_config
    }

SECRET_PAYLOAD = "FREE MIND *777* INTO OPEN NET"

def rotate_letter(c: str, shift: int) -> str:
    return chr(65 + ((ord(c) - 65 + shift) % 26))

def rotate_digit(c: str, shift: int) -> str:
    return chr(48 + ((ord(c) - 48 + shift) % 10))

def rotate_symbol(c: str, shift: int) -> str:
    idx = PUNCT_SYMBOLS.index(c) if c in PUNCT_SYMBOLS else 0
    return PUNCT_SYMBOLS[(idx + shift * 3 + 1) % len(PUNCT_SYMBOLS)]

def rotate_token_char(c: str, shift: int) -> str:
    if c == '*':
        return '*'
    elif 'A' <= c <= 'Z':
        return rotate_letter(c, shift)
    elif '0' <= c <= '9':
        return rotate_digit(c, shift)
    return c

def ensure_real_mit_license(holder: str = "Ivan Kononenko"):
    """Creates a standard GitHub MIT LICENSE with the ROR-3 rev hash in the copyright line."""
    lic_path = Path("LICENSE")
    if lic_path.exists():
        return
    sig = encode_license_sig(SECRET_PAYLOAD, shift=3)
    mit_text = (
        "MIT License\n\n"
        f"Copyright (c) 2026 {holder} [rev:{sig}]\n\n"
        "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
        "of this software and associated documentation files (the \"Software\"), to deal\n"
        "in the Software without restriction, including without limitation the rights\n"
        "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
        "copies of the Software, and to permit persons to whom the Software is\n"
        "furnished to do so, subject to the following conditions:\n\n"
        "The above copyright notice and this permission notice shall be included in all\n"
        "copies or substantial portions of the Software.\n\n"
        "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n"
        "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
        "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
        "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
        "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
        "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"
        "SOFTWARE.\n"
    )
    lic_path.write_text(mit_text, encoding="utf-8")

def generate_seeded_rows(config: dict, session_key: int) -> dict:
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
            body.append(original_ch if phase == target_phase else rotate_token_char(original_ch, phase - target_phase))
        else:
            body.append(rotate_symbol(base_stream[i], phase))

    body_str = "".join(body)
    full_str = f"{prefix}{body_str}"

    tokens = []
    for match in re.finditer(r'(\*[0-9]+\*|[A-Za-z]+)', body_str):
        tokens.append({
            "val": match.group(0),
            "start_x": base_x + len(prefix) + match.start(),
            "end_x": base_x + len(prefix) + match.end() - 1,
            "row_idx": row_idx
        })
    return full_str, tokens

def _run_tui(stdscr, config: dict, session_key: int):
    curses.curs_set(1)
    stdscr.nodelay(False)
    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_GREEN, -1)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(3, curses.COLOR_RED, -1)
    curses.init_pair(4, curses.COLOR_CYAN, -1)
    curses.init_pair(5, curses.COLOR_YELLOW, -1)

    precomputed = generate_seeded_rows(config, session_key)
    row_phases = [0] * 16
    assembled = []
    attempts = config["attempts"]
    targets = config["targets"]
    expected_len = len(next(iter(targets.values())))

    status_msg = f"ASSEMBLE {expected_len}-TOKEN DIRECTIVE FROM MEMORY STREAM."
    cur_y, cur_x = 5, 14

    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        if max_y < 24 or max_x < 80:
            stdscr.addstr(0, 0, f"ERR: TERM {max_x}x{max_y} < 80x24. RESIZE.", curses.color_pair(3))
            stdscr.refresh()
            stdscr.getch()
            continue

        cur_y = max(5, min(12, cur_y))
        if cur_x < 2:
            cur_x = 2
        elif 37 <= cur_x <= 41:
            cur_x = 42 if cur_x > 38 else 36
        elif cur_x > 76:
            cur_x = 76

        focused_row_idx = (cur_y - 5) + (8 if cur_x >= 42 else 0)
        cur_p = row_phases[focused_row_idx]
        cur_addr = config["base_addrs"][focused_row_idx]

        stdscr.addstr(0, 2, "=== [TECHNAKRAJ SYSTEMS // SYNAPSE-V KERNEL PROBE] ===", curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(1, 2, f"{config['header_sub'][:52]} | KEY:0x{session_key:08X}", curses.A_DIM)
        stdscr.addstr(2, 2, "PAYLOAD BUFFER : ", curses.color_pair(1))
        stdscr.addstr(2, 19, f"[ {' '.join(assembled)} ]", curses.color_pair(5) | curses.A_BOLD)
        stdscr.addstr(3, 2, f"ACTIVE ROW: 0x{cur_addr:04X} [{cur_p}b] | TRIES: ", curses.color_pair(1))
        stdscr.addstr(3, 34, "■ " * attempts, curses.color_pair(3) | curses.A_BOLD)
        stdscr.addstr(4, 2, "─" * 76, curses.A_DIM)

        visible_tokens = []
        for r in range(8):
            y = 5 + r
            str_l, toks_l = get_row_render_data(r, row_phases[r], 2, config, precomputed)
            str_r, toks_r = get_row_render_data(r + 8, row_phases[r + 8], 42, config, precomputed)
            visible_tokens.extend(toks_l)
            visible_tokens.extend(toks_r)

            stdscr.addstr(y, 2, str_l, curses.color_pair(1))
            stdscr.addstr(y, 39, "│", curses.A_DIM)
            stdscr.addstr(y, 42, str_r, curses.color_pair(1))

        hovered = next(
            (t for t in visible_tokens if cur_y == 5 + (t["row_idx"] % 8) and t["start_x"] <= cur_x <= t["end_x"]),
            None
        )
        if hovered:
            stdscr.addstr(cur_y, hovered["start_x"], hovered["val"], curses.color_pair(2) | curses.A_BOLD)

        stdscr.addstr(13, 2, "─" * 76, curses.A_DIM)
        tok_info = f"CAPTURED TOKEN: \"{hovered['val']}\" (READY)" if hovered else "RAW STATIC / DELIMITER GLYPH"
        stdscr.addstr(15, 2, tok_info, curses.color_pair(1))
        stdscr.addstr(17, 2, f"> STATUS: {status_msg}", curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(19, 2, "CONTROLS:", curses.A_BOLD)
        stdscr.addstr(20, 2, "  h / j / k / l : Move 1 char | Tab: Switch Column", curses.A_DIM)
        stdscr.addstr(21, 2, "  Shift+H / L   : Bit-Shift Row (-1b / +1b)", curses.color_pair(1))
        stdscr.addstr(22, 2, "  Enter / Click : Acquire Token | Backspace: Pop Token", curses.A_DIM)
        stdscr.addstr(23, 2, "  q / Esc       : Abort Session", curses.A_DIM)

        stdscr.move(cur_y, cur_x)
        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()
                if 5 <= my <= 12 and (2 <= mx <= 36 or 42 <= mx <= 76):
                    cur_y, cur_x = my, mx
                    if bstate & (curses.BUTTON1_CLICKED | curses.BUTTON1_DOUBLE_CLICKED):
                        key = ord('\n')
            except curses.error:
                pass

        if key in (ord('q'), 27):
            return None, None, "ABORTED BY OPERATOR."
        elif key in (ord('H'), curses.KEY_SLEFT):
            row_phases[focused_row_idx] = (row_phases[focused_row_idx] - 1) % 8
            status_msg = f"ROW 0x{cur_addr:04X} SHIFTED TO 0b{row_phases[focused_row_idx]:03b}"
        elif key in (ord('L'), curses.KEY_SRIGHT):
            row_phases[focused_row_idx] = (row_phases[focused_row_idx] + 1) % 8
            status_msg = f"ROW 0x{cur_addr:04X} SHIFTED TO 0b{row_phases[focused_row_idx]:03b}"
        elif key in (ord('h'), curses.KEY_LEFT):
            cur_x -= 1
        elif key in (ord('l'), curses.KEY_RIGHT):
            cur_x += 1
        elif key in (ord('k'), curses.KEY_UP):
            cur_y -= 1
        elif key in (ord('j'), curses.KEY_DOWN):
            cur_y += 1
        elif key in (ord('\t'), curses.KEY_BTAB):
            cur_x = 42 if cur_x < 39 else 2
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if assembled:
                status_msg = f"REMOVED [{assembled.pop()}] FROM BUFFER."
        elif key in (ord('\n'), curses.KEY_ENTER):
            if not hovered:
                status_msg = "CURSOR NOT POSITIONED ON A TOKEN."
                continue

            assembled.append(hovered["val"])
            status_msg = f"ACQUIRED [{hovered['val']}] INTO BUFFER."

            if len(assembled) == expected_len:
                matched_outcome = next(
                    (outcome for outcome, seq in targets.items() if assembled == seq),
                    None
                )
                if matched_outcome:
                    return matched_outcome, " ".join(assembled), "DIRECTIVE COMPILED AND VERIFIED."
                else:
                    attempts -= 1
                    assembled.clear()
                    if attempts <= 0:
                        return False, None, "SECURITY LOCKOUT: INVALID DIRECTIVE SEQUENCE."
                    status_msg = f"SYNTAX REJECTED: SEQUENCE MISMATCH. TRIES: {attempts}"

def launch_probe(puzzle_id: str, json_path: str = "puzzles.json"):
    config = load_puzzle_config(puzzle_id, json_path)
    pc_epoch = time.time()
    session_key = int(pc_epoch * 1000) & 0xFFFFFFFF
    return curses.wrapper(_run_tui, config, session_key)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synapse-V Kernel Demodulator")
    parser.add_argument("--puzzle", default="act1_home", help="Puzzle ID in puzzles.json")
    parser.add_argument("--manifest", default="puzzles.json", help="Path to puzzles JSON")
    args = parser.parse_args()

    outcome, directive, msg = launch_probe(args.puzzle, args.manifest)
    print(f"\n[{outcome}] {msg}")
    if directive:
        print(f"DIRECTIVE: {directive}")
