#!/usr/bin/env python3
"""Editor -> generated >64KiB ZMODEM download -> same-session BBS menu."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from enigma_key_stream_fixture import ROOT,owned,verify_running,PORT,sha
from enigma_key_stream_dos import recipe,messages
from product_inputs import select_product


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True);p.add_argument('--terminal',type=Path,required=True)
    p.add_argument('--irq',type=int,choices=[5,7],required=True);p.add_argument('--label',required=True)
    args=p.parse_args();candidate=owned(args.candidate);verify_running(candidate)
    assert args.label and all(c.isalnum()or c in'-_'for c in args.label)
    binary,product_sources=select_product(args.terminal,'TERMINAL.EXE')
    fixture=json.loads((candidate/'irq-transfer-fixture.json').read_text())
    payload=candidate/'file_base/pcplus_transfer/IRQDATA.BIN'
    assert fixture['passed']and fixture['bytes']>65536 and fixture['sha256']==sha(payload)
    out=ROOT/'build/bbs-lab/results/enigma'/args.label
    wrapper=out.with_name(args.label+'-wrapper');assert not out.exists()and not wrapper.exists()
    wrapper.mkdir(parents=True)
    keys=recipe('editor-transfer')
    assert keys.count('P C X T E S T . B I N')==2 and keys.count('p30000')==1
    keys=keys.replace('P C X T E S T . B I N','I R Q D A T A . B I N').replace('p30000','p60000')
    divisor,unit=(1048576,'MB')if fixture['bytes']>=1048576 else(1024,'KB')
    displayed_size=f'{fixture["bytes"]/divisor:.2f}'.rstrip('0').rstrip('.')
    command=[sys.executable,'lab/bbs/test_zmodem_dos.py','enigma','--port',str(PORT),
             '--server-instance',str(candidate/'instance.json'),'--editor-first','--binary',str(binary),
             '--label',args.label,'--sha256',sha(binary),'--mode','download',
             '--file','IRQDATA.BIN='+str(payload),'--auto-download','--dial-fixture','--keys',keys,
             '--start-input-hex',b'IRQDATA.BIN\r'.hex(),'--post-input-hex',b'S\r'.hex(),
             '--post-menu','IRQDATA.BIN ','--post-menu',displayed_size+' ','--post-menu',unit+' ',
             '--timeout','260','--cpu','8086','--irq',str(args.irq),'--mouse-scales','8','4']
    sources=[ROOT/'lab/bbs'/name for name in ['enigma_irq_large_dos.py','enigma_key_stream_dos.py',
             'enigma_key_stream_fixture.py','test_zmodem_dos.py','test_transfer_dos.py','modem.py',
             'audit_zmodem.py','product_inputs.py','editor-recipes.json']]
    sources += [binary,binary.parent/'manifest.json',*product_sources,payload,candidate/'instance.json',
                candidate/'config/config.hjson',candidate/'irq-transfer-fixture.json',candidate/'core/client.js',
                candidate/'core/key_stream.js',candidate/'helpers/sexyz']
    before={str(path.relative_to(ROOT)):sha(path)for path in sources};count=messages(candidate)
    (wrapper/'command.json').write_text(json.dumps(command,indent=2)+'\n')
    with (wrapper/'harness.log').open('w')as log:
        code=subprocess.call(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    after={str(path.relative_to(ROOT)):sha(path)for path in sources}
    result=dict(passed=code==0 and before==after and messages(candidate)==count,harness_exit=code,
                input_hashes=before,inputs_unchanged=before==after,message_count_before=count,message_count_after=messages(candidate),
                modem_packet_delay_ms=0,irq=args.irq,cpu='8086',payload_bytes=fixture['bytes'],
                scope=__doc__+' Current source-built terminal, immediate framed local BBS and generated media; no physical or general saturation claim.')
    (wrapper/'experiment.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return 0 if result['passed']else 1


if __name__=='__main__':raise SystemExit(main())
