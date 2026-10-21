#!/usr/bin/env python3
"""Compare actual DOS bytes, independent caller decode and guest wire frames."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import struct
from modem import Telnet


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def differences(expected, actual):
    return [{'operation':op,'expected_start':i,'expected_end':j,'actual_start':k,'actual_end':l,
             'expected_hex':expected[i:j].hex(),'actual_hex':actual[k:l].hex()}
            for op,i,j,k,l in difflib.SequenceMatcher(a=expected,b=actual,autojunk=False).get_opcodes()
            if op!='equal']


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('cohort',type=Path)
    out=parser.parse_args().cohort.resolve();raw=(out/'serial-in.bin').read_bytes()
    assert raw.startswith(b'ATZ\rATD1\r');expected=raw[9:]
    offline=json.loads((out/'offline-caller.json').read_text())
    decoded=b''.join(bytes.fromhex(row['hex']) for row in offline['received'])
    assert sha(out/'rtp-from-caller.bin')==offline['capture_sha256']
    wire=(out/'control-wire.bin').read_bytes();at=0;guest=bytearray()
    while at<len(wire):
        assert at+3<=len(wire);length,kind=struct.unpack_from('<HB',wire,at)
        assert 1<=length<=4094 and at+length+2<=len(wire)
        if kind==0x15:guest.extend(wire[at+3:at+length+2])
        at+=length+2
    # No speculative training-tail removal. A nonzero declared sink count
    # would need phase accounting; this cohort must have a zero-byte prefix.
    import re
    holds=re.findall(r'Post-train hold complete .*dropped (\d+) bytes\)',(out/'node.log').read_text())
    assert holds==['0'],holds
    target=expected.split(b'\r',1)[0]+b'\r'
    sent,_=Telnet().feed((out/'bbs-input.bin').read_bytes())
    display,_=Telnet().feed((out/'bbs-output.bin').read_bytes())
    caller=(out/'caller-decoded.bin').read_bytes()
    prefix=(b'PCPLUS DSP LAB V22 1200\r\nCONNECT> Connecting to '+target[:-1]+
            b'...\r\r\nConnected to '+target[:-1]+b'.\r\r\nIn-band menu escape disabled; remote close returns to menu. QUIT there hangs up.\r\r\n\r\r\n')
    upstream=differences(expected,bytes(guest))
    downstream=differences(prefix+display,caller)
    checks={'offline_caller_matches_all_DOS_bytes':decoded==expected,
            'guest_matches_exact_BBS_input':bytes(guest)==target+sent,
            'extra_upstream_bytes_reproduced':bool(upstream),
            'entire_caller_stream_compared':True}
    names=('serial-in.bin','control-wire.bin','bbs-input.bin','bbs-output.bin',
           'caller-decoded.bin','rtp-from-caller.bin','offline-caller.json','node.log','result.json')
    result={'diagnosis_verified':all(checks.values()),'checks':checks,
            'DOS_online_bytes':len(expected),'offline_caller_bytes':len(decoded),'guest_DATA_RX_bytes':len(guest),
            'upstream_changes':upstream,'downstream_changes':downstream,
            'unexpected_upstream_bytes':sum(len(bytes.fromhex(x['actual_hex'])) for x in upstream),
            'captured_BBS_display_bytes':len(display),'caller_decoded_bytes':len(caller),
            'capture_sha256':{name:sha(out/name) for name in names},'analyzer_sha256':sha(Path(__file__)),
            'scope':'Read-only actual serial/guest/Telnet comparison and independent captured-caller QAM decode. Diagnosis verification means a reproduced failure, not transport acceptance. No guest PCM/arrival timing exists in this normal capture, so jitter, DSP and resampling causes remain unproven; terminal-close truncation is not automatically acoustic corruption.'}
    (out/'integrity-diagnosis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
