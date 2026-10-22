#!/usr/bin/env python3
"""Actual File/A ASPECT launch after MODEM loss, then redial/manual input."""
import argparse,json,re,shutil,struct,subprocess
from pathlib import Path
import test_program_offline_modem_dos as program
ROOT=program.ROOT;sha=program.sha;ESC=b'\x1b'
renderer=program.reconnect.renderer


def observer(out):
    renderer.OUT=out;renderer.observer(renderer.map_offsets(ROOT/'build/terminal/terminal.map'))
    symbols=program.reconnect.window.symbols(ROOT/'build/terminal/terminal.map')
    path=out/'observer.asm';text=path.read_text();fields=['connection_state','connection_status','connection_carrier_seen','uart_xoff_sent']
    sample=' push es\n mov es,[parent_ds]\n'
    for i,name in enumerate(fields):
        sample+=(' xor ax,ax\n mov al,' if i>=2 else ' mov ax,')+'[es:'+str(symbols[name][1])+']\n mov [offline_sample+'+str(i*2)+'],ax\n'
    sample+=' pop es\n'
    needle=' inc word [exec_seen]\n';assert text.count(needle)==1;text=text.replace(needle,needle+sample)
    needle='sample_end:\nowner_table:';assert text.count(needle)==1
    text=text.replace(needle,'offline_sample: times 4 dw 0\n'+needle);path.write_text(text)
    subprocess.run(['nasm','-fbin',str(path),'-o',str(out/'RENDER.COM')],check=True)
    return (out/'RENDER.COM').read_bytes()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);a=p.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
    out=ROOT/'build/script-offline-modem-dos'/a.label;out.mkdir(parents=True,exist_ok=False);inputs={}
    for directory,leaf in [('terminal','TERMINAL.EXE'),('aspect-runner','ASPECT.EXE')]:
        base=ROOT/'build'/directory;m=json.loads((base/'manifest.json').read_text());assert sha(base/leaf)==m['binary_sha256'];inputs.update(m['sources'])
        for f in (base/leaf,base/'manifest.json',*base.glob('*.map')):inputs[str(f.relative_to(ROOT))]=sha(f)
    for f in (Path(__file__),Path(program.__file__),Path(program.reconnect.__file__),Path(program.reconnect.carrier.__file__),Path(program.reconnect.carrier.connection.__file__),Path(renderer.__file__),Path(program.reconnect.window.__file__)):
        inputs[str(f.relative_to(ROOT))]=sha(f)
    inputs['src/aspect/compiler.py']=sha(ROOT/'src/aspect/compiler.py')
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    compiled=observer(out);rows=[]
    source='proc main\nfopen 5 "LOCAL.OK" "wb"\nfputs 5 "OFFLINE SCRIPT"\nfclose 5\nendproc\n'
    for hard in (0,1):
        name='both' if hard else 'soft';folder=out/name;folder.mkdir();events=[];peer=program.adapter(out,events)
        shutil.copy2(ROOT/'build/terminal/TERMINAL.EXE',folder/'TERMINAL.EXE');peer.BINARY=folder/'TERMINAL.EXE'
        settings=bytearray(program.reconnect.prm(soft=1,hard=hard));settings[0x79:0x79+25]=b'ATH^M'.ljust(25,b'\0')
        files={'ASPECT.EXE':(ROOT/'build/aspect-runner/ASPECT.EXE').read_bytes(),'GO.ASP':source.encode(),'GO.ASX':renderer.compile_source(source),'RENDER.COM':compiled}
        try:
            r=peer.run(name,'success','p3000 a-z p200 a p200 g o . a s x enter p2400 a-d p3500 r e a d y p900 a-x',
                directory=program.reconnect.directory(profile=4),prm=bytes(settings),profile=4,files=files,working_drive='d',observer='RENDER',accounting_delta=2,
                arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK',banner=ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+ESC+b'[6n'+ESC+b'[0c')
        finally:(folder/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
        raw=(folder/'RENDER.BIN').read_bytes();head=struct.unpack_from('<7H',raw);offline=struct.unpack('<4H',raw[-8:])
        log=(folder/'dosbox.log').read_text();commands=re.findall(r'Command sent to modem: ->(.*?)<-',log);dial=(folder/'DIAL.IN').read_bytes()[275:296].split(b'\0',1)[0].decode()
        wire=(folder/'serial.bin').read_bytes();prefix=ESC+b'[1;16R'+ESC+b'[?62;2c'
        checks=dict(r['checks'],actual_ASPECT_exit=head[:4]==(0x524e,1,1,1) and head[6]==0,
            offline_at_direct_EXEC=offline==(0,6,1,0),JFT_restored=raw[14:34]==raw[34:54],file_owners_restored=raw[54:470]==raw[470:886],
            local_script_marker=(folder/'LOCAL.OK').is_file() and (folder/'LOCAL.OK').read_bytes()==b'OFFLINE SCRIPT',
            clean_modem_commands=commands==['ATZ','ATD'+dial,'ATZ','ATD'+dial],no_modem_ERROR='Modem response: ERROR' not in log,
            exact_BBS_stream=wire==prefix+prefix+b'ready'+ESC+b'[1;16R',both_connections=sum(e['kind']=='connected' for e in events)==2)
        rows.append(dict(case=name,passed=all(checks.values()),checks=checks,offline_sample=list(offline),child_exit=head[6],wire_hex=wire.hex(),captures={str(f.relative_to(folder)):sha(f) for f in folder.rglob('*') if f.is_file()}))
        print(json.dumps(dict(case=name,passed=rows[-1]['passed'],checks=checks,offline_sample=list(offline),child_exit=head[6])),flush=True)
    result=dict(passed=all(r['passed'] for r in rows),cases=rows,inputs=inputs,parent_sha256=sha(ROOT/'build/terminal/TERMINAL.EXE'),runner_sha256=sha(ROOT/'build/aspect-runner/ASPECT.EXE'),
        scope=__doc__+' Two actual8086 SOFT/BOTH sessions. Real virtual-modem DCD loss; passive direct-EXEC observation of offline parent; actual local ASPECT file output; JFT/file-owner/UART restoration; clean second ATZ and manual ANSI query. No product state, serial replies or observed handler results injected. Physical hardware and complete application acceptance remain open.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed']


if __name__=='__main__':main()
