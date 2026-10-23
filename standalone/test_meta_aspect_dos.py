#!/usr/bin/env python3
"""Actual DOS KEY ASPECT invocation, serial handback and ordinary terminal resume."""
import argparse,hashlib,json,re,shutil,struct,sys
from pathlib import Path
import test_connection_dos as harness
ROOT=harness.ROOT
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source
from directory_fixtures import prm

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--label',required=True);ap.add_argument('--case',choices=['serial','missing','empty','repeat','source','bad-script'],required=True)
    ap.add_argument('--port',type=int,choices=[1,2],default=1);a=ap.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',a.label)
    out=ROOT/'build/aspect-keys'/a.label;out.mkdir(parents=True,exist_ok=False)
    terminal=ROOT/'build/terminal-aspect-keys/TERMINAL.EXE';child=ROOT/'build/aspect-help-resource-parent/ASPECT.EXE'
    sources={}
    for binary in (terminal,child):
        m=json.loads((binary.parent/'manifest.json').read_text());assert sha(binary)==m['binary_sha256']
        for n,h in m['sources'].items():assert n not in sources or sources[n]==h,n;sources[n]=h
    dependencies=['standalone/test_meta_aspect_dos.py','standalone/test_connection_dos.py','standalone/test_terminal.py','standalone/modem_fixtures.py','standalone/directory_test_support.py','standalone/directory_fixtures.py','src/aspect/compiler.py']
    for n in dependencies:sources[n]=sha(ROOT/n)
    if a.case=='source':
        compiler=ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE'
        m=json.loads((compiler.parent/'manifest.json').read_text());assert sha(compiler)==m['binary_sha256']
        for n,h in m['sources'].items():assert n not in sources or sources[n]==h,n;sources[n]=h
    for n,h in sources.items():
        assert sha(ROOT/n)==h,n
        target=out/'source'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
    key=bytearray(540)
    for i in range(10):struct.pack_into('<H',key,54*i,3)
    index=9 if a.port==2 else 0;struct.pack_into('<H',key,54*index,0)
    name=b'TEST.ASP' if a.case=='source' else b'TEST' if a.case=='serial' else b'TEST.ASX'
    if a.case!='empty':key[54*index+2:54*index+2+len(name)]=name
    script='proc main\ntransmit "KEYSTART^M"\n'
    if a.case=='serial':script+='waitfor "MATCH" 5\n'
    script+='transmit "KEYDONE^M"\nendproc\n'
    files={'TEST.KEY':bytes(key)}
    if a.case=='source':files.update({'TEST.ASP':script.encode(),'ASPCOMP.EXE':compiler.read_bytes()})
    else:files['TEST.ASX']=bytes.fromhex('00 cf fd 94') if a.case=='bad-script' else compile_source(script)
    if a.case!='missing':files['ASPECT.EXE']=child.read_bytes()
    invoke='a-0' if index==9 else 'a-1'
    keys='p3000 '+invoke+' p2200 '
    if a.case in ('missing','bad-script'):keys+='space p500 '
    if a.case=='repeat':keys+=invoke+' p2200 '
    keys+='r e a d y p700 a-x'
    settings=bytearray(prm(port=a.port));struct.pack_into('<HH',settings,0x4e4,8,4)
    package=out/'package';package.mkdir()
    shutil.copyfile(terminal,package/'TERMINAL.EXE')
    if a.case!='missing':shutil.copyfile(child,package/'ASPECT.EXE')
    if a.case=='source':shutil.copyfile(compiler,package/'ASPCOMP.EXE')
    harness.BINARY=package/'TERMINAL.EXE'
    result=harness.run('aspect-key-'+a.label,'success',keys,com=a.port,prm=bytes(settings),working_drive='d',
        arguments='@D:\\TEST.PRM /D:CaseTest:23 /T:D:\\TEST.KEY',files=files,
        online_updates=[(4,b'MATCH\x1b[10;1HKEY REMAINDER')] if a.case=='serial' else ())
    folder=ROOT/'build/connection-dos'/('aspect-key-'+a.label);wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes()[::2]
    count=2 if a.case=='repeat' else 0 if a.case in ('missing','empty','bad-script') else 1
    result['checks'].update(script_transmit_count=wire.count(b'KEYSTART\r')==count and wire.count(b'KEYDONE\r')==count,
        ordinary_keyboard_resume=b'ready' in wire,source_current=all(sha(ROOT/n)==h for n,h in sources.items()),
        terminal_current=sha(terminal)==result['binary_sha256'],child_current=sha(child)==json.loads((child.parent/'manifest.json').read_text())['binary_sha256'])
    if a.case=='serial':result['checks']['unread_serial_suffix_reaches_parent']=screen[9*80:9*80+13]==b'KEY REMAINDER'
    if a.case=='source':result['checks']['DOS_compiler_published_ASX']=(folder/'TEST.ASX').read_bytes()==compile_source(script)
    result.update(passed=all(result['checks'].values()),sources=sources,child_sha256=sha(child),case=a.case,port=a.port,
        scope='Actual DOS optional KEY ASPECT action, shared direct Script owner, real maintained interpreter and serial resume. Synthetic UART peer, no original executable or user files. Physical hardware and HOOK remain unverified.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    assert result['passed'],{k:result[k] for k in ('case','checks','errors')}
    print('PASS',a.case,'COM'+str(a.port),flush=True)
if __name__=='__main__':main()
