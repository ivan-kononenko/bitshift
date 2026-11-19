import curses
from pathlib import Path
from core.demodulator import DemodulatorSession


def _run_tui(stdscr, session: DemodulatorSession):
    curses.curs_set(1)
    stdscr.nodelay(False)
    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
    curses.use_default_colors()

    curses.init_pair(1, curses.COLOR_GREEN, -1)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(3, curses.COLOR_RED, -1)
    curses.init_pair(4, curses.COLOR_CYAN, -1)
    curses.init_pair(5, curses.COLOR_YELLOW, -1)

    while session.result is None:
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()
        if max_y < 24 or max_x < 80:
            stdscr.addstr(0, 0, f"ERR: TERM {max_x}x{max_y} < 80x24. RESIZE.", curses.color_pair(3))
            stdscr.refresh()
            stdscr.getch()
            continue

        cfg = session.config
        stdscr.addstr(0, 2, "=== [TECHNAKRAJ SYSTEMS // SYNAPSE-V KERNEL PROBE] ===", curses.color_pair(4) | curses.A_BOLD)
        stdscr.addstr(1, 2, f"{cfg['header_sub'][:52]} | KEY:0x{session.session_key:08X}", curses.A_DIM)
        stdscr.addstr(2, 2, "PAYLOAD BUFFER : ", curses.color_pair(1))
        stdscr.addstr(2, 19, f"[ {' '.join(session.assembled)} ]", curses.color_pair(5) | curses.A_BOLD)
        stdscr.addstr(3, 2, f"ACTIVE ROW: 0x{session.focused_addr:04X} [{session.focused_phase}b] | TRIES: ", curses.color_pair(1))
        stdscr.addstr(3, 34, "■ " * session.attempts, curses.color_pair(3) | curses.A_BOLD)
        stdscr.addstr(4, 2, "─" * 76, curses.A_DIM)

        grid_rows, hovered = session.get_grid_snapshot()
        for r, (str_l, str_r) in enumerate(grid_rows):
            y = 5 + r
            stdscr.addstr(y, 2, str_l, curses.color_pair(1))
            stdscr.addstr(y, 39, "│", curses.A_DIM)
            stdscr.addstr(y, 42, str_r, curses.color_pair(1))

        if hovered:
            stdscr.addstr(session.cur_y, hovered["start_x"], hovered["val"], curses.color_pair(2) | curses.A_BOLD)

        stdscr.addstr(13, 2, "─" * 76, curses.A_DIM)
        tok_info = f"CAPTURED TOKEN: \"{hovered['val']}\" (READY)" if hovered else "RAW STATIC / DELIMITER GLYPH"
        stdscr.addstr(15, 2, tok_info, curses.color_pair(1))
        stdscr.addstr(17, 2, f"> STATUS: {session.status_msg}", curses.color_pair(1) | curses.A_BOLD)
        stdscr.addstr(19, 2, "CONTROLS:", curses.A_BOLD)
        stdscr.addstr(20, 2, "  h / j / k / l : Move 1 char | Tab: Switch Column", curses.A_DIM)
        stdscr.addstr(21, 2, "  Shift+H / L   : Bit-Shift Row (-1b / +1b)", curses.color_pair(1))
        stdscr.addstr(22, 2, "  Enter / Click : Acquire Token | Backspace: Pop Token", curses.A_DIM)
        stdscr.addstr(23, 2, "  q / Esc       : Abort Session", curses.A_DIM)

        stdscr.move(session.cur_y, session.cur_x)
        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_MOUSE:
            try:
                _, mx, my, _, bstate = curses.getmouse()
                if 5 <= my <= 12 and (2 <= mx <= 36 or 42 <= mx <= 76):
                    session.set_cursor(my, mx)
                    if bstate & (curses.BUTTON1_CLICKED | curses.BUTTON1_DOUBLE_CLICKED):
                        key = ord("\n")
            except curses.error:
                pass

        if key in (ord("q"), 27):
            session.result = "ABORT"
            session.status_msg = "ABORTED BY OPERATOR."
        elif key in (ord("H"), curses.KEY_SLEFT):
            session.shift_row(-1)
        elif key in (ord("L"), curses.KEY_SRIGHT):
            session.shift_row(1)
        elif key in (ord("h"), curses.KEY_LEFT):
            session.move_cursor(0, -1)
        elif key in (ord("l"), curses.KEY_RIGHT):
            session.move_cursor(0, 1)
        elif key in (ord("k"), curses.KEY_UP):
            session.move_cursor(-1, 0)
        elif key in (ord("j"), curses.KEY_DOWN):
            session.move_cursor(1, 0)
        elif key in (ord("\t"), curses.KEY_BTAB):
            session.switch_column()
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            session.pop_token()
        elif key in (ord("\n"), curses.KEY_ENTER):
            session.acquire_token()

    outcome = None if session.result == "ABORT" else session.result
    return outcome, session.final_directive, session.status_msg


def launch_cli_probe(
    puzzle_id: str,
    json_path: str | Path | None = None,
    session_env: dict | None = None,
):
    session = DemodulatorSession(puzzle_id, json_path=json_path, session_env=session_env)
    return curses.wrapper(_run_tui, session)