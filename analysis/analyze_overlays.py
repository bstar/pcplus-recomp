#!/usr/bin/env python3
"""Export overlay functions from explicitly synthetic REA analysis contexts."""
import json
import argparse
import datetime
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--entry-anchors", action="store_true")
args = parser.parse_args()
image_dir = ROOT / ("pcplus-overlay-entry-images" if args.entry_anchors else "pcplus-overlay-images")
prefix = "pcplus-overlay-anchored" if args.entry_anchors else "pcplus-overlay"
manifest = json.loads((image_dir / "manifest.json").read_text())
original_manifest = json.loads((ROOT / "pcplus-overlays/manifest.json").read_text())
results = []
for image in manifest["images"]:
    number = image["overlay"]
    output = ROOT / f"{prefix}-{number:02d}"
    output.mkdir(exist_ok=True)
    complete = False
    if all((output / name).exists() for name in
           ("close_binary.json", "open_binary.json", "failures.json", "evidence-bundle.json")):
        response = json.loads((output / "open_binary.json").read_text())
        opened = response.get("structuredContent") or json.loads(response["content"][0]["text"])
        complete = (opened.get("result", {}).get("sha256") == image["sha256"]
                    and not json.loads((output / "failures.json").read_text()))
    if not complete:
        functions = output / "functions"
        if functions.exists():
            stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            functions.rename(output / f"functions-before-{stamp}")
        with (output / "run.log").open("w") as log:
            result = subprocess.run([
                sys.executable, str(ROOT / "rea_mcp.py"),
                str(image_dir / image["file"]), str(output),
                "--decompile-all", "--region", hex(image["region_start"]), hex(image["region_end"]),
            ], stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            print(f"Overlay {number}: failed; see {output / 'run.log'}", flush=True)
            results.append({"overlay": number, "status": "failed"})
            continue
    functions = list((output / "functions").glob("*.c"))
    failures = json.loads((output / "failures.json").read_text())
    response = json.loads((output / "list_procedures.json").read_text())
    evidence = response.get("structuredContent") or json.loads(response["content"][0]["text"])
    discovered = {int(p["address"], 16) for p in evidence["normalized_result"]}
    expected = {0x10000 + entry for entry in original_manifest["overlays"][number - 1]["entrypoints"]}
    results.append({"overlay": number, "status": "analyzed", "pseudocode_functions": len(functions),
                    "failed_operations": len(failures), "synthetic_image_sha256": image["sha256"],
                    "known_export_entrypoints": len(expected),
                    "discovered_export_entrypoints": len(expected & discovered),
                    "missing_export_entrypoints": [hex(a) for a in sorted(expected - discovered)]})
    print(f"Overlay {number:02d}: {len(functions)} pseudocode functions; "
          f"{len(expected & discovered)}/{len(expected)} known entries; {len(failures)} failed operations", flush=True)
(ROOT / f"{prefix}-summary.json").write_text(json.dumps(results, indent=2) + "\n")
if any(r["status"] == "failed" or r.get("failed_operations") for r in results):
    sys.exit(1)
