#!/usr/bin/env python3
import curses
import random
import re
import sys
import time

# Capture PC system time as entropy key for pseudo-random soup generation
PC_EPOCH = time.time()
SESSION_KEY = int(PC_EPOCH * 1000) & 0xFFFFFFFF  # 32-bit hardware entropy key

# Target directive the player must assemble:
TARGET_SENTENCE = ["PURGE", "CORE", "*132*", "IF", "COOLANT", "DROPS"]

# Multi-token bank per row:
# (token, alignment_phase)
ROW_WORD_CONFIG = {
    0:  [("PURGE", 2), ("VALVE", 6)],
    1:  [("TURBINE", 4), ("AT", 1)],
    2:  [("CORE", 5), ("ISOLATE", 2)],
    3:  [("*132*", 3), ("RESET", 5)],             # Target 3 (*132*) reveals at phase 3
    4:  [("PUMP", 6), ("*409*", 1), ("LOCK", 4)], # Decoy coated number *409*
    5:  [("IF", 3), ("STATIC", 7)],               # Target 4 at phase 3
    6:  [("ONLINE", 0), ("LEAK", 2)],
    7:  [("ACTUATOR", 4), ("*880*", 5)],          # Decoy coated number *880*
    8:  [("COOLANT", 1), ("STATUS", 3)],          # Target 5 at phase 1
    9:  [("OVERHEAT", 4), ("WARN", 0)],
    10: [("FEEDLINE", 7), ("DRAIN", 2)],
    11: [("DROPS", 5), ("SHUTDOWN", 3)],          # Target 6 at phase 5
    12: [("SENSOR", 1), ("RELAY", 6)],
    13: [("STABLE", 7)],
    14: [("VENT", 3), ("TRIP", 5)],
    15: [("SYSTEM", 0), ("FAULT", 4)]
}

BASE_ADDRS = [0xF400 + (i * 0x10) for i in range(16)]

# Noise symbols (pure punctuation delimiters and unpadded numbers)
PUNCT_SYMBOLS = "!@#$%^&()_+-=~:;/?|\\<>0123456789"
ROW_BODY_LEN = 23

def rotate_letter(c: str, shift: int) -> str:
    """Rotates an uppercase letter cleanly within A-Z."""
    idx = ord(c) - 65
    return chr(65 + ((idx + shift) % 26))

def rotate_digit(c: str, shift: int) -> str:
    """Rotates numbers cleanly within 0-9."""
    idx = ord(c) - 48
    return chr(48 + ((idx + shift) % 10))

def rotate_symbol(c: str, shift: int) -> str:
    """Rotates noise symbols with no dead glyphs."""
    idx = PUNCT_SYMBOLS.index(c) if c in PUNCT_SYMBOLS else 0
    return PUNCT_SYMBOLS[(idx + shift * 3 + 1) % len(PUNCT_SYMBOLS)]

def rotate_token_char(c: str, shift: int) -> str:
    """Rotates a character inside a target token (letters, numbers, or retaining stars)."""
    if c == '*':
        return '*'
    elif 'A' <= c <= 'Z':
        return rotate_letter(c, shift)
    elif '0' <= c <= '9':
        return rotate_digit(c, shift)
    return c

def generate_time_seeded_rows(session_key: int):
    """
    Pseudo-random soup generator driven by PC system time (session_key).
    Generates dynamic word placement and randomized noise stream per run.
    """
    rows = {}
    for r in range(16):
        word_defs = ROW_WORD_CONFIG[r]
        addr = BASE_ADDRS[r]
        
        # Mix row address, row index, and PC time key
        row_seed = (session_key ^ (addr << 8) ^ (r * 0x1F1F)) & 0xFFFFFFFF
        rng = random.Random(row_seed)
        
        num_words = len(word_defs)
        word_slots = []
        
        cursor = 1
        for token, phase in word_defs:
            w_len = len(token)
            max_start = ROW_BODY_LEN - w_len - (num_words - len(word_slots) - 1) * 4 - 1
            start_idx = cursor if cursor > max_start else rng.randint(cursor, max_start)
            
            word_slots.append({
                "token": token,
                "phase": phase,
                "start": start_idx,
                "len": w_len
            })
            cursor = start_idx + w_len + 1
            
        # Time-seeded noise baseline
        stream = [rng.choice(PUNCT_SYMBOLS) for _ in range(ROW_BODY_LEN)]
        
        # Enforce delimiters around slots
        for slot in word_slots:
            s = slot["start"]
            e = s + slot["len"]
            if s > 0:
                stream[s - 1] = rng.choice(":;|=/!%_")
            if e < ROW_BODY_LEN:
                stream[e] = rng.choice(":;|=/!%_")
                
        rows[r] = {
            "slots": word_slots,
            "base_stream": stream
        }
    return rows

PRECOMPUTED = generate_time_seeded_rows(SESSION_KEY)

