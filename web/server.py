from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, PlainTextResponse
from core.config import LICENSE_PATH
from core.demodulator import DemodulatorSession
from core.vfs import ShellSession, ensure_mit_license

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Technakraj Systems // Synapse-V Web Terminal")


@app.on_event("startup")
def startup_event():
    ensure_mit_license()


@app.get("/")
async def serve_index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/LICENSE")
async def serve_license():
    ensure_mit_license()
    return PlainTextResponse(LICENSE_PATH.read_text(encoding="utf-8"))


def render_ansi_frame(session: DemodulatorSession) -> str:
    """Renders the 80x24 DemodulatorSession state into VT100/ANSI escape codes."""
    cfg = session.config
    buf = ["\x1b[?25l\x1b[H\x1b[2J"]  # Hide cursor, home, clear screen

    # Header (Rows 1..5 in 1-based ANSI coordinates)
    buf.append(
        "\x1b[1;3H\x1b[1;36m=== [TECHNAKRAJ SYSTEMS // SYNAPSE-V KERNEL PROBE] ===\x1b[0m"
    )
    buf.append(
        f"\x1b[2;3H\x1b[2;32m{cfg['header_sub'][:52]} | KEY:0x{session.session_key:08X}\x1b[0m"
    )
    buf.append(
        f"\x1b[3;3H\x1b[32mPAYLOAD BUFFER : \x1b[1;33m[ {' '.join(session.assembled)} ]\x1b[0m"
    )
    tries_bar = "■ " * session.attempts
    buf.append(
        f"\x1b[4;3H\x1b[32mACTIVE ROW: 0x{session.focused_addr:04X} [{session.focused_phase}b] | TRIES: "
        f"\x1b[1;31m{tries_bar}\x1b[0m"
    )
    buf.append(f"\x1b[5;3H\x1b[2;32m{'─' * 76}\x1b[0m")

    # Dual-Column Grid (Rows 6..13 in 1-based ANSI)
    grid_rows, hovered = session.get_grid_snapshot()
    for r, (str_l, str_r) in enumerate(grid_rows):
        y = 6 + r
        buf.append(
            f"\x1b[{y};3H\x1b[32m{str_l}\x1b[0m"
            f"\x1b[{y};40H\x1b[2;32m│\x1b[0m"
            f"\x1b[{y};43H\x1b[32m{str_r}\x1b[0m"
        )

    # Reverse-video highlight for hovered token
    if hovered:
        hy = session.cur_y + 1
        hx = hovered["start_x"] + 1
        buf.append(f"\x1b[{hy};{hx}H\x1b[1;30;42m{hovered['val']}\x1b[0m")

    # Footer (Rows 14..24 in 1-based ANSI)
    buf.append(f"\x1b[14;3H\x1b[2;32m{'─' * 76}\x1b[0m")
    tok_info = (
        f"CAPTURED TOKEN: \"{hovered['val']}\" (READY)"
        if hovered
        else "RAW STATIC / DELIMITER GLYPH"
    )
    buf.append(f"\x1b[16;3H\x1b[32m{tok_info}\x1b[0m")
    buf.append(f"\x1b[18;3H\x1b[1;32m> STATUS: {session.status_msg}\x1b[0m")
    buf.append("\x1b[20;3H\x1b[1;32mCONTROLS:\x1b[0m")
    buf.append("\x1b[21;3H\x1b[2;32m  h / j / k / l : Move 1 char | Tab: Switch Column\x1b[0m")
    buf.append("\x1b[22;3H\x1b[32m  Shift+H / L   : Bit-Shift Row (-1b / +1b)\x1b[0m")
    buf.append("\x1b[23;3H\x1b[2;32m  Enter / Click : Acquire Token | Backspace: Pop Token\x1b[0m")
    buf.append("\x1b[24;3H\x1b[2;32m  q / Esc       : Abort Session\x1b[0m")

    # Position visible block cursor
    cy = session.cur_y + 1
    cx = session.cur_x + 1
    buf.append(f"\x1b[{cy};{cx}H\x1b[?25h")
    return "".join(buf)


