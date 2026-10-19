#!/usr/bin/env python3
"""Synthetic negative controls for the passive owned-server log auditor."""
import json
from pathlib import Path
import tempfile

from test_transfer_dos import ROOT, audit_enigma_server


def main():
    parent = ROOT / "build/bbs-lab/log-boundary-checks"
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=parent) as directory:
        root = Path(directory)
        log = root / "server.jsonl"
        output = root / "output"
        output.mkdir()
        prefix = b'{"msg":"Client connected on node 1","sessionId":"old"}\n'
        events = [
            {"msg": "Client connected on node 1"},
            {"msg": 'User "loclab" successfully logged in'},
            {"menuName": "fileTransferProtocolSelection"},
            {"msg": "Executing external protocol"},
            {"msg": "Process exited", "exitCode": 0},
            {"menuName": "fileBaseMainMenu"},
            {"menuName": "fileBaseListEntries"},
        ]
        body = b"".join((json.dumps(dict(event, sessionId="owned")) + "\n").encode()
                        for event in events)
        log.write_bytes(prefix + body + prefix)
        boundary = dict(byte_offset=len(prefix), path=str(log), inode=log.stat().st_ino)

        def write_boundary(value):
            (output / "server-log-start.json").write_text(json.dumps(value))

        write_boundary(boundary)
        result = audit_enigma_server(output, "download", len(prefix + body))
        assert result["passed"] and not result["stock_server"]
        assert result["session_id"] == "owned"
        assert (output / "server-session.jsonl").read_bytes() == body
        assert not audit_enigma_server(output, "download")["passed"], "Foreign tail connection must fail uniqueness"
        for value in [dict(boundary, inode=boundary["inode"] + 1),
                      dict(boundary, path="/etc/passwd")]:
            write_boundary(value)
            try:
                audit_enigma_server(output, "download")
            except AssertionError:
                pass
            else:
                raise AssertionError("Invalid log identity accepted")
        write_boundary(boundary)
        for end in [len(prefix) - 1, log.stat().st_size + 1]:
            try:
                audit_enigma_server(output, "download", end)
            except AssertionError:
                pass
            else:
                raise AssertionError("Invalid log extent accepted")
    print("Passed six synthetic server-log boundary/identity controls; not BBS compatibility evidence")


if __name__ == "__main__":
    main()