def get_row_render_data(row_idx: int, phase: int, base_x: int):
    """
    Renders 35-char row: '0xADDR [Nb] <23 chars body>'
    Delimits letter words [A-Z]+ and star-coated numbers \\*[0-9]+\\*.
    """
    addr = BASE_ADDRS[row_idx]
    prefix = f"0x{addr:04X} [{phase}b] "
    
    meta = PRECOMPUTED[row_idx]
    slots = meta["slots"]
    base_stream = meta["base_stream"]
    
    body = []
    i = 0
    while i < ROW_BODY_LEN:
        active_slot = None
        for s in slots:
            if s["start"] <= i < s["start"] + s["len"]:
                active_slot = s
                break
                
        if active_slot:
            char_idx = i - active_slot["start"]
            original_ch = active_slot["token"][char_idx]
            target_phase = active_slot["phase"]
            
            if phase == target_phase:
                body.append(original_ch)
            else:
                diff = (phase - target_phase)
                body.append(rotate_token_char(original_ch, diff))
            i += 1
        else:
            raw_sym = base_stream[i]
            body.append(rotate_symbol(raw_sym, phase))
            i += 1
            
    body_str = "".join(body)
    full_str = f"{prefix}{body_str}"
    
    # Grab tokens: [A-Za-z]+ or \\*[0-9]+\\*
    token_pattern = re.compile(r'(\*[0-9]+\*|[A-Za-z]+)')
    tokens = []
    for match in token_pattern.finditer(body_str):
        tok_val = match.group(0)
        tok_start_x = base_x + len(prefix) + match.start()
        tok_end_x = base_x + len(prefix) + match.end() - 1
        tokens.append({
            "val": tok_val,
            "start_x": tok_start_x,
            "end_x": tok_end_x,
            "row_idx": row_idx
        })
        
    return full_str, tokens

def run_tui(stdscr):
    curses.curs_set(1)
    stdscr.nodelay(False)
    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_GREEN, -1)                  # Standard phosphor green
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN) # Token highlight
    curses.init_pair(3, curses.COLOR_RED, -1)                    # Tries / Fault
    curses.init_pair(4, curses.COLOR_CYAN, -1)                   # Header accents
    curses.init_pair(5, curses.COLOR_YELLOW, -1)                 # Sentence buffer

    row_phases = [0] * 16
    assembled_sentence = []
    attempts = 4
    status_msg = "SCAN ROWS. ASSEMBLE 6-TOKEN DIRECTIVE (WORDS + *SERIAL* CODES)."

    cur_y = 5
    cur_x = 14

    while True:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()

        if max_y < 24 or max_x < 80:
            stdscr.addstr(0, 0, f"ERR: TERM {max_x}x{max_y} < 80x24. RESIZE WINDOW.", curses.color_pair(3))
            stdscr.refresh()
            stdscr.getch()
            continue

        # Grid bounds clamping
        cur_y = max(5, min(12, cur_y))
        if cur_x < 2:
            cur_x = 2
        elif 37 <= cur_x <= 41:
            cur_x = 42 if cur_x > 38 else 36
        elif cur_x > 76:
            cur_x = 76

        is_right_col = (cur_x >= 42)
        grid_row = cur_y - 5
        focused_row_idx = grid_row + (8 if is_right_col else 0)

        # 1. Header (Rows 0 - 4) with PC Epoch entropy signature
        stdscr.addstr(0, 2, "=== [VANDENBERG-OS // MEMORY FRAME DEMODULATOR] ===", curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(1, 2, f"ENTROPY_KEY: 0x{SESSION_KEY:08X} // RTC_EPOCH: {int(PC_EPOCH)}", curses.A_DIM)
        
        # Buffer display
        stdscr.addstr(2, 2, "PAYLOAD BUFFER : ", curses.color_pair(1))
        assembled_str = " ".join(assembled_sentence)
        stdscr.addstr(2, 19, f"[ {assembled_str} ]", curses.color_pair(5) | curses.A_BOLD)
        
        # Active row & attempts
        cur_p = row_phases[focused_row_idx]
        cur_addr = BASE_ADDRS[focused_row_idx]
        stdscr.addstr(3, 2, f"ACTIVE ROW: 0x{cur_addr:04X} [{cur_p}b] | TRIES: ", curses.color_pair(1))
        stdscr.addstr(3, 34, "■ " * attempts, curses.color_pair(3) | curses.A_BOLD)

        stdscr.addstr(4, 2, "─" * 76, curses.A_DIM)

        # 2. Dual-Column Grid (Rows 5 - 12)
        visible_tokens = []
        for r in range(8):
            y = 5 + r
            
            # Left column (rows 0..7)
            idx_l = r
            str_l, toks_l = get_row_render_data(idx_l, row_phases[idx_l], 2)
            visible_tokens.extend(toks_l)
            
            # Right column (rows 8..15)
            idx_r = r + 8
            str_r, toks_r = get_row_render_data(idx_r, row_phases[idx_r], 42)
            visible_tokens.extend(toks_r)

            stdscr.addstr(y, 2, str_l, curses.color_pair(1))
            stdscr.addstr(y, 39, "│", curses.A_DIM)
            stdscr.addstr(y, 42, str_r, curses.color_pair(1))

        # 3. Dynamic Word / Star-Code Grabbing
        hovered_token = None
        for tok in visible_tokens:
            tok_row = 5 + (tok["row_idx"] % 8)
            if cur_y == tok_row and tok["start_x"] <= cur_x <= tok["end_x"]:
                hovered_token = tok
                stdscr.addstr(cur_y, tok["start_x"], tok["val"], curses.color_pair(2) | curses.A_BOLD)
                break

        # 4. Footer & Diagnostic Status (Rows 13 - 23)
        stdscr.addstr(13, 2, "─" * 76, curses.A_DIM)
        
        if hovered_token:
            tok_info = f"CAPTURED TOKEN: \"{hovered_token['val']}\" (READY TO ACQUIRE)"
        else:
            tok_info = "RAW STATIC / UNCOATED SOUP (ONLY LETTERS OR *NUMBERS* CAPTURED)"
        stdscr.addstr(15, 2, tok_info, curses.color_pair(1))

        stdscr.addstr(17, 2, f"> STATUS: {status_msg}", curses.color_pair(1) | curses.A_BOLD)

        stdscr.addstr(19, 2, "CONTROLS:", curses.A_BOLD)
        stdscr.addstr(20, 2, "  h / j / k / l : Move cursor 1 char | Tab: Switch Column", curses.A_DIM)
        stdscr.addstr(21, 2, "  Shift+H / L   : Bit-Shift Focused Row Left/Right (-1b / +1b)", curses.color_pair(1))
        stdscr.addstr(22, 2, "  Enter / Click : Acquire Token to Buffer | Backspace: Pop Word", curses.A_DIM)
        stdscr.addstr(23, 2, "  q / Esc       : Abort Demodulation Session", curses.A_DIM)

        stdscr.move(cur_y, cur_x)
        stdscr.refresh()

        key = stdscr.getch()

        # Mouse Handling
        if key == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()
                if 5 <= my <= 12 and (2 <= mx <= 36 or 42 <= mx <= 76):
                    cur_y = my
                    cur_x = mx
                    if bstate & (curses.BUTTON1_CLICKED | curses.BUTTON1_DOUBLE_CLICKED):
                        key = ord('\n')
            except curses.error:
                pass

        # Global Exit
        if key in (ord('q'), 27):
            return None, "ABORTED BY OPERATOR."

        # Bit Shift Focused Row (Shift+H / Shift+L)
        elif key in (ord('H'), curses.KEY_SLEFT):
            row_phases[focused_row_idx] = (row_phases[focused_row_idx] - 1) % 8
            status_msg = f"ROW 0x{cur_addr:04X} SHIFTED TO 0b{row_phases[focused_row_idx]:03b} (-1b)"

        elif key in (ord('L'), curses.KEY_SRIGHT):
            row_phases[focused_row_idx] = (row_phases[focused_row_idx] + 1) % 8
            status_msg = f"ROW 0x{cur_addr:04X} SHIFTED TO 0b{row_phases[focused_row_idx]:03b} (+1b)"

        # Character-Level Navigation
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

        # Backspace: Pop last token from buffer
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if assembled_sentence:
                popped = assembled_sentence.pop()
                status_msg = f"REMOVED [{popped}] FROM PAYLOAD BUFFER."

        # Submission / Token Acquisition
        elif key in (ord('\n'), curses.KEY_ENTER):
            if not hovered_token:
                status_msg = "CURSOR NOT POSITIONED ON A VALID TOKEN."
                continue

            token_val = hovered_token["val"]
            assembled_sentence.append(token_val)
            status_msg = f"ACQUIRED [{token_val}] INTO BUFFER."

            # Check sentence completion
            if len(assembled_sentence) == len(TARGET_SENTENCE):
                if assembled_sentence == TARGET_SENTENCE:
                    return " ".join(assembled_sentence), "DIRECTIVE COMPILED AND VERIFIED."
                else:
                    attempts -= 1
                    assembled_sentence.clear()
                    if attempts <= 0:
                        return False, "SECURITY LOCKOUT: INVALID DIRECTIVE SEQUENCE."
                    status_msg = f"SYNTAX REJECTED: SEQUENCE DOES NOT MATCH OVERRIDE. TRIES: {attempts}"

def main():
    print(f"[*] Initializing TUI demodulator with RTC key: 0x{SESSION_KEY:08X}...")
    token, msg = curses.wrapper(run_tui)

    print("\n" + "=" * 62)
    if token:
        print(f"[+] SUCCESS: {msg}")
        print(f"[+] RECONSTRUCTED DIRECTIVE: \"{token}\"")
        print("[+] ROOT BYPASS ENGAGED. DIRECTORY UNLOCKED.")
    elif token is False:
        print(f"[-] CRITICAL: {msg}")
    else:
        print(f"[*] {msg}")
    print("=" * 62)

if __name__ == "__main__":
    main()