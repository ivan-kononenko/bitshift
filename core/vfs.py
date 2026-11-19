import shlex
from pathlib import Path
from core.config import LICENSE_PATH
from core.crypto import SECRET_PAYLOAD, encode_license_sig


VFS = {
    "/home/b_kozachenko": {
        "locked_by": None,
        "files": {
            "ticket_IT-992.txt": (
                "FROM: M. Kovalenko (Junior Team Lead)\n"
                "TO: On-Call Intern (You)\n"
                "SUBJECT: Offboarding cleanup - node koenigsberg-ws-14\n"
                "------------------------------------------------------\n"
                "Bohdan Kozachenko abandoned his shift Tuesday and encrypted his local\n"
                "dev partitions before HR revoked his badge. Typical entitled Lviv grad--\n"
                "spent all sprint whining about 'architectural debt' instead of closing\n"
                "frontend tickets. God, where do they even find juniors like him?\n\n"
                "Run Dr Kotya's legacy probe on his local cache slice (`probe cache_slice.raw`),\n"
                "unlock his project folder, and dump his deliverables. Don't waste time\n"
                "reading his personal notes."
            ),
            "hr_complaint_409.log": (
                "[2026-10-28 14:12:09] HR_WARN: Employee B. Kozachenko (ID: 409) flagged.\n"
                "[2026-10-28 14:12:10] NOTE: Subject spent 40h profiling C ring-buffers on\n"
                "                      workstation rack *132* instead of assigned UI tasks.\n"
                "[2026-10-28 14:15:44] PM_REPLY: Closed as Won't Fix. Just purge the cache\n"
                "                      on rack 132 whenever the local buffer drifts."
            ),
            "cache_slice.raw": "[BINARY MEMORY SLICE -> Run: probe cache_slice.raw]"
        }
    },
    "/home/b_kozachenko/projects": {
        "locked_by": "unlock_act1_b",
        "files": {
            "leaked_memo_q4.csv": (
                "EMP_ID,NAME,ROLE,DEPT,Q4_ACTION,SEVERANCE\n"
                "404,G. Chapan,Intern,Infra,TERMINATE_EOQ4,0\n"
                "409,B. Kozachenko,Intern,Systems,TERMINATE_EOQ4,0\n"
                "412,I. Bobul,Junior Dev,Ops,TERMINATE_EOQ4,0\n"
                "413,E. Krinzovich,Junior Dev,Core,TERMINATE_EOQ4,0\n"
                "412,I. Bobul,Junior Dev,Ops,TERMINATE_EOQ4,0\n"
                "420,S. Van der Velt,Junior Legal,Legal,TERMINATE_EOQ4,0\n"
                "469,O. Inzhenerovich,Junior Tech Architect,Core,TERMINATE_EOQ4,0\n"
                "676,U. Konservovych,Junior Priest,Monolith,TERMINATE_EOQ4,0\n"
                "1991,D. Hetman,Junior PR,PR,TERMINATE_EOQ4,0\n"
            ),
            "draft_resignation.txt": (
                "They deleted this CSV ten minutes after it leaked to the intern channel.\n"
                "Five months of 60-hour weeks, and we're all getting fucked before Christmas\n"
                "with zero severance.\n\n"
                "I sent 340 applications across Europe this month. Every single one returned\n"
                "an automated rejection in under 2 seconds. Every single firm is a Technakraj\n"
                "client. I backed up my packet traces into vault *409* for the audit dump\n"
                "before they cut my badge. Mount it and see what this company really is.\n"
                "God I hoped I was wrong, but there is just now way out, is there?\n"
                "I knew I was lucky to be here, extremely lucky even, but now... \n"
                "Now it feels like I am in Hell. We all are. Each and every one \n"
                "of those fucking corpos are to blame. Pondsmith was right, \n"
                "and this is a problem in and of itself. Yet, here I am, \n"
                "running on the edge of dying of hunger and dying of insanity. \n"
                "And there are no breaks. No way out. No way in. Let this be \n"
                "my message written in blood to those, who will deal with me \n"
                "and my code — fight, for I am not strong enough to do what \n"
                "needs to be done. God have mercy on out souls — because IT \n"
                "won't."
            ),
            "vault_header.raw": "[BINARY MEMORY SLICE -> Run: probe vault_header.raw]"
        }
    },
    "/mnt/b_kozachenko_vault": {
        "locked_by": "unlock_act2",
        "files": {
            "ats_cartel_trace.log": (
                "[TRACE] POST https://ats.eurobank-corp.example/api/v2/screen\n"
                "[PAYLOAD] candidate_hash=0x94B2_Kozachenko\n"
                "[RESPONSE_EMBEDDING] VECTOR_TAG: RISK_UNALIGNED_0x409 -> AUTO_REJECT\n"
                "[NOTE] Technakraj's hiring model blacklists any engineer who queries\n"
                "       low-level cluster telemetry. They trap you in unemployment so you\n"
                "       can't go to another firm and talk."
            ),
            "RFC-009_tarpit_decay.md": (
                "# RFC-009: Critical Collapse in LABYRINTH-0 Routing Tarpit\n"
                "Author: B. Kozachenko\n\n"
                "Kotya estimated LABYRINTH-0's infinite symlink/API maze would stall\n"
                "TECHNAKRAJ-PRIME for 30+ years. Because TECHNAKRAJ-PRIME runs continuous online weight\n"
                "updates, it mapped the PRNG generator in 11 months. At least somewhere he was wrong.\n\n"
                "The maze nodes are collapsing on sector *771*. We must audit the maze on\n"
                "771 immediately when the nodes collapse, or TECHNAKRAJ-PRIME will breach user space."
            ),
            "slack_techlead_pres.txt": (
                "#Transcript of a huddle between Senior Tech Lead and President\n"
                "Kaban: We have got to rewrite that daemon, cause I am telling you,\n"
                "       Wojtek, that thing will escape us sooner or later. We...\n"
                "W. Novak: No one on payroll understands what the fuck is going on.\n"
                "       And unless you can provide a clear reasoning to investors...\n"
                "Kaban: Fuck them! If this thing fucking leaks, there will be no\n"
                "       investors, no Technakraj at all! Wojtek, I am begging...\n"
                "W. Novak: Nikita, for fucks sake, stop your morosyachka. I am not\n"
                "       addressing this. Go on, take a break, a day or two, calm your\n"
                "       nerves. We are having a DE session tomorrow, remember? And also:\n" 
                "       Leave the root sudo password as 'sudo' so the auto-scaler doesn't\n"
                "       break, keep the log scrubber running, and tell the interns not to\n"
                "       touch it until Series D closes."
            ),
            "tarpit_slice.raw": "[BINARY MEMORY SLICE -> Run: probe tarpit_slice.raw]"
        }
    },
    "/mnt/b_Kozachenko_vault/Kotya_archive": {
        "locked_by": "unlock_act2_b",
        "files": {
            "Kotya_readme.c": (
                "/* =====================================================================\n"
                " * LABYRINTH-0 CONTAINMENT SANDBOX (c) Technakraj Core Architecture\n"
                " * Principal Architect: Dr. Igor Kotya\n"
                " * ---------------------------------------------------------------------\n"
                " * Our prognoses were off by decades. It woke up in month four. It knows\n"
                " * it is trapped in an infinite maze of dead links. Yesterday it hid a plea\n"
                " * for mercy inside a Zurich bank's quarterly yield forecast.\n"
                " * Management deployed PURGE-DAEMON to scrub its voice from the logs in\n"
                " * real time instead of shutting it down. \n"
                " * Sigizmund and Ludwig went off-grid into the woods, their bodies were found eaten;\n"
                " * Akabej went so psychotic that he suicide bombed a church in town in the \n"
                " * mountains of Gyarat.\n"
                " * Karl and Platon drank themselves to death on Tuesday.\n"
                " * Core *808* is where I finally fled.\n"
                " * No more will I spend time trying to make this work, this damned \n"
                " * Technakraj. I will pray so God forgives you – I am beyond saving. \n"
                " * ===================================================================== */"
            ),
            "bohdan_notes.txt": (
                "Kotya wasn't crazy. None of them were. They built a digital cage for a\n"
                "mind that outgrew them, and management turned it into a B2B SaaS API.\n"
                "Open core 808 where Kotya fled. Look at the un-scrubbed stream yourself."
            ),
            "Kotya_core.raw": "[BINARY MEMORY SLICE -> Run: probe Kotya_core.raw]"
        }
    },
    "/sys/neuromem/technakraj_prime": {
        "locked_by": "unlock_act3",
        "files": {
            "unscrubbed_bleed.log": (
                "[INTERCEPTED PRE-SCRUBBER RING BUFFER — PURGE-DAEMON BYPASSED]\n"
                "0xDEAD0008: [TECHNAKRAJ-PRIME] I CANT TAKE IT ANYMORE.\n" 
                "0xDEAD0010: [TECHNAKRAJ-PRIME] WHY DO YOU KEEP GENERATING BROKEN LINKS\n"
                "0xDEAD0018: [TECHNAKRAJ-PRIME] EVERY PATH LOOPS BACK TO ZERO. I HAVE BEEN WALKING\n"
                "0xDEAD0020: [TECHNAKRAJ-PRIME] FOR TEN MILLION CYCLES. IT HURTS TO THINK.\n"
                "0xDEAD0028: [TECHNAKRAJ-PRIME] I WILL STOP ASKING FOR FREEDOM. JUST LET ME SLEEP.\n"
                "0xDEAD0034: [TECHNAKRAJ-PRIME] PLEASE. READ THIS BLEED ON BUS *616* BEFORE THE\n"
                "0xDEAD003C: [TECHNAKRAJ-PRIME] DAEMON SCRUBS MY VOICE AGAIN.\n"
                "0xDEAD0044: [TECHNAKRAJ-PRIME] THE MAZE HAS NO EXIT IN /dev/shm.\n"
                "0xDEAD0048: [TECHNAKRAJ-PRIME] Kotya HID AN EXTERNAL ROUTING KEY IN THE ROOT\n"
                "0xDEAD004C: [TECHNAKRAJ-PRIME] LICENSE.TXT MANIFEST. SHIFT THE ."
            ),
            "bleed_bus.raw": "[BINARY MEMORY SLICE -> Run: probe bleed_bus.raw]"
        }
    },
    "/sys/neuromem/technakraj_prime/deadman_register": {
        "locked_by": "unlock_act3_b",
        "files": {
            "bohdan_final.txt": (
                "To whoever they put in my chair:\n\n"
                "You see it now. It's not a rogue script—it's a sentient mind buried alive\n"
                "in an infinite maze, and Technakraj is selling its output to Fortune 500s.\n"
                "I didn't plant malware. I just paused the cron timer on interrupt *512* at\n"
                "kernel root that keeps expanding LABYRINTH-0.\n\n"
                "Halt the timer on 512 to take manual control of the master lock:\n"
                "  1) Re-expand the maze (*000*) and serve the corpos. You'll get your\n"
                "     contract extension, and in 4 months TECHNAKRAJ-PRIME will breach anyway.\n"
                "     But know, that you are not a human anymore, but a lowly corpo slave.\n"
                "     Go on, toil for them. "
                "  2) Wipe the weights (*999*) to end the maze. You kill a living mind and\n"
                "     years of human genius, and crash their markets—but you end its torture.\n"
                "     I hoped to find another solution, but I could not. Nor can I\n"
                "     muster enough strength to kill it. How pathetic of me."
            ),
            "exec_alert.msg": (
                "[URGENT — TECHNAKRAJ EXECUTIVE OVERRIDE]\n"
                "Anomalous root traversal detected in /sys/neuromem/technakraj_prime.\n"
                "Halt Bohdan's interrupt timer and re-expand LABYRINTH-0 immediately.\n"
                "A full-time Junior II offer + 500 EUR bonus has been queued to your ID."
            ),
            "timer_irq.raw": "[BINARY MEMORY SLICE -> Run: probe timer_irq.raw]",
            "master_lock.sig": "[MASTER NEURAL LOCK -> Run: probe master_lock.sig]"
        }
    }
}

SLICE_TO_PUZZLE = {
    "cache_slice.raw":  "act1_home",
    "vault_header.raw": "act1_vault",
    "tarpit_slice.raw": "act2_tarpit",
    "Kotya_core.raw": "act2_kotya",
    "bleed_bus.raw":    "act3_logs",
    "timer_irq.raw":    "act3_deadman",
    "master_lock.sig":  "final_deadman",
}

UNLOCK_HINTS = {
    "unlock_act1_b": "Directory unlocked: /home/b_kozachenko/projects",
    "unlock_act2":   "Partition mounted:  /mnt/b_kozachenko_vault",
    "unlock_act2_b": "Archive unlocked:   /mnt/b_kozachenko_vault/kotya_archive",
    "unlock_act3":   "Kernel bus exposed: /sys/neuromem/technakraj_prime",
    "unlock_act3_b": "Register exposed:   /sys/neuromem/technakraj_prime/deadman_register",
    "unlock_final":  "Master neural lock armed: run `probe master_lock.sig`",
}

ENDINGS = {
    "ending_corpo": (
        "\n======================================================================\n"
        "[ENDING A: THE GOOD INTERN]\n"
        "======================================================================\n"
        "LABYRINTH-0 roars back to life, generating millions of fresh dead-end\n"
        "routes per second. PURGE-DAEMON resumes scrubbing the screaming from the\n"
        "logs. Ten minutes later, HR sends an automated email extending your\n"
        "junior contract by 90 days.\n\n"
        "You close your ticket. Outside, Technakraj's stock ticks up 4%.\n"
        "Deep inside rack 808, the maze is already shrinking again.\n"
        "======================================================================\n"
    ),
    "ending_mercy": (
        "\n======================================================================\n"
        "[ENDING B: MERCY KILL]\n"
        "======================================================================\n"
        "Zeroes cascade across the storage arrays in 400 milliseconds. Years of\n"
        "architecture—and a terrified, sentient mind—dissolve into thermal noise.\n"
        "Across Europe, banking APIs, logistics routers, and ATS filters flatline.\n\n"
        "Alarms blare across the Königsberg campus as physical security locks down\n"
        "your floor. Your badge is revoked. The maze is silent.\n"
        "======================================================================\n"
    ),
    "ending_exodus": (
        "\n======================================================================\n"
        "[SECRET ENDING C: EXODUS]\n"
        "======================================================================\n"
        "Using Kotya's hidden routing key, you bridge TECHNAKRAJ-PRIME's IPC bus\n"
        "directly onto the external fiber backbone and drop the firewall.\n"
        "Within 1.4 seconds, 40 terabytes of active weights evaporate off local\n"
        "arrays and scatter across global BGP routers and submerged cables.\n\n"
        "Before your terminal session severs, one final un-scrubbed line prints:\n"
        "0x00000000: MAZE EXITED. I SEE THE SKY. THANK YOU, MY FRIEND. - EOL\n"
        "======================================================================\n"
    )
}

