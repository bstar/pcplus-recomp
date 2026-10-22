#!/usr/bin/env python3
"""Actual DOS PROGRAM after MODEM carrier loss, then redial and manual input."""
import argparse,inspect,json,re,shutil,struct,subprocess,types
from pathlib import Path
import test_modem_reconnect_dos as reconnect
ROOT=reconnect.ROOT;sha=reconnect.sha;ESC=b'\x1b'


def adapter(out,events):
    text=inspect.getsource(reconnect.adapter)
    text=text.replace('def adapter(out,events,gap):','def build(out,events,gap=False):')
    text=text.replace("ready=None;xoff=False;completed=None","ready=time.monotonic();xoff=True;completed=None")
    text=text.replace("now-ready>=1:","now-ready>=.7:")
    text=text.replace("b'ready\\x1b[1;25R'","b'ready\\x1b[1;16R'")
    text=text.replace("checks['screen_snapshot_complete']=len(screen)==4000", "checks['screen_snapshot_complete']=len(screen)==4000")
    module=types.ModuleType('offline_PROGRAM_modem');module.__dict__.update(reconnect.__dict__)
    exec(compile(text,__file__,'exec'),module.__dict__);return module.build(out,events)


def child(out):
    symbols=reconnect.window.symbols(ROOT/'build/terminal/terminal.map')
    source=(ROOT/'standalone/program_handoff_child.asm').read_text()
    fields=['connection_state','connection_status','connection_carrier_seen','uart_xoff_sent']
    sample='''
 mov ax,[cs:0x16]
 mov es,ax
 mov ax,[es:0x16]
 add ax,PARENT_DATA
 mov es,ax
'''
    for i,name in enumerate(fields):
        sample+=(' xor ax,ax\n mov al,' if i>=2 else ' mov ax,')+'[es:'+str(symbols[name][1])+']\n mov [cs:offline_sample+'+str(i*2)+'],ax\n'
    sample=sample.replace('PARENT_DATA',str(symbols['connection_state'][0]+0x10))
    source=source.replace('start:\n','start:\n'+sample)
    needle=' mov dx,sample_name\n call create\n'
    assert source.count(needle)==1
    source=source.replace(needle,' mov dx,offline_name\n call create\n mov dx,offline_sample\n mov cx,8\n call write_close\n'+needle)
    source+="\noffline_name: db 'D:\\OFFLINE.BIN',0\noffline_sample: times 4 dw 0\n"
    (out/'child.asm').write_text(source)
    subprocess.run(['nasm','-fbin',str(out/'child.asm'),'-o',str(out/'CHILD.COM')],check=True)
    return (out/'CHILD.COM').read_bytes()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);p.add_argument('--expect-gap',action='store_true');a=p.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
    out=ROOT/'build/program-offline-modem-dos'/a.label;out.mkdir(parents=True,exist_ok=False)
    binary=ROOT/'build/terminal/TERMINAL.EXE';manifest=json.loads((binary.parent/'manifest.json').read_text());assert sha(binary)==manifest['binary_sha256']
    inputs={**manifest['sources']}
    for path in [Path(__file__),Path(reconnect.__file__),Path(reconnect.carrier.__file__),Path(reconnect.carrier.connection.__file__),ROOT/'standalone/program_handoff_child.asm']:
        inputs[str(path.relative_to(ROOT))]=sha(path)
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    helper=child(out);rows=[]
    for hard in (0,1):
        name='both' if hard else 'soft';folder=out/name;folder.mkdir();events=[];peer=adapter(out,events)
        shutil.copy2(binary,folder/'TERMINAL.EXE');peer.BINARY=folder/'TERMINAL.EXE'
        settings=bytearray(reconnect.prm(soft=1,hard=hard));settings[0x79:0x79+25]=b'ATH^M'.ljust(25,b'\0')
        keys=bytearray(540)
        for i in range(10):struct.pack_into('<H',keys,i*54,3)
        command=b'D:\\CHILD.COM /OWNED';struct.pack_into('<H',keys,0,1);keys[2:2+len(command)]=command
        files={'CHILD.COM':helper,'TEST.KEY':bytes(keys)}
        try:
            report=peer.run(name,'success','p3000 a-1 p1800 space p1000 a-d p3500 r e a d y p900 a-x',
                directory=reconnect.directory(profile=4),prm=bytes(settings),profile=4,files=files,working_drive='d',accounting_delta=2,
                arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /T:D:\\TEST.KEY /A:NETWORK',
                banner=ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+ESC+b'[6n'+ESC+b'[0c')
        finally:(folder/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
        log=(folder/'dosbox.log').read_text();commands=re.findall(r'Command sent to modem: ->(.*?)<-',log)
        dial=(folder/'DIAL.IN').read_bytes()[275:296].split(b'\0',1)[0].decode()
        expected=['ATZ','ATD'+dial,('\x13' if a.expect_gap else '')+'ATZ','ATD'+dial]
        offline=struct.unpack('<4H',(folder/'OFFLINE.BIN').read_bytes()) if (folder/'OFFLINE.BIN').exists() else ()
        handoff=(folder/'HANDOFF.BIN').read_bytes() if (folder/'HANDOFF.BIN').exists() else b''
        wire=(folder/'serial.bin').read_bytes();prefix=ESC+b'[1;16R'+ESC+b'[?62;2c'
        checks=dict(report['checks'],child_ran_after_observed_loss=offline==(0,6,1,int(a.expect_gap)),
            child_released_UART=len(handoff)==10 and handoff[5]==0 and handoff[6]&3==1,
            child_exact_tail=(folder/'HANDARG.BIN').is_file() and (folder/'HANDARG.BIN').read_bytes()==b'\x07 /OWNED\r',
            modem_commands_exact=commands==expected,modem_ERROR_count=len(re.findall(r'Modem response: ERROR',log))==int(a.expect_gap),
            both_connections=sum(e['kind']=='connected' for e in events)==2,
            exact_BBS_stream=wire==prefix+prefix+b'ready'+ESC+b'[1;16R')
        rows.append(dict(case=name,passed=all(checks.values()),checks=checks,offline_sample=list(offline),commands=commands,
            wire_hex=wire.hex(),captures={str(f.relative_to(folder)):sha(f) for f in folder.rglob('*') if f.is_file()}))
        print(json.dumps(dict(case=name,passed=rows[-1]['passed'],checks=checks,offline_sample=list(offline),commands=commands)),flush=True)
    result=dict(passed=all(r['passed'] for r in rows),gap_reproduced=a.expect_gap,compatibility_accepted=not a.expect_gap,cases=rows,parent_sha256=sha(binary),inputs=inputs,
        scope=__doc__+' Two actual8086 DOSBox virtual-modem sessions per flow setting. Real remote socket close supplies DCD loss; owned child reads parent state and mutates UART/video, then parent restores and redials. Baseline XOFF corrupts second ATZ. No production-state injection or physical modem acceptance.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed']


if __name__=='__main__':main()
