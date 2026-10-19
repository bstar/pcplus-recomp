#!/usr/bin/env python3
"""Replay a captured valid ZFILE through the actual linked metadata decoder."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from check_transport import Transport
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab/bbs'))
from audit_zmodem import scan,packet,metadata


def main(capture,output):
    capture=capture.resolve();output=output.resolve()
    assert capture.is_relative_to(ROOT/'build') and output.is_relative_to(ROOT/'build')
    assert not output.exists(),'Retain earlier evidence'
    stream=capture.read_bytes();offer=None
    for h in scan(stream):
        if h['type']!=4:continue
        try:
            p=packet(stream,h['end'],h['format']);name,size=metadata(p['payload'])
            if name=='PCPLUS PROBE 01 (1991).ZIP':offer=(h,p,name,size);break
        except (AssertionError,ValueError,UnicodeError):continue
    assert offer,'No CRC-verified selected game offer'
    h,p,name,size=offer;raw=p['payload'];assert len(raw)<=1024
    name_bytes,sep,rest=raw.partition(b'\0');assert sep
    alias=b'PROBE01.ZIP';changed=alias+b'\0'+rest
    observations=[]
    for kind,block,expected in [('captured',raw,2),('DOS83-filename-only',changed,0)]:
        m=Transport();block=block+bytes(1024-len(block));sentinel=b'\x77'*36
        pointer=m.stage_near(block+sentinel)
        value=m.call('_batch_header_decode',[pointer,1024,pointer+1024],limit=200000)
        result=bytes(m.uc.mem_read(m.data_base+pointer+1024,36))
        assert value==expected,(kind,value)
        if value:assert result==sentinel,'Failed decode changed result'
        else:assert result[:13].split(b'\0',1)[0]==alias
        observations.append(dict(input=kind,status=value,result_unchanged=result==sentinel,block_sha256=hashlib.sha256(block).hexdigest()))
    report=dict(passed=True,terminal_sha256=hashlib.sha256((ROOT/'build/terminal/TERMINAL.EXE').read_bytes()).hexdigest(),
        checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        header_source_sha256=hashlib.sha256((ROOT/'src/transfer/batch_header.c').read_bytes()).hexdigest(),
        capture_sha256=hashlib.sha256(stream).hexdigest(),wire_name=name,wire_size=size,
        metadata_crc_verified=True,header_offset=h['offset'],observations=observations,
        scope='Actual linked production metadata decoder receives CRC-verified captured ZFILE, padded exactly as the receive engine does. Captured long name returns BH_NAME atomically; changing only that field to a DOS83 name returns BH_OK. No transfer completion, filesystem mapping or physical-modem claim.')
    output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();main(a.capture,a.output)
