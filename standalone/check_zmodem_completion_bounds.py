#!/usr/bin/env python3
"""Component safety bounds for completed-data drain and closing retries."""
import ctypes as C
import hashlib,json,subprocess
from pathlib import Path
from check_zmodem import Fixture,P,U,h,offer,payload
from check_zmodem_wire import packet

ROOT=Path(__file__).resolve().parents[1]


def main():
    out=ROOT/'build/zmodem-completion-bounds';out.mkdir(exist_ok=True)
    sources=[ROOT/'src/transfer'/name for name in ('zmodem.c','zmodem_wire.c','zmodem_name.c','batch_header.c')]
    library=out/'session.so'
    subprocess.run(['gcc','-std=c89','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-shared','-fPIC',*[str(p) for p in sources],'-o',str(library)],check=True)
    lib=C.CDLL(str(library));lib.zm_run.argtypes=[P,P,P,U]
    body=b'ABCD';base=offer('ONE.BIN',4)+payload(body)+h(11,4)
    stale=h(10,0,67)+packet(body,67,107,0)
    bad_packet=bytearray(packet(body,67,107,0));bad_packet[0]^=1
    bad_header=bytearray(h(7));at=bad_header.index(13)-1;bad_header[at]=48 if bad_header[at]!=48 else 49
    recipes=[
        ('initial-post-EOF-abort-remains-fatal',base+h(7),5),
        ('bad-CRC-replay-does-not-write',base+h(10,0,67)+bad_packet,6),
        ('replay-beyond-committed-range-rejected',base+h(10,3,67)+packet(b'XX',67,107,0),6),
        ('empty-continuing-replay-bounded',base+h(10,0,67)+packet(b'',67,105,0),6),
        ('ten-replay-frame-ceiling',base+stale*10+h(8)+b'OO',4),
        ('ten-closing-header-ceiling',base+h(8)+h(8)*10+b'OO',8),
        ('bad-CRC-closing-header-not-OO',base+h(8)+bad_header+b'OO',8),
        ('nonzero-closing-position-rejected',base+h(8)+h(8,1)+b'OO',8),
        ('unrelated-closing-header-rejected',base+h(8)+h(3)+b'OO',8),
        ('noise-containing-OO-not-success',base+h(8)+b'NOISEOO',8),
        ('flow-between-literal-Os',base+h(8)+b'O\x11OAPP',0),
        ('five-CANs-still-cancel-closing',base+h(8)+b'\x18'*5,5),
        ('missing-OO-after-valid-close-headers-unconfirmed',base+h(8)+(h(7)+h(8))*4,8),
    ]
    rows=[]
    for name,wire,wanted in recipes:
        f=Fixture(lib,rx=wire);status=f.run()
        checks={'expected_status':status==wanted,'installed_file_preserved':f.received=={'ONE.BIN':body},
            'one_open_write_commit':sum(e[0]=='open' for e in f.events)==sum(e[0]=='append' for e in f.events)==sum(e[0]=='commit' for e in f.events)==1,
            'no_unresolved_stage':f.stage is None}
        if wanted==0:checks['application_tail_unconsumed']=bytes(f.rx)==b'APP'
        row={'case':name,'passed':all(checks.values()),'status':status,'checks':checks,'actual_wire_hex':f.tx.hex()}
        rows.append(row);assert row['passed'],row
    result={'passed':True,'cases':rows,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'scope':'Maintained C component compiled with strict C89 in pinned Nix; ctypes file/transport callbacks modeled. Thirteen rejection/limit/flow cases preserve one checked file and cannot infer actual DOS/audio or physical acceptance.'}
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print('Passed',len(rows),'ZMODEM completion-bound cases')


if __name__=='__main__':main()
