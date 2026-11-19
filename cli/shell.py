try:
    import readline  # noqa: F401
except ImportError:
    pass

from cli.tui import launch_cli_probe
from core.vfs import ShellSession, ensure_mit_license


def run_cli_shell():
    ensure_mit_license()
    shell = ShellSession()
    print(shell.banner())

    while True:
        try:
            raw_in = input(shell.prompt)
        except (EOFError, KeyboardInterrupt):
            print("\nSession terminated.")
            break

        out, action = shell.execute(raw_in)
        if out:
            print(out)

        if action:
            kind, arg = action
            if kind == "EXIT":
                break
            elif kind == "PROBE":
                outcome, directive, msg = launch_cli_probe(arg, session_env=shell.env)
                res_out, state = shell.handle_probe_result(outcome, directive, msg)
                print(res_out)
                if state == "GAME_OVER":
                    break