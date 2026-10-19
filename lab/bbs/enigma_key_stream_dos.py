#!/usr/bin/env python3
"""Run actual DOS editor/transfer checks against the isolated patched BBS.

Run through tools/dev after preparing/starting enigma_key_stream_fixture.py
through tools/bbs-dev. All drafts and files belong to the synthetic local lab.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

from enigma_key_stream_fixture import ROOT, STOCK, PORT, owned, verify_running


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def recipe(mode):
    canonical = json.loads((ROOT / "lab/bbs/editor-recipes.json").read_text())
    keys = canonical["enigma_unsaved"]["keyboard_input"]
    if mode == "editor-transfer":
        # The log proves User Stats follows declining newscan; the second N
        # on that display is redundant. Keep its first six-second display wait.
        prefix = keys[:keys.index("K E Y T E S T")].replace(
            "n p6000 n p3000 enter", "n p6000 enter")
        keys = prefix + (
            "K enter p1500 A home H ins Z escape p500 right enter p1500 Q enter p1000 "
            "F enter p2000 S enter p1500 P C X T E S T . B I N enter p1500 enter "
            "p2000 t p1000 q p1000 escape p1000 D enter p1500 a p1000 enter p1000 "
            "p30000 enter p2000 S enter p1500 P C X T E S T . B I N enter p1500 enter"
        )
    assert len("ADDKEY p1000 " + keys + " p3000 a-x") < 500
    return keys


def messages(candidate):
    with sqlite3.connect(f"file:{candidate / 'db/message.sqlite3'}?mode=ro", uri=True) as db:
        return db.execute("SELECT COUNT(*) FROM message").fetchone()[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["editor", "editor-transfer"])
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    assert args.label and all(c.isalnum() or c in "-_" for c in args.label)
    candidate = owned(args.candidate)
    server_log = verify_running(candidate)
    output = ROOT / "build/bbs-lab/results/enigma" / args.label
    output.mkdir(parents=True, exist_ok=False)
    # Keep wrapper evidence beside, not inside, the strict transfer output dir.
    wrapper = output.with_name(args.label + "-wrapper")
    wrapper.mkdir(exist_ok=False)
    output.rmdir()
    inputs = [ROOT / "build/terminal/TERMINAL.EXE", STOCK / "core/client.js",
              STOCK / "config/config.hjson", candidate / "core/client.js",
              candidate / "core/key_stream.js", candidate / "config/config.hjson",
              candidate / "helpers/sexyz", candidate / "file_base/pcplus_transfer/PCXTEST.BIN"]
    inputs += [ROOT / "lab/bbs" / name for name in [
        "enigma_key_stream_dos.py", "enigma_key_stream_fixture.py", "editor_dos_probe.py",
        "test_dos.py", "check_editor_dos.py", "test_transfer_dos.py", "test_zmodem_dos.py",
        "modem.py", "audit_zmodem.py", "editor-recipes.json"]]
    before = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    message_count = messages(candidate)
    binary = ROOT / "build/terminal/TERMINAL.EXE"
    keys = recipe(args.mode)
    if args.mode == "editor":
        command = [sys.executable, "lab/bbs/editor_dos_probe.py", str(binary), "enigma",
                   "--port", str(PORT), "--server-log", str(server_log), "--label", args.label,
                   "--com", "2", "--baud", "19200", "--flow", "HARD", "--dial-fixture",
                   "--timeout", "160", "--wait", "2", "--keys", keys]
    else:
        command = [sys.executable, "lab/bbs/test_zmodem_dos.py", "enigma", "--port", str(PORT),
                   "--server-instance", str(candidate / "instance.json"), "--editor-first",
                   "--label", args.label, "--sha256", sha(binary), "--mode", "download",
                   "--file", "PCXTEST.BIN=" + str(candidate / "file_base/pcplus_transfer/PCXTEST.BIN"),
                   "--auto-download", "--dial-fixture", "--keys", keys,
                   "--start-input-hex", "504358544553542e42494e0d", "--post-input-hex", "530d",
                   "--post-menu", "PCXTEST.BIN ", "--post-menu", "11.25 ", "--post-menu", "KB ",
                   "--timeout", "200"]
    (wrapper / "command.json").write_text(json.dumps(command, indent=2) + "\n")
    with (wrapper / "harness.log").open("w") as log:
        code = subprocess.call(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    audit_code = None
    if args.mode == "editor" and (output / "result.json").exists():
        with (wrapper / "editor-audit.log").open("w") as log:
            audit_code = subprocess.call([sys.executable, "lab/bbs/check_editor_dos.py", "enigma",
                "--label", args.label, "--disconnect-unsaved"], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    after = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    result = dict(passed=code == 0 and audit_code in (None, 0) and before == after
                  and messages(candidate) == message_count, mode=args.mode, harness_exit=code,
                  editor_audit_exit=audit_code, input_hashes=before, inputs_unchanged=before == after,
                  message_count_before=message_count, message_count_after=messages(candidate),
                  modem_packet_delay_ms=0, endpoint=f"127.0.0.1:{PORT}",
                  scope="Actual DOS against isolated patched ENiGMA; immediate byte-transparent modem; no physical modem or remote stock-server claim")
    (wrapper / "experiment.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
