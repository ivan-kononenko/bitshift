#!/usr/bin/env python3
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="Technakraj Systems // Synapse-V Demodulator")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--cli", action="store_true", help="Launch local terminal shell (default)")
    mode.add_argument("--web", action="store_true", help="Launch FastAPI + xterm.js web server")
    parser.add_argument("--host", default="127.0.0.1", help="Web server bind host")
    parser.add_argument("--port", type=int, default=8085, help="Web server bind port")
    args = parser.parse_args()

    if args.web:
        try:
            import uvicorn
        except ImportError:
            print("[-] Missing web dependencies. Run: pip install -r requirements.txt", file=sys.stderr)
            sys.exit(1)
        uvicorn.run("web.server:app", host=args.host, port=args.port, reload=False)
    else:
        from cli.shell import run_cli_shell
        run_cli_shell()


if __name__ == "__main__":
    main()