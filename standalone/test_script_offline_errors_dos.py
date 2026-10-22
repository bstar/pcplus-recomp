#!/usr/bin/env python3
"""Actual DOS offline File/A errors must clean up and allow clean redial."""
import argparse,json,re,shutil,struct,subprocess
from pathlib import Path
import test_script_offline_modem_dos as script
ROOT=script.ROOT;sha=script.sha;ESC=b'\x1b'


def observer(out):
    script.observer(out);path=out/'observer.asm';text=path.read_text()
    needle=' save\n push cs\n pop ds\n mov di,after_jft\n';assert text.count(needle)==1
    added=' mov bp,sp\n mov ax,[ss:bp+16]\n mov [exec_result],ax\n mov ax,[ss:bp+18]\n mov [exec_flags],ax\n'
    text=text.replace(needle,needle.replace(' mov di,after_jft\n',added+' mov di,after_jft\n'))
    text=text.replace('sample_end:\nowner_table:','exec_result: dw 0xffff\nexec_flags: dw 0xffff\nsample_end:\nowner_table:')
    path.write_text(text);subprocess.run(['nasm','-fbin',str(path),'-o',str(out/'RENDER.COM')],check=True)
    return (out/'RENDER.COM').read_bytes()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);a=p.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
    out=ROOT/'build/script-offline-errors-dos'/a.label;out.mkdir(parents=True,exist_ok=False);inputs={}
    for directory,leaf in [('terminal','TERMINAL.EXE'),('aspect-runner','ASPECT.EXE')]:
        base=ROOT/'build'/directory;m=json.loads((base/'manifest.json').read_text());assert sha(base/leaf)==m['binary_sha256'];inputs.update(m['sources'])
        for f in (base/leaf,base/'manifest.json',*base.glob('*.map')):inputs[str(f.relative_to(ROOT))]=sha(f)
    for f in (Path(__file__),Path(script.__file__),Path(script.program.__file__),Path(script.program.reconnect.__file__),Path(script.program.reconnect.carrier.__file__),Path(script.program.reconnect.carrier.connection.__file__),Path(script.renderer.__file__),Path(script.program.reconnect.window.__file__),ROOT/'src/aspect/compiler.py'):
        inputs[str(f.relative_to(ROOT))]=sha(f)
    for name,digest in inputs.items():
        assert sha(ROOT/name)==digest;target=out/'inputs'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    compiled=observer(out);rows=[]
    source='proc main\nfopen 5 "BAD.OK" "wb"\nfputs 5 "UNREACHABLE"\nfclose 5\nendproc\n'
    valid=script.renderer.compile_source(source)
    for kind in ('missing-runner','missing-script','bad-header'):
      for hard in (0,1):
        name=kind+('-both' if hard else '-soft');folder=out/name;folder.mkdir();events=[];peer=script.program.adapter(out,events)
        shutil.copy2(ROOT/'build/terminal/TERMINAL.EXE',folder/'TERMINAL.EXE');peer.BINARY=folder/'TERMINAL.EXE'
        settings=bytearray(script.program.reconnect.prm(soft=1,hard=hard));settings[0x79:0x79+25]=b'ATH^M'.ljust(25,b'\0')
        files={'RENDER.COM':compiled,'GO.ASP':source.encode()}
        if kind!='missing-runner':files['ASPECT.EXE']=(ROOT/'build/aspect-runner/ASPECT.EXE').read_bytes()
        if kind!='missing-script':files['GO.ASX']=b'\x81' if kind=='bad-header' else valid
        # Failed direct EXEC needs its ordinary local acknowledgement. An
        # adopted renderer reports child errors and immediately restores input.
        after='p1600 space p800' if kind=='missing-runner' else 'p2400'
        try:
            r=peer.run(name,'success','p3000 a-z p200 a p200 g o . a s x enter '+after+' a-d p3500 r e a d y p900 a-x',
                directory=script.program.reconnect.directory(profile=4),prm=bytes(settings),profile=4,files=files,working_drive='d',observer='RENDER',accounting_delta=2,
                arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK',banner=ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+ESC+b'[6n'+ESC+b'[0c')
        finally:(folder/'peer-events.json').write_text(json.dumps(events,indent=2)+'\n')
        raw=(folder/'RENDER.BIN').read_bytes();head=struct.unpack_from('<7H',raw);sample=struct.unpack('<6H',raw[-12:]);missing=kind=='missing-runner'
        log=(folder/'dosbox.log').read_text();commands=re.findall(r'Command sent to modem: ->(.*?)<-',log);dial=(folder/'DIAL.IN').read_bytes()[275:296].split(b'\0',1)[0].decode()
        wire=(folder/'serial.bin').read_bytes();prefix=ESC+b'[1;16R'+ESC+b'[?62;2c'
        checks=dict(r['checks'],direct_EXEC_observed=head[:3]==(0x524e,1,1),actual_child_result=(head[3],head[6])==((0,65535) if missing else (1,1 if kind=='missing-script' else 2)),
            native_EXEC_result=((sample[4]==2 and sample[5]&1==1) if missing else sample[5]&1==0),offline_before_EXEC=sample[:4]==(0,6,1,0),
            JFT_restored=raw[14:34]==raw[34:54],file_owners_restored=raw[54:470]==raw[470:886],unreachable_marker_absent=not (folder/'BAD.OK').exists(),
            clean_modem_commands=commands==['ATZ','ATD'+dial,'ATZ','ATD'+dial],no_modem_ERROR='Modem response: ERROR' not in log,
            exact_BBS_stream=wire==prefix+prefix+b'ready'+ESC+b'[1;16R',both_connections=sum(e['kind']=='connected' for e in events)==2)
        rows.append(dict(case=name,passed=all(checks.values()),checks=checks,child_exits=head[3],child_exit=head[6],sample=list(sample),wire_hex=wire.hex(),captures={str(f.relative_to(folder)):sha(f) for f in folder.rglob('*') if f.is_file()}))
        print(json.dumps(dict(case=name,passed=rows[-1]['passed'],checks=checks,child_exits=head[3],child_exit=head[6],sample=list(sample))),flush=True)
    result=dict(passed=all(r['passed'] for r in rows),cases=rows,inputs=inputs,parent_sha256=sha(ROOT/'build/terminal/TERMINAL.EXE'),runner_sha256=sha(ROOT/'build/aspect-runner/ASPECT.EXE'),
        scope=__doc__+' Six actual8086 SOFT/BOTH File/A workflows: missing ASPECT direct-EXEC failure, missing ASX, malformed ASX header. Passive parent/DOS-return observation; unreachable marker absence; JFT/file-owner/UART cleanup; exact redial/manual query. Owned file omissions/invalid header only, no product/hardware-state injection. No physical or complete application acceptance.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed']


if __name__=='__main__':main()
