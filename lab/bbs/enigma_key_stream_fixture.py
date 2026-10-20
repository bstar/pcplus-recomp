#!/usr/bin/env python3
"""Own a separate loopback ENiGMA instance for the keyboard-parser experiment.

Use tools/bbs-dev. Setup accepts a successfully checked candidate, snapshots
only the synthetic stock fixture, and never shares writable runtime directories.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import sqlite3
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
STOCK = ROOT / "build/bbs-lab/enigma/source"
PORT = 23234


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def owned(path):
    path = path.resolve()
    assert path.is_relative_to(ROOT / "build") and path != STOCK
    return path


def setup(candidate):
    report = json.loads((candidate.parent / "report.json").read_text())
    assert report["passed"] and report["stock_client_unchanged"]
    assert sha(candidate / "core/client.js") == report["candidate_client_sha256"]
    assert sha(candidate / "core/key_stream.js") == report["candidate_key_stream_sha256"]
    assert sha(STOCK / "core/client.js") == report["stock_client_sha256"]
    assert not (candidate / "instance.json").exists(), "Instance already prepared"
    for directory in ("db", "logs", "drop", "file_base"):
        assert not (candidate / directory).exists(), "Refusing existing runtime state"
    with sqlite3.connect(f"file:{STOCK / 'db/user.sqlite3'}?mode=ro", uri=True) as db:
        users = {row[0] for row in db.execute("SELECT user_name FROM user")}
    assert users == {"locadmin", "loclab"}, "Only synthetic fixture users may be copied"
    # Source export contains tracked default config files; overlay local menus.
    shutil.copytree(STOCK / "config", candidate / "config", dirs_exist_ok=True)
    shutil.copytree(STOCK / "file_base", candidate / "file_base")
    helpers = candidate / "helpers"
    helpers.mkdir()
    shutil.copy2(STOCK.parent / "helpers/sexyz", helpers / "sexyz")
    snapshots = {}
    for source in sorted((STOCK / "db").rglob("*.sqlite3")):
        target = candidate / "db" / source.relative_to(STOCK / "db")
        target.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as original:
            with sqlite3.connect(target) as copy:
                original.backup(copy)
                assert copy.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        snapshots[str(source.relative_to(STOCK))] = sha(target)
    for directory in ("logs", "drop", "db/mods"):
        (candidate / directory).mkdir(parents=True, exist_ok=True)
    # Replace fixture paths in JSON; no stock runtime path survives this rewrite.
    config = json.loads((STOCK / "config/config.hjson").read_text())
    text = json.dumps(config).replace(str(STOCK.parent / "helpers"), str(helpers))
    text = text.replace(str(STOCK), str(candidate))
    config = json.loads(text)
    config["loginServers"]["telnet"].update(address="127.0.0.1", port=PORT)
    config["general"]["boardName"] = "LoC ENiGMA Keyboard Lab"
    config["general"]["prettyBoardName"] = "LoC ENiGMA Keyboard Lab"
    # Defaults resolve code/art and every mutable runtime path from this tree.
    assert "paths" not in config
    assert str(STOCK) not in json.dumps(config)
    (candidate / "config/config.hjson").write_text(json.dumps(config, indent=2) + "\n")
    metadata = dict(port=PORT, address="127.0.0.1", candidate=str(candidate),
                    upstream_revision=report["upstream_revision"],
                    client_sha256=sha(candidate / "core/client.js"),
                    key_stream_sha256=sha(candidate / "core/key_stream.js"),
                    stock_client_sha256=sha(STOCK / "core/client.js"),
                    config_sha256=sha(candidate / "config/config.hjson"),
                    database_snapshots=snapshots,
                    scope="Separate patched server; synthetic DB snapshots; no writable stock runtime shared")
    (candidate / "instance.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


def pid(candidate):
    try:
        value = int((candidate / "instance.pid").read_text())
        cmd = Path(f"/proc/{value}/cmdline").read_bytes()
        if str(candidate / "main.js").encode() in cmd:
            return value
    except (FileNotFoundError, ValueError, ProcessLookupError):
        pass
    return None


def verify_running(candidate):
    candidate = owned(candidate)
    metadata = json.loads((candidate / "instance.json").read_text())
    assert metadata["candidate"] == str(candidate)
    assert metadata["address"] == "127.0.0.1" and metadata["port"] == PORT
    assert sha(candidate / "core/client.js") == metadata["client_sha256"]
    assert sha(candidate / "core/key_stream.js") == metadata["key_stream_sha256"]
    assert sha(candidate / "config/config.hjson") == metadata["config_sha256"]
    assert pid(candidate), "Owned experimental server is not running"
    return candidate / "logs/enigma-bbs.log"


def start(candidate, private_tmp=False, cleanup_fault=False):
    assert not pid(candidate), "Owned instance already running"
    metadata = json.loads((candidate / "instance.json").read_text())
    assert sha(candidate / "core/client.js") == metadata["client_sha256"]
    assert sha(candidate / "core/key_stream.js") == metadata["key_stream_sha256"]
    assert sha(candidate / "config/config.hjson") == metadata["config_sha256"]
    executable = shutil.which("node")
    assert executable and str(Path(executable).resolve()).startswith("/nix/store/")
    environment = dict(os.environ)
    if private_tmp:
        temporary = candidate / 'runtime-tmp'
        temporary.mkdir(exist_ok=True)
        assert not temporary.is_symlink() and temporary.resolve().parent == candidate
        environment.update(TMPDIR=str(temporary), TMP=str(temporary), TEMP=str(temporary))
    if cleanup_fault:
        assert private_tmp and not environment.get('NODE_OPTIONS')
        fixture = json.loads((candidate / 'search-instance.json').read_text())
        assert fixture.get('transfer_owner_experiment'), 'Fault injection requires the explicit owner candidate'
        report = candidate / 'cleanup-fault-events.jsonl'
        assert not report.exists(), 'Preserve earlier fault evidence; use a fresh fixture'
        preload = ROOT / 'lab/bbs/patches/enigma-transfer-owner/fault-once.js'
        environment.update(PCPLUS_ENIGMA_FAULT_LOG=str(report), NODE_OPTIONS='--require ' + str(preload))
    with socket.socket() as check:
        check.bind(("127.0.0.1", PORT))
    with (candidate / "instance.log").open("ab") as log:
        process = subprocess.Popen([executable, str(candidate / "main.js")], cwd=candidate,
                                   stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                   start_new_session=True, env=environment)
    (candidate / "instance.pid").write_text(str(process.pid) + "\n")
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        assert process.poll() is None, "Instance exited; inspect instance.log"
        try:
            with socket.create_connection(("127.0.0.1", PORT), timeout=.1):
                print(f"Owned patched ENiGMA pid {process.pid}, 127.0.0.1:{PORT}")
                return
        except OSError:
            time.sleep(.1)
    raise TimeoutError("Instance did not listen; inspect instance.log")


def stop(candidate):
    value = pid(candidate)
    if value:
        os.kill(value, signal.SIGTERM)
        for _ in range(50):
            if not pid(candidate):
                break
            time.sleep(.1)
        if pid(candidate):
            os.kill(value, signal.SIGKILL)
    (candidate / "instance.pid").unlink(missing_ok=True)
    print("Stopped owned patched instance")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["setup", "start", "stop"])
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--private-tmp", action="store_true", help="Start with temporary files inside the owned candidate")
    parser.add_argument("--cleanup-fault-once", action="store_true", help="Model one EACCES deletion error on the isolated explicit-owner candidate")
    args = parser.parse_args()
    assert not args.private_tmp or args.action == 'start'
    assert not args.cleanup_fault_once or (args.action == 'start' and args.private_tmp)
    if args.action == 'start':start(owned(args.candidate), args.private_tmp, args.cleanup_fault_once)
    else:globals()[args.action](owned(args.candidate))
