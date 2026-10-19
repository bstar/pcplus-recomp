#!/usr/bin/env python3
"""Freeze the paired stock/patched ENiGMA DOS evidence without binaries or DBs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = "731418bde8f3264d5f6c987195eb54b20c86a2981259ea1c721ba252e3c9a776"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def source_audit(candidate, stock):
    assert not subprocess.check_output(
        ["git", "-C", str(stock), "status", "--porcelain", "--untracked-files=no"])
    entries = subprocess.check_output(
        ["git", "-C", str(stock), "ls-tree", "-r", "-z", "HEAD"]).split(b"\0")
    checked, different, tracked = 0, [], set()
    digest = hashlib.sha256()
    for entry in filter(None, entries):
        info, name = entry.split(b"\t", 1)
        mode, kind, _ = info.decode().split()
        if kind != "blob":
            continue
        name = os.fsdecode(name)
        tracked.add(name)
        left, right = candidate / name, stock / name
        data = os.readlink(left).encode() if mode == "120000" else left.read_bytes()
        original = os.readlink(right).encode() if mode == "120000" else right.read_bytes()
        if data != original:
            different.append(name)
        digest.update(name.encode() + b"\0" + hashlib.sha256(data).digest())
        checked += 1
    added_core = sorted(str(p.relative_to(candidate)) for p in (candidate / "core").rglob("*")
                        if p.is_file() and str(p.relative_to(candidate)) not in tracked)
    assert different == ["core/client.js"] and added_core == ["core/key_stream.js"]
    return dict(passed=True, tracked_files_compared=checked, different_tracked_files=different,
                added_core_files=added_core, candidate_path_and_content_digest=digest.hexdigest(),
                scope="Byte comparison to clean pinned checkout; Git checkout/archive EOL transforms retained; synthetic ignored runtime files excluded")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-root", type=Path, required=True)
    parser.add_argument("--patched-editor", required=True)
    parser.add_argument("--stock-editor", required=True)
    parser.add_argument("--combined", required=True)
    parser.add_argument("--failed", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    experiment = args.experiment_root.resolve()
    assert experiment.is_relative_to(ROOT / "build")
    candidate = experiment / "candidate"
    stock = ROOT / "build/bbs-lab/enigma/source"
    results = ROOT / "build/bbs-lab/results/enigma"
    patch, baseline, combined, failed = [results / label for label in
        (args.patched_editor, args.stock_editor, args.combined, args.failed)]
    p, b, z, f = [read(p / "result.json") for p in (patch, baseline, combined, failed)]
    pa, ba = [read(p / "semantic-audit.json") for p in (patch, baseline)]
    wrapper = combined.with_name(combined.name + "-wrapper")
    w = read(wrapper / "experiment.json")
    assert p["passed"] and b["passed"] and z["passed"] and z["standard_completion"]
    assert pa["passed"] and not ba["passed"] and not f["passed"]
    assert not ba["checks"]["home_moves_before_marker"]
    assert not ba["checks"]["insert_toggled_overtype"]
    assert ba["checks"]["no_post_saved"] and ba["checks"]["all_exercised_keys_emitted"]
    assert pa["authority"]["stock_server"] is False and ba["authority"]["stock_server"] is True
    assert p["keyboard_input"] == b["keyboard_input"] and p["serial"] == b["serial"]
    assert p["modem_packet_delay_ms"] == b["modem_packet_delay_ms"] == 0
    assert p["binary_sha256"] == b["binary_sha256"] == z["binary_sha256"] == RUNTIME
    assert w["passed"] and w["inputs_unchanged"]
    assert w["message_count_before"] == w["message_count_after"]
    for name, digest in w["input_hashes"].items():
        assert sha(ROOT / name) == digest, name
    assert z["checks"]["same_session_editor_then_transfer"] and z["checks"]["no_editor_post_saved"]
    assert z["checks"]["no_manual_transfer_keys"] and z["checks"]["posttransfer_actual_menu_input_response"]
    before, after = [read(experiment / name) for name in
        ("readback-before-second-transfer.json", "readback-after-transfer.json")]
    assert before["passed"] and after["passed"]
    assert after["file"]["download_count"] == before["file"]["download_count"] + 1
    assert sha(combined / "RECV/PCXTEST.BIN") == after["file"]["sha256"]
    assert (combined / "RECV/PCXTEST.BIN").stat().st_size == 11521
    upstream = subprocess.check_output(["git", "-C", str(stock), "rev-parse", "HEAD"], text=True).strip()
    assert upstream == "6c25317168b762f7d9088a54d3f8295438827a0e"
    tree = source_audit(candidate, stock)
    controls = {"zmodem-audit-controls.log": "Passed 88", "transfer-audit-controls.log": "10 declared",
                "server-log-controls.log": "Passed six"}
    for name, needle in controls.items():
        assert needle in (experiment / name).read_text()
    artifacts = {
        "patched-editor-result.json": patch / "result.json",
        "patched-editor-audit.json": patch / "semantic-audit.json",
        "stock-editor-result.json": baseline / "result.json",
        "stock-editor-audit.json": baseline / "semantic-audit.json",
        "stock-editor-experiment.json": baseline / "experiment.json",
        "combined-result.json": combined / "result.json",
        "combined-server-audit.json": combined / "server-session-audit.json",
        "combined-experiment.json": wrapper / "experiment.json",
        "failed-recipe-result.json": failed / "result.json",
        "readback-before.json": experiment / "readback-before-second-transfer.json",
        "readback-after.json": experiment / "readback-after-transfer.json",
        "writable-fds.json": experiment / "writable-fds.json",
        "instance.json": candidate / "instance.json",
    }
    manifest = {}
    for directory in (patch, baseline, combined, failed, wrapper):
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                manifest[str(path.relative_to(ROOT))] = sha(path)
    inputs = [ROOT / "standalone/record_key_stream_dos.py", ROOT / "nix/flake.lock"]
    inputs += [ROOT / "lab/bbs" / name for name in ["enigma_key_stream_readback.js", "check_enigma_log_boundary.py"]]
    assert not args.output.exists(), "Use a new frozen evidence directory"
    args.output.mkdir(parents=True)
    for name, path in artifacts.items():
        shutil.copyfile(path, args.output / name)
    for name in controls:
        shutil.copyfile(experiment / name, args.output / name)
    report = dict(passed=True, runtime_sha256=RUNTIME, upstream_revision=upstream,
                  source_tree=tree, source_inputs={str(p.relative_to(ROOT)): sha(p) for p in inputs},
                  paired_editor=dict(same_keyboard_recipe=True, same_DOS_binary=True,
                      same_serial_settings=True, modem_packet_delay_ms=0,
                      stock_passed=False, patched_passed=True),
                  official_download_count_before=before["file"]["download_count"],
                  official_download_count_after=after["file"]["download_count"],
                  failed_attempts=[dict(label=args.failed, reason="Message-menu Escape is not Quit; corrected recipe uses Q plus Enter")],
                  frozen_artifacts={p.name: sha(p) for p in sorted(args.output.iterdir()) if p.is_file()},
                  local_artifacts=manifest,
                  scope="Actual DOS paired stock/patched editor and patched same-session editor/discard/ZMODEM/menu. No physical modem or remote stock-server fix; all whole-application gates open")
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(args.output / "report.json")


if __name__ == "__main__":
    main()