def parse_tui_input(session: DemodulatorSession, data: str):
    """Translates raw xterm.js keystrokes and SGR mouse sequences into DemodulatorSession actions."""
    # SGR mouse event: \x1b[<button;col;rowM or m
    if data.startswith("\x1b[<"):
        try:
            body = data[3:]
            is_press = body.endswith("M")
            parts = body[:-1].split(";")
            btn, col, row = int(parts[0]), int(parts[1]), int(parts[2])
            x, y = col - 1, row - 1
            if 5 <= y <= 12 and (2 <= x <= 36 or 42 <= x <= 76):
                session.set_cursor(y, x)
                if is_press and btn == 0:
                    session.acquire_token()
        except (ValueError, IndexError):
            pass
        return

    if data in ("q", "\x1b"):
        session.result = "ABORT"
        session.status_msg = "ABORTED BY OPERATOR."
    elif data in ("H", "\x1b[1;2D"):
        session.shift_row(-1)
    elif data in ("L", "\x1b[1;2C"):
        session.shift_row(1)
    elif data in ("h", "\x1b[D"):
        session.move_cursor(0, -1)
    elif data in ("l", "\x1b[C"):
        session.move_cursor(0, 1)
    elif data in ("k", "\x1b[A"):
        session.move_cursor(-1, 0)
    elif data in ("j", "\x1b[B"):
        session.move_cursor(1, 0)
    elif data in ("\t", "\x1b[Z"):
        session.switch_column()
    elif data in ("\x7f", "\b"):
        session.pop_token()
    elif data in ("\r", "\n"):
        session.acquire_token()


@app.websocket("/ws")
async def terminal_ws(ws: WebSocket):
    await ws.accept()
    shell = ShellSession()
    probe: DemodulatorSession | None = None
    line_buf = ""

    async def write_line(text: str = ""):
        formatted = text.replace("\n", "\r\n")
        await ws.send_text(f"{formatted}\r\n")

    await write_line(shell.banner())
    await ws.send_text(shell.prompt)

    try:
        while True:
            data = await ws.receive_text()

            # Mode 1: Active TUI Probe
            if probe is not None:
                parse_tui_input(probe, data)
                if probe.result is None:
                    await ws.send_text(render_ansi_frame(probe))
                else:
                    outcome = None if probe.result == "ABORT" else probe.result
                    res_out, state = shell.handle_probe_result(
                        outcome, probe.final_directive, probe.status_msg
                    )
                    probe = None
                    # Exit alternate screen buffer and print outcome
                    await ws.send_text("\x1b[?1049l\x1b[?25h")
                    await write_line(res_out)
                    if state == "GAME_OVER":
                        await ws.close()
                        return
                    await ws.send_text(shell.prompt)
                continue

            # Mode 2: Interactive Bash Shell line editor
            for ch in data:
                if ch in ("\r", "\n"):
                    await ws.send_text("\r\n")
                    cmd_str = line_buf
                    line_buf = ""

                    out, action = shell.execute(cmd_str)
                    if out:
                        await write_line(out)

                    if action:
                        kind, arg = action
                        if kind == "EXIT":
                            await ws.close()
                            return
                        elif kind == "PROBE":
                            probe = DemodulatorSession(arg, session_env=shell.env)
                            # Enter alternate screen buffer and render initial frame
                            await ws.send_text("\x1b[?1049h" + render_ansi_frame(probe))
                            break
                    await ws.send_text(shell.prompt)

                elif ch in ("\x7f", "\b"):
                    if line_buf:
                        line_buf = line_buf[:-1]
                        await ws.send_text("\b \b")

                elif ch == "\x03":  # Ctrl+C
                    line_buf = ""
                    await ws.send_text(f"^C\r\n{shell.prompt}")

                elif ord(ch) >= 32:
                    line_buf += ch
                    await ws.send_text(ch)

    except WebSocketDisconnect:
        pass