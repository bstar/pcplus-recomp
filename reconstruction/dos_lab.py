#!/usr/bin/env python3
"""Test private PCPlus copies in DOSBox-X with loopback serial and real key events."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import threading
import time

ROOT = Path(__file__).resolve().parents[1]


def run(variant, baud, cycles, transport):
    suffix = "-modem" if transport == "modem" else ""
    output = ROOT / f"reconstruction/lab/{variant}-{baud}-{cycles}{suffix}"
    output.mkdir(parents=True, exist_ok=True)
    drive = output / "drive"
    if drive.exists():
        shutil.rmtree(drive)
    shutil.copytree(ROOT / "analysis/pcplus-install", drive)
    binary = (ROOT / "analysis/pcplus-originals/PCPLUS-main-2.01.EXE" if variant == "baseline"
              else ROOT / "reconstruction/dist/tech-net-candidate/PCPLUS.EXE")
    input_sha256 = hashlib.sha256(binary.read_bytes()).hexdigest()
    shutil.copy2(binary, drive / "PCPLUS.EXE")
    script = f'''proc main
   set port com1
   set baudrate {baud}
   set databits 8
   set parity none
   set stopbits 1
   emulate ansi
   transmit "LOC-READY^M"
endproc
'''
    (drive / "RETURNED.TXT").unlink(missing_ok=True)
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    server.settimeout(30)
    port = server.getsockname()[1]
    if transport == "modem":
        commands = (f'   transmit "ATZ^M"\n   waitfor "OK" 3\n'
                    f'   transmit "ATNET1^M"\n   waitfor "OK" 3\n'
                    f'   transmit "ATDT127.0.0.1:{port}^M"\n   waitfor "CONNECT" 5\n')
        script = script.replace('   transmit "LOC-READY^M"', commands + '   transmit "LOC-READY^M"')
    (drive / "PROFILE.ASP").write_bytes(script.replace("\n", "\r\n").encode("ascii"))
    events, checks = [], {}
    stopping = threading.Event()
    started = time.monotonic()

    def event(kind, **fields):
        events.append({"event": kind, "seconds": round(time.monotonic() - started, 4), **fields})

    def peer():
        try:
            connection, _ = server.accept()
            event("connected")
            with connection:
                connection.settimeout(0.1)
                pending = bytearray()
                if transport == "modem":
                    negotiation = (b"\xff\xfb\x01\xff\xfb\x03"
                                   b"\xff\xfd\x00\xff\xfd\x01\xff\xfd\x03")
                    event("serial-tx", hex=negotiation.hex())
                    connection.sendall(negotiation)

                def receive(expected, seconds):
                    deadline = time.monotonic() + seconds
                    while not stopping.is_set() and time.monotonic() < deadline:
                        if expected in pending:
                            at = pending.index(expected) + len(expected)
                            del pending[:at]
                            return True
                        try:
                            data = connection.recv(4096)
                            if not data:
                                return False
                            pending.extend(data)
                            event("serial-rx", hex=data.hex())
                        except socket.timeout:
                            pass
                    return False

                def send(data):
                    event("serial-tx", hex=data.hex())
                    connection.sendall(data)

                checks["startup_script_ready"] = receive(b"LOC-READY\r", 15)
                if not checks["startup_script_ready"]:
                    return
                if transport == "modem":
                    # DOSBox-X consumes server WILL options without replying.
                    # Its documented DO handlers answer binary, echo and SGA.
                    receive(b"\xff\xfb\x03", 2)
                    wire = b"".join(bytes.fromhex(e["hex"]) for e in events if e["event"] == "serial-rx")
                    checks["telnet_negotiated"] = all(reply in wire for reply in
                        (b"\xff\xfb\x00", b"\xff\xfc\x01", b"\xff\xfb\x03"))
                send(b"\x1b[2J\x1b[H\x1b[5n")
                checks["status_reply"] = receive(b"\x1b[0n", 2)
                send(b"\x1b[10;20H\x1b[6n")
                checks["cursor_reply"] = receive(b"\x1b[10;20R", 2)
                send(b"\x1b[;4q")
                time.sleep(0.1)
                send(b"\x1b[5n")
                immediate = receive(b"\x1b[0n", 0.7)
                checks["q_followup_response_present"] = immediate
                checks["q_behavior_matches_variant"] = immediate == (variant == "candidate")
                if not immediate:
                    # Release unwanted baseline payload reads instead of waiting forty seconds.
                    send(b"." * 20)
                    time.sleep(0.15)
                    send(b"\x1b[5n")
                    checks["recovered_after_q_payload"] = receive(b"\x1b[0n", 2)
                checks["typed_key"] = receive(b"k", 6)
                checks["arrow_up"] = receive(b"\x1b[A", 2)
                checks["arrow_right"] = receive(b"\x1b[C", 2)
                while not stopping.is_set():
                    try:
                        data = connection.recv(4096)
                        if not data:
                            break
                        event("serial-rx", hex=data.hex())
                    except socket.timeout:
                        pass
        except OSError as error:
            event("peer-error", message=str(error))

    thread = threading.Thread(target=peer, daemon=True)
    thread.start()
    serial = (f"nullmodem server:127.0.0.1 port:{port} transparent:1 rxdelay:200 txdelay:1"
              if transport == "nullmodem" else "modem listenport:0")
    config = f'''[sdl]
fullscreen=false
output=surface
[dosbox]
machine=svga_s3
memsize=8
[cpu]
core=normal
cputype=386
cycles=fixed {cycles}
[mixer]
nosound=true
[serial]
serial1={serial}
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{drive}"
c:
ASPCOMP PROFILE.ASP > COMPILE.TXT
ADDKEY p750 enter p3250 k p200 up p200 right p6000 a-x p500 y enter
PCPLUS
echo RETURNED>RETURNED.TXT
exit
'''
    (output / "dosbox.conf").write_text(config)
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy")
    with (output / "dosbox.log").open("w") as log:
        process = subprocess.Popen(["dosbox-x", "-fastlaunch", "-nogui", "-conf", str(output / "dosbox.conf")],
                                   cwd=output, env=env, stdout=log, stderr=log)
        try:
            returncode = process.wait(timeout=35)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                returncode = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                returncode = process.wait()
            event("deadline")
    stopping.set()
    server.close()
    thread.join(timeout=2)
    compile_log = (drive / "COMPILE.TXT").read_text(encoding="cp437") if (drive / "COMPILE.TXT").exists() else ""
    checks["aspect_compiled"] = "Script file successfully compiled!" in compile_log
    checks["returned_to_dos"] = (drive / "RETURNED.TXT").exists() and returncode == 0
    required = ("startup_script_ready", "status_reply", "cursor_reply", "q_behavior_matches_variant",
                "typed_key", "arrow_up", "arrow_right", "aspect_compiled", "returned_to_dos")
    if transport == "modem":
        required += ("telnet_negotiated",)
    result = {"variant": variant, "baud": baud, "cycles": cycles, "transport": transport, "returncode": returncode,
              "input_executable_sha256": input_sha256,
              "seconds": round(time.monotonic() - started, 3), "checks": checks,
              "passed": all(checks.get(k, False) for k in required), "events": events,
              "scope": "Complete DOS application, built-in DOS, emulated UART and keyboard, loopback TCP peer; no Wi-Fi modem or public BBS."}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "events"}, indent=2), flush=True)
    return result["passed"]


def locked_run(variant, baud, cycles, transport):
    suffix = "-modem" if transport == "modem" else ""
    directory = ROOT / f"reconstruction/lab/{variant}-{baud}-{cycles}{suffix}"
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / ".lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit(f"This lab case is already running: {directory}")
        return run(variant, baud, cycles, transport)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", choices=["baseline", "candidate", "both"], default="both")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--cycles", type=int, default=6000)
    parser.add_argument("--transport", choices=["nullmodem", "modem"], default="nullmodem")
    args = parser.parse_args()
    variants = ["baseline", "candidate"] if args.variant == "both" else [args.variant]
    outcomes = [locked_run(v, args.baud, args.cycles, args.transport) for v in variants]
    raise SystemExit(0 if all(outcomes) else 1)
