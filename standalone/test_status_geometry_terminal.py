#!/usr/bin/env python3
"""Compare real DOS cursor/scroll/RIS behavior with an independent24-row screen."""
import argparse,json,re,struct
from pathlib import Path
import test_connection_dos as terminal
from build_phone_log_queue import ROOT,sha
from test_ansi_reference_dos import reference
from modem_fixtures import fixture


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--terminal',type=Path,required=True);p.add_argument('--control',type=Path,required=True);p.add_argument('--label',required=True)
    a=p.parse_args();assert re.fullmatch('[a-z0-9-]+',a.label)
    out=ROOT/'build/status-geometry-terminal'/a.label;assert not out.exists();out.mkdir(parents=True)
    banner=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c'
    payload=b'\x1b[999;1H\x1b[6n\x1bc\x1b[999;1H\x1b[6n\x1b[2J\x1b[H'
    payload+=b''.join(f'R{n:02}\r\n'.encode() for n in range(1,25))
    payload+=b'\x1b[HFIRST BYTE SAFE\x1b[6n'
    expected,_=reference(banner+payload)
    rows=[]
    for name,binary,accepted in [('candidate',a.terminal.resolve(),True),('old25',a.control.resolve(),False)]:
        manifest=json.loads((binary.parent/'manifest.json').read_text());assert sha(binary)==manifest['binary_sha256']
        terminal.BINARY=binary
        settings=bytearray(fixture(timeout=5));struct.pack_into('<HH',settings,0x4e4,8,4)
        native=terminal.run(a.label+'-'+name,'success','p900 enter p3500 a-x',online_updates=((1,payload),),cpu='8086',prm=bytes(settings),working_drive='d')
        folder=ROOT/'build/connection-dos'/(a.label+'-'+name)
        screen=(folder/'SCREEN.BIN').read_bytes();wire=(folder/'serial.bin').read_bytes()
        differences=[i for i in range(1920) if screen[2*i:2*i+2]!=expected[2*i:2*i+2]]
        reply_ok=wire==b'ATZ\rATDCaseTest:23\r\x1b[1;16R\x1b[?1;2c\x1b[24;1R\x1b[24;1R\x1b[1;16R+++ATH\r'
        matched=not differences and reply_ok
        checks=dict(native_passed=native['passed'],expected_acceptance=matched==accepted,binary_unchanged=sha(binary)==manifest['binary_sha256'])
        rows.append(dict(case=name,passed=all(checks.values()),checks=checks,matched24=matched,different_cells=len(differences),
                         cursor_replies=re.findall(rb'\x1b\[\d+;\d+R',wire).__repr__(),native=native,binary_sha256=sha(binary),
                         screen_sha256=sha(folder/'SCREEN.BIN')))
    result=dict(passed=all(r['passed'] for r in rows),cases=rows,reference_sha256=__import__('hashlib').sha256(expected).hexdigest(),
        sources={n:sha(ROOT/n) for n in ('standalone/test_status_geometry_terminal.py','standalone/test_connection_dos.py','standalone/test_ansi_reference_dos.py')},
        scope=__doc__+' Actual source-built candidate and old25-row control, real UART replies and hardware restoration; no product writes or synthetic replies. Selected reset/scroll boundary only.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));assert result['passed']

if __name__=='__main__':main()
