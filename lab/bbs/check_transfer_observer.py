#!/usr/bin/env python3
"""Decoded transfer traces exclude Telnet-only input without losing byte ranges."""
import argparse
import hashlib
import json
from pathlib import Path

from test_transfer_dos import ROOT,ObservedModem,timestamp


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();out=args.output.resolve()
    assert out.is_relative_to(ROOT/'build')and not out.exists()
    out.mkdir(parents=True)
    payload=bytes(range(256))
    wire=b'\xff\xfb\x01'+payload[:128]+b'\xff\xfd\x03'+payload[128:].replace(b'\xff',b'\xff\xff')+b'\xff\xfb\x03'
    vectors=[[wire[:i],wire[i:]]for i in range(len(wire)+1)]
    vectors += [[bytes([byte])for byte in wire],[b'\xff',b'\xfb',b'\x01',b'',wire[3:]]]
    for chunks in vectors:
        modem=ObservedModem('127.0.0.1',1,out/'unused')
        for chunk in chunks:modem.observe_bbs(chunk)
        assert modem.bbs_offset==len(payload)
        assert all(event['size']>0 and event['direction']=='bbs'for event in modem.trace)
        end=0
        for event in modem.trace:
            assert event['offset']==end
            end+=event['size']
        assert end==len(payload)
        for offset in range(len(payload)):assert timestamp(modem.trace,'bbs',offset)>=0
    # A real serial-side proxy has already decoded Telnet. Literal FF, FF-FF
    # and FF-FB bytes are binary payload here and must never be decoded again.
    raw_payload=payload+b'\xff\xff\xff\xfb\x01'
    raw_vectors=[[raw_payload[:i],raw_payload[i:]]for i in range(len(raw_payload)+1)]
    raw_vectors.append([bytes([byte])for byte in raw_payload])
    for chunks in raw_vectors:
        modem=ObservedModem('127.0.0.1',1,out/'unused',raw=True)
        for chunk in chunks:modem.observe_bbs(chunk)
        assert modem.bbs_offset==len(raw_payload) and not modem.audit_codec.events
        end=0
        for event in modem.trace:
            assert event['offset']==end and event['size']>0
            end+=event['size']
        assert end==len(raw_payload)
        for offset in range(len(raw_payload)):assert timestamp(modem.trace,'bbs',offset)>=0
    def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
    result=dict(passed=True,cases=len(vectors),raw_cases=len(raw_vectors),raw_byte_offsets=len(raw_payload),all_byte_offsets=len(payload),sources={str(path.relative_to(ROOT)):sha(path)
                for path in [Path(__file__).resolve(),ROOT/'lab/bbs/test_transfer_dos.py',ROOT/'lab/bbs/modem.py']},scope=__doc__)
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS decoded observer:',len(vectors),'partitions and all256 byte offsets')


if __name__=='__main__':main()