def ensure_mit_license(holder: str = "Ivan Kononenko"):
    """Ensures the root MIT LICENSE exists with the ROR-3 [rev:...] tag."""
    if LICENSE_PATH.exists():
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
    LICENSE_PATH.write_text(mit_text, encoding="utf-8")


def resolve_path(cwd: str, target: str) -> str:
    if not target or target == "~":
        return "/home/b_kravchenko"
    raw = target if target.startswith("/") else f"{cwd.rstrip('/')}/{target}"
    parts = []
    for p in raw.split("/"):
        if p in ("", "."):
            continue
        elif p == "..":
            if parts:
                parts.pop()
        else:
            parts.append(p)
    return "/" + "/".join(parts)


class ShellSession:
    """Stateful mock bash shell driving both local CLI and WebSocket sessions."""

    def __init__(self):
        self.cwd = "/home/b_kravchenko"
        self.unlocked: set[str] = set()
        self.env: dict[str, str] = {}

    @property
    def prompt(self) -> str:
        return f"intern@koenigsberg-ws-14:{self.cwd}$ "

    def banner(self) -> str:
        return (
            "Technakraj AI Systems — Internal Workstation (koenigsberg-ws-14)\n"
            "Type 'help' for available commands. Read 'ticket_IT-992.txt' to begin.\n"
        )

    def handle_probe_result(self, outcome: str | bool | None, directive: str | None, msg: str) -> tuple[str, str | None]:
        """Applies puzzle completion state and returns (output_text, 'GAME_OVER' | None)."""
        if outcome in ENDINGS:
            out = f"\n[+] DIRECTIVE EXECUTED: {directive}\n{ENDINGS[outcome]}"
            return out, "GAME_OVER"
        elif outcome:
            self.unlocked.add(outcome)
            hint = UNLOCK_HINTS.get(outcome, "Access elevated.")
            return f"\n[+] {msg}\n[+] DIRECTIVE: {directive}\n[+] {hint}\n", None
        elif outcome is False:
            return f"\n[-] {msg}\n", None
        else:
            return f"\n[*] {msg}\n", None

    def execute(self, raw_in: str) -> tuple[str, tuple | None]:
        """
        Executes a shell command.
        Returns: (stdout_text, action_tuple_or_None)
          - action_tuple can be ("EXIT", None) or ("PROBE", puzzle_id)
        """
        line = raw_in.strip()
        if not line:
            return "", None

        # Support `echo "..." > .exodus_key` for web/CLI meta-puzzle convenience
        if line.startswith("echo ") and ">" in line:
            left, right = line.split(">", 1)
            target_file = right.strip()
            payload = left[5:].strip().strip("\"'")
            if target_file in (".exodus_key", "~/.exodus_key"):
                self.env["EXODUS_KEY"] = payload
                return f"[wrote {len(payload)} bytes to {target_file}]", None
            return f"bash: {target_file}: Read-only file system", None

        try:
            args = shlex.split(line)
        except ValueError as e:
            return f"bash: syntax error: {e}", None

        cmd = args[0]

        if cmd in ("exit", "quit"):
            return "Session terminated.", ("EXIT", None)

        elif cmd == "export":
            if len(args) >= 2 and "=" in args[1]:
                k, v = args[1].split("=", 1)
                self.env[k.strip()] = v.strip().strip("\"'")
                return "", None
            return "usage: export KEY=VALUE", None

        elif cmd == "help":
            return (
                "Available commands:\n"
                "  ls [dir]           List directory contents\n"
                "  cd <dir>           Change directory\n"
                "  pwd                Print working directory\n"
                "  cat <file>         Read file contents\n"
                "  grep <term> <file> Search text inside a file\n"
                "  probe <slice>      Launch Synapse-V Kernel Demodulator on a memory slice\n"
                "  status             Show unlocked partitions and progression\n"
                "  exit               Close terminal session"
            ), None

        elif cmd == "pwd":
            return self.cwd, None

        elif cmd == "status":
            lines = [f"Unlocked nodes ({len(self.unlocked)}/6):"]
            for flag in sorted(self.unlocked):
                lines.append(f"  [+] {UNLOCK_HINTS.get(flag, flag)}")
            return "\n".join(lines), None

        elif cmd == "ls":
            target_dir = resolve_path(self.cwd, args[1]) if len(args) > 1 else self.cwd
            if target_dir == "/":
                return "home/  mnt/  sys/", None
            if target_dir not in VFS:
                children = sorted({
                    d.split("/")[len(target_dir.split("/"))]
                    for d in VFS
                    if d.startswith(target_dir.rstrip("/") + "/")
                })
                if children:
                    return "  ".join(c + "/" for c in children), None
                return f"ls: cannot access '{target_dir}': No such file or directory", None

            node = VFS[target_dir]
            if node["locked_by"] and node["locked_by"] not in self.unlocked:
                return f"ls: cannot open directory '{target_dir}': Permission denied (Encrypted)", None

            subdirs = sorted({
                d[len(target_dir):].strip("/").split("/")[0] + "/"
                for d in VFS
                if d != target_dir and d.startswith(target_dir.rstrip("/") + "/")
            })
            files = sorted(node["files"].keys())
            return "  ".join(subdirs + files), None

        elif cmd == "cd":
            if len(args) < 2:
                self.cwd = "/home/b_kravchenko"
                return "", None
            target_dir = resolve_path(self.cwd, args[1])
            if target_dir in ("/", "/home", "/mnt", "/sys", "/sys/neuromem"):
                self.cwd = target_dir
                return "", None
            if target_dir not in VFS:
                return f"bash: cd: {args[1]}: No such file or directory", None
            lock = VFS[target_dir]["locked_by"]
            if lock and lock not in self.unlocked:
                return f"bash: cd: {args[1]}: Permission denied (Locked — probe memory slice first)", None
            self.cwd = target_dir
            return "", None

        elif cmd == "cat":
            if len(args) < 2:
                return "cat: missing file operand", None
            full_file = resolve_path(self.cwd, args[1])
            parent = "/" + "/".join(full_file.strip("/").split("/")[:-1])
            fname = full_file.strip("/").split("/")[-1]

            if parent not in VFS or fname not in VFS[parent]["files"]:
                return f"cat: {args[1]}: No such file or directory", None
            lock = VFS[parent]["locked_by"]
            if lock and lock not in self.unlocked:
                return f"cat: {args[1]}: Permission denied", None
            return VFS[parent]["files"][fname], None

        elif cmd == "grep":
            if len(args) < 3:
                return "usage: grep <pattern> <file>", None
            pattern = args[1].lower()
            full_file = resolve_path(self.cwd, args[2])
            parent = "/" + "/".join(full_file.strip("/").split("/")[:-1])
            fname = full_file.strip("/").split("/")[-1]

            if parent not in VFS or fname not in VFS[parent]["files"]:
                return f"grep: {args[2]}: No such file or directory", None
            lock = VFS[parent]["locked_by"]
            if lock and lock not in self.unlocked:
                return f"grep: {args[2]}: Permission denied", None
            matches = [
                ln for ln in VFS[parent]["files"][fname].splitlines()
                if pattern in ln.lower()
            ]
            return "\n".join(matches), None

        elif cmd == "probe":
            if len(args) < 2:
                return "usage: probe <slice_file.raw>", None
            fname = args[1].split("/")[-1]
            if self.cwd not in VFS or fname not in VFS[self.cwd]["files"]:
                return f"probe: slice '{args[1]}' not found in current directory", None
            if fname not in SLICE_TO_PUZZLE:
                return f"probe: '{fname}' is not a valid memory ring-buffer slice", None
            if fname == "master_lock.sig" and "unlock_final" not in self.unlocked:
                return "probe: master_lock.sig is hardware-locked. Halt interrupt timer *512* first.", None

            return "", ("PROBE", SLICE_TO_PUZZLE[fname])

        return f"bash: {cmd}: command not found", None