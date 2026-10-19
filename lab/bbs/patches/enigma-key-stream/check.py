#!/usr/bin/env python3
"""Build an isolated ENiGMA keyboard experiment; never patch the stock fixture.

Run through tools/bbs-dev. The source checkout must already contain the pinned
upstream revision and its installed node_modules. No dependency downloads occur.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

REVISION = "6c25317168b762f7d9088a54d3f8295438827a0e"
CLIENT_SHA256 = "d66207f46af13ae4acb0ac430b1d0f2572a03722c79f4bcb7125dcd01e98e788"
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--revision", default=REVISION,
                        help="explicit expected upstream revision; default pinned lab revision")
    parser.add_argument("--client-sha256", default=CLIENT_SHA256,
                        help="explicit expected unmodified client hash; required for another revision")
    parser.add_argument("--output", type=Path, required=True,
                        help="new directory, refused if it already exists")
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    revision = subprocess.check_output(
        ["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    dirty = subprocess.check_output(
        ["git", "-C", str(source), "status", "--porcelain", "--untracked-files=no"], text=True)
    if revision != args.revision or dirty or sha(source / "core/client.js") != args.client_sha256:
        raise SystemExit("Refusing source: expected clean pinned ENiGMA revision/client")
    if (source / "core/key_stream.js").exists():
        raise SystemExit("Refusing source with an existing experimental key framer")
    if not (source / "node_modules/mocha/bin/mocha.js").is_file():
        raise SystemExit("Install the pinned fixture dependencies first")
    output.mkdir(parents=True, exist_ok=False)
    candidate = output / "candidate"
    candidate.mkdir()
    archive = output / "source.tar"
    with archive.open("wb") as handle:
        subprocess.run(["git", "-C", str(source), "archive", revision],
                       stdout=handle, check=True)
    with tarfile.open(archive) as handle:
        handle.extractall(candidate, filter="data")
    archive.unlink()
    # The candidate owns all source/runtime paths; reuse only installed modules.
    (candidate / "node_modules").symlink_to(source / "node_modules", target_is_directory=True)
    subprocess.run(["git", "init", "--quiet", str(candidate)], check=True)
    subprocess.run(["git", "apply", str(HERE / "client.patch")],
                   cwd=candidate, check=True)
    shutil.copyfile(HERE / "key_stream.js", candidate / "core/key_stream.js")
    report = {
        "upstream_revision": revision,
        "node": subprocess.check_output(["node", "--version"], text=True).strip(),
        "inputs": {p.name: sha(p) for p in sorted(HERE.iterdir()) if p.is_file()},
        "nix_lock_sha256": sha(HERE.parents[3] / "nix/flake.lock"),
        "upstream_package_lock_sha256": sha(source / "package-lock.json"),
        "stock_client_sha256": sha(source / "core/client.js"),
        "candidate_client_sha256": sha(candidate / "core/client.js"),
        "candidate_key_stream_sha256": sha(candidate / "core/key_stream.js"),
        "scope": "Isolated Client/editor experiment; not a running BBS or DOS/physical-modem compatibility claim",
        "tests": [],
    }
    upstream_tests = ["client_end", "view_controller_action_keys", "mltev", "fse_focus"]
    commands = [
        ("framer", ["node", str(HERE / "check_key_stream.js")], HERE),
        ("stock-counterexample", ["node", str(HERE / "check_client.js"), str(source)], HERE),
        ("candidate-client-editor", ["node", str(HERE / "check_client.js"), str(candidate), "--fixed", "--baseline", str(output / "stock-counterexample.log")], HERE),
        ("upstream-regressions", ["node", "node_modules/mocha/bin/mocha.js",
            *[f"test/{name}.test.js" for name in upstream_tests],
            "--require", "./test/setup.js", "--timeout", "5000", "--exit"], candidate),
    ]
    for name, command, cwd in commands:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=120)
        log = output / f"{name}.log"
        log.write_text(result.stdout + result.stderr)
        item = {"name": name, "exit_code": result.returncode, "log_sha256": sha(log)}
        if result.returncode == 0 and name != "upstream-regressions":
            item["result"] = json.loads(result.stdout.strip().splitlines()[-1])
        report["tests"].append(item)
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(f"{name}: exit {result.returncode}", flush=True)
        if result.returncode:
            raise SystemExit(f"Failed: see {log}")
    if sha(source / "core/client.js") != args.client_sha256:
        raise SystemExit("Stock client changed during experiment")
    report["passed"] = True
    report["stock_client_unchanged"] = True
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(output / "report.json")


if __name__ == "__main__":
    main()
