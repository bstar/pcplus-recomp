#!/usr/bin/env python3
"""Observe real DOS8086 connect beeps while serial BBS rendering stays active."""
import argparse,json,struct,subprocess,hashlib,shutil,sys
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--runner',type=Path);p.add_argument('--label',required=True);a=p.parse_args()
    assert a.label.replace('-','').isalnum()
    harness.BINARY=a.terminal.resolve();out=ROOT/'build'/('connect-alert-dos-'+a.label);out.mkdir(exist_ok=False)
    if a.runner:
        stage=out/'PARENT';stage.mkdir()
        shutil.copyfile(a.terminal,stage/'TERMINAL.EXE');shutil.copyfile(a.runner,stage/'ASPECT.EXE')
        harness.BINARY=stage/'TERMINAL.EXE'
    subprocess.run(['nasm','-fbin',str(ROOT/'standalone/connect_alert_watch.asm'),'-o',str(out/'TONE.COM')],check=True)
    cases=[]
    plans=[('quiet',0,5,'p900 enter p3500 a-x'),('expiry',1,5,'p900 enter p8500 a-x'),('key',1,5,'p900 enter p2400 q p2000 a-x')]
    if a.runner:plans.append(('script',1,5,'p900 enter p1700 a-1 p1800 space p900 a-x'))
    for kind,enabled,seconds,keys in plans:
        raw=bytearray(prm(port=3,baud=5,soft=0,hard=0))
        struct.pack_into('<HH',raw,0x1bc,enabled,seconds);struct.pack_into('<HH',raw,0x4e4,8,4);struct.pack_into('<H',raw,0x188,5)
        name='connect-alert-'+a.label+'-'+kind
        assert not (ROOT/'build/connection-dos'/name).exists()
        files={'TONE.COM':(out/'TONE.COM').read_bytes()};extra=''
        if kind=='script':
            sys.path.insert(0,str(ROOT/'src/aspect'))
            from compiler import compile_source
            from test_directory_key_bindings_dos import actions
            files['ALERT.ASX']=compile_source('proc main\ntransmit "SCRIPTALIVE^M"\nendproc\n')
            files['ACTIONS.KEY']=actions(b'D:\\ALERT.ASX',0);extra=' /T:D:\\ACTIONS.KEY'
        r=harness.run(name,'success',keys,prm=bytes(raw),com=3,irq=5,cpu='8086',
            arguments='@D:\\TEST.PRM /D:CaseTest:23 /I:3'+extra,files=files,auxiliary=('TONE',),working_drive='d')
        assert r['passed'],r
        folder=ROOT/'build/connection-dos'/name
        magic,samples,high,edges,banner,final=struct.unpack('<6H',(folder/'TONE.BIN').read_bytes())
        assert magic==0xca17 and samples>20 and final==0
        if not enabled:assert high==edges==banner==0
        else:assert high>0 and edges>=2 and banner>0
        wire=(folder/'serial.bin').read_bytes()
        if kind=='key':assert wire.count(b'q')==1
        if kind=='script':assert wire.count(b'SCRIPTALIVE\r')==1
        cases.append(dict(case=kind,passed=True,samples=samples,high_ticks=high,beep_edges=edges,banner_while_sounding=banner,final_gate=final,harness_result=str((folder/'result.json').relative_to(ROOT))))
    assert cases[1]['high_ticks']>cases[2]['high_ticks'] and cases[1]['beep_edges']>cases[2]['beep_edges']
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    result=dict(passed=True,cases=cases,binary_sha256=sha(a.terminal),
        sources={n:sha(ROOT/n) for n in ('standalone/test_connect_alert_dos.py','standalone/connect_alert_watch.asm','standalone/test_connection_dos.py','standalone/test_terminal.py')},
        scope=__doc__+' Passive timer reads port61 and video, without patching product code or supplying replies for it. Checks real PRM startup policy, quiet/expiry/keypress and PIT quiet after exit. Mixer muted: not acoustic or physical modem acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS:',len(cases),'actual DOS connect/speaker/UART cases')
if __name__=='__main__':main()
