#!/usr/bin/env python3
"""Run the Nix-provided REA stdio MCP server and retain its full responses.

No registration changes, DOS execution, or writes to the supplied binary.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def decode(result):
    if "structuredContent" in result:
        return result["structuredContent"]
    for block in result.get("content", []):
        if block.get("type") == "text":
            try:
                return json.loads(block["text"])
            except json.JSONDecodeError:
                pass
    return result


class ReaMcp:
    def __init__(self, output):
        self.output = output
        self.log = (output / "server-stderr.log").open("w")
        env = dict(os.environ, REA_GHIDRA_STARTUP_TIMEOUT_MS="300000")
        self.process = subprocess.Popen(
            ["rea", "mcp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=self.log, text=True, env=env,
        )
        self.sequence = 0
        self.request("initialize", {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "pcplus-analysis", "version": "1.0"},
        })
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def send(self, message):
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def request(self, method, params):
        self.sequence += 1
        request_id = self.sequence
        self.send({"jsonrpc": "2.0", "id": request_id,
                   "method": method, "params": params})
        while True:
            line = self.process.stdout.readline()
            if not line:
                raise RuntimeError("REA exited; see server-stderr.log")
            reply = json.loads(line)
            if reply.get("id") == request_id:
                if "error" in reply:
                    raise RuntimeError(reply["error"])
                return reply["result"]

    def call(self, name, arguments=None, label=None):
        result = self.request("tools/call", {
            "name": name, "arguments": arguments or {},
        })
        path = self.output / ((label or name) + ".json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2) + "\n")
        decoded = decode(result)
        if result.get("isError") or "error" in decoded:
            raise RuntimeError(f"{name}: {json.dumps(decoded)}")
        return decoded

    def close(self):
        try:
            self.call("close_binary")
        finally:
            self.process.stdin.close()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                self.process.wait(timeout=10)
            self.log.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("binary", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--decompile-all", action="store_true")
    parser.add_argument("--region", nargs=2, type=lambda x: int(x, 0), metavar=("START", "END"))
    args = parser.parse_args()
    binary = args.binary.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    rea = ReaMcp(output)
    try:
        catalog = rea.request("tools/list", {})
        (output / "tools.json").write_text(json.dumps(catalog, indent=2) + "\n")
        session = rea.call("binary_session")["result"]
        print(json.dumps({"providers": [
            {"provider": p["provider"], "availability": p["availability"]}
            for p in session["analysis_provider_candidates"]
        ]}), flush=True)
        rea.call("open_binary", {"path": str(binary), "provider_id": "ghidra"})
        print("Verifying the loaded DOS image through REA/Ghidra...", flush=True)
        load = rea.call("inspect_native_load_image")
        loaded = load.get("normalized_result", {})
        print(json.dumps({"load_image": {k: loaded.get(k) for k in
              ("status", "module_bytes", "overlay_bytes", "target_sha256")}}), flush=True)
        overview = rea.call("binary_overview")
        print(json.dumps({"overview": {k: overview.get("normalized_result", {}).get(k) for k in
              ("procedure_count", "string_count", "segment_count")}}), flush=True)
        procedures = rea.call("list_procedures")["normalized_result"]
        rea.call("search_strings", {
            "pattern": "ANSI|UART|COM[1-4]|RTS|CTS|XON|XOFF|PLINK|Overlay|PROCOMM",
            "mode": "regex", "case_sensitive": False,
        })
        if args.region:
            procedures = [p for p in procedures
                          if args.region[0] <= int(p["address"], 16) < args.region[1]]
        selected = procedures if args.decompile_all else procedures[:5]
        print(f"Exporting pseudocode and assembly for {len(selected)} functions...", flush=True)
        failures = []
        for index, procedure in enumerate(selected):
            address = procedure["address"]
            stem = address.replace(":", "_").replace("%", "_")
            for tool, suffix in [("procedure_pseudo_code", "c"), ("procedure_assembly", "asm")]:
                try:
                    evidence = rea.call(tool, {"procedure": address}, f"functions/{stem}-{suffix}")
                    text = evidence.get("normalized_result")
                    if isinstance(text, str):
                        header = (f"/* REA/Ghidra pseudocode; not original source. Address {address}; "
                                  f"Evidence {evidence.get('evidence_id')}. */\n") if suffix == "c" else ""
                        (output / "functions" / f"{stem}.{suffix}").write_text(header + text + "\n")
                except RuntimeError as error:
                    failures.append({"address": address, "tool": tool, "error": str(error)})
            if (index + 1) % 25 == 0:
                print(f"Exported {index + 1}/{len(selected)} functions", flush=True)
        (output / "failures.json").write_text(json.dumps(failures, indent=2) + "\n")
        rea.call("export_evidence_bundle", {"path": str(output / "evidence-bundle.json"), "overwrite": True})
        print(f"Completed; {len(failures)} failed operations. Artifacts: {output}", flush=True)
    finally:
        rea.close()


if __name__ == "__main__":
    main()
