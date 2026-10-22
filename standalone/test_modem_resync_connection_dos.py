#!/usr/bin/env python3
"""Stock-backend DOS connection regressions with explicit empty modem command handling."""
import argparse, inspect, json, types
from pathlib import Path
import test_connection_dos as base
from audit_aspect_transmit_wait import ROOT, sha, ESC


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--product',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    text=inspect.getsource(base.run).replace("out=ROOT/'build/connection-dos'/name",'out=CASE_OUT/name')
    # The common modem peer ignores empty CR commands. Keep exact wire checks
    # below so ignoring a separator cannot hide changed initialization bytes.
    assert text.count('if not command:continue')==1
    module=types.ModuleType('resync_connection');module.__dict__.update(base.__dict__)
    module.__dict__.update(CASE_OUT=out,BINARY=a.product.resolve()/'TERMINAL.EXE')
    exec(compile(text,__file__,'exec'),module.__dict__)
    cases=[('first-connect','success','p4000 a-x'),('busy-abort','busy','p4000 a-x'),('timeout-abort','silence','p4000 a-x'),('hangup','hangup','p3000 a-h p2200 a-x'),('redial','redial','p3500 a-d p3500 a-x')]
    rows=[]
    for name,mode,keys in cases:
        result=module.run(name,mode,keys);assert result['passed']
        wire=(out/name/'serial.bin').read_bytes();commands=b'ATZ\rATDCaseTest:23\r'
        if mode=='redial':assert wire.startswith(commands+ESC+b'\r'+commands)
        else:assert wire.startswith(commands) and not wire.startswith(b'\r')
        if mode in ('busy','silence'):assert wire==commands+ESC
        rows.append(dict(case=name,passed=True,wire_sha256=sha(out/name/'serial.bin'),producer_report_sha256=sha(out/name/'result.json')))
    report=dict(passed=True,cases=rows,parent_sha256=sha(module.BINARY),checker_sha256=sha(Path(__file__)),base_checker_sha256=sha(Path(base.__file__)),scope=__doc__+' Owned modem peer, stock nullmodem transport. Initial connections unchanged; BUSY retry sends exactly one separator after abort, followed by clean configured initialization. Physical modem and full application remain unverified.')
    (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows))))


if __name__=='__main__':main()
