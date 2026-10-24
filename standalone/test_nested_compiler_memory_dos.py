#!/usr/bin/env python3
"""Production nested source compilation under the full helper parent, without a TSR."""
import argparse,hashlib,json,shutil,struct,sys
from pathlib import Path
import test_connection_dos as connection
from modem_fixtures import fixture
from directory_fixtures import directory as directory_fixture
from test_directory_key_bindings_dos import actions
ROOT=connection.ROOT
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--port',type=int,choices=[1,2],required=True)
    p.add_argument('--case',choices=['explicit','fallback','chain','rejected'],required=True)
    p.add_argument('--terminal',type=Path);p.add_argument('--runner',type=Path)
    p.add_argument('--irq',type=int,choices=[3,4,5,7])
    p.add_argument('--chooser',action='store_true',help='Select through startup chooser, enter/cancel its editor, then run the nested compiler')
    p.add_argument('--splash-key',action='store_true',help='Dismiss the explicitly selected branded parent splash')
    p.add_argument('--log-collisions',type=int,default=0,help='Precreate synthetic LPC log names to verify collision preservation')
    a=p.parse_args()
    assert 0<=a.log_collisions<=999
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    products={'TERMINAL.EXE':'terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-apply',
              'ASPECT.EXE':'aspect-register-parent','ASPCOMP.EXE':'aspect-compiler-dos'}
    sources={};hashes={}
    for leaf,folder in products.items():
        src=a.terminal.resolve() if leaf=='TERMINAL.EXE' and a.terminal else ROOT/'build'/folder/leaf
        if leaf=='ASPECT.EXE' and a.runner:
            assert a.runner.name=='ASPECT.EXE';src=a.runner.resolve()
        m=json.loads((src.parent/'manifest.json').read_text())
        assert not m.get('original_inputs') and sha(src)==m['binary_sha256']
        for name,digest in m['sources'].items():assert sha(ROOT/name)==digest;sources[name]=digest
        shutil.copyfile(src,out/leaf);hashes[leaf]=sha(src)
    path=b'D:\\LOGON.ASX' if a.case=='fallback' else b'D:\\LOGON.ASP'
    source='integer i\nproc main\ni='+('('*120)+'1'+(')'*120)+'\ntransmit "COMPILED^M"\nendproc\n'
    scripts={'LOGON.ASP':source};expected={'LOGON.ASX':compile_source(source)}
    if a.case=='chain':
        source='integer value\nstring filename\nproc main\nvalue=42\nset break 1234\nfilename="D:\\NEXT.ASP"\nexecute filename\nendproc\n'
        end='integer value,saved\nproc main\nfetch break saved\nif value==42 && saved==1234\ntransmit "COMPILED^M"\nendif\nendproc\n'
        scripts={'LOGON.ASP':source,'NEXT.ASP':end};expected={leaf[:-3]+'ASX':compile_source(text)for leaf,text in scripts.items()}
    if a.case=='rejected':scripts={'LOGON.ASP':'proc main\nunknown\nendproc\n'};expected={}
    raw=bytearray(fixture(timeout=5));struct.pack_into('<H',raw,0,a.port-1);struct.pack_into('<HH',raw,0x4e4,8,4)
    struct.pack_into('<H',raw,0x174+(a.port-1)*2,0x3f8 if a.port==1 else 0x2f8)
    struct.pack_into('<H',raw,0x184+(a.port-1)*2,4 if a.port==1 else 3)
    if a.irq is not None:struct.pack_into('<H',raw,0x184+(a.port-1)*2,a.irq)
    files={leaf:text.encode('cp437')for leaf,text in scripts.items()};files['ACTIONS.KEY']=actions(path,0)
    existing_logs={f'LPC{i:05X}.LOG':b'PREEXISTING LOG '+str(i).encode()for i in range(a.log_collisions)}
    files.update(existing_logs)
    connection.BINARY=out/'TERMINAL.EXE';label='heap-'+out.parent.name+'-'+out.name
    keys=('p600 e p300 escape p300 enter 'if a.chooser else'')+('p900 enter 'if a.splash_key else'')+'p2000 a-1 p6500 o b s e r v e enter p800 r e a d y p700 a-x'
    selection=directory_fixture(entry=1,target=b'CaseTest:23',port=a.port)if a.chooser else None
    report=connection.run(label,'success',keys,directory=selection,
        prm=bytes(raw),com=a.port,working_drive='d',files=files,cpu='8086',
        arguments='@D:\\TEST.PRM '+('/E:D:\\TEST.DIR'if a.chooser else'/D:CaseTest:23')+' /T:D:\\ACTIONS.KEY',
        online_triggers=[(b'observe\r',b'\x1b[5n')],irq=a.irq)
    result=ROOT/'build/connection-dos'/label;wire=(result/'serial.bin').read_bytes()
    checks=dict(connection_passed=report['passed'],
        post_child_parser=b'observe\r'in wire and b'\x1b[0n'in wire and wire.index(b'observe\r')<wire.rindex(b'\x1b[0n'),
        expected_script_output=wire.count(b'COMPILED\r')==(0 if a.case=='rejected' else 1),
        PRM_unchanged=(result/'TEST.PRM').read_bytes()==raw,
        hardware_restored=(result/'BEFORE.BIN').read_bytes()==(result/'AFTER.BIN').read_bytes())
    if a.chooser:checks['chooser_then_program']=report['checks']['directory_expected_updates_only']
    for leaf,data in expected.items():checks['exact_'+leaf]=(result/leaf).exists()and(result/leaf).read_bytes()==data
    checks['existing_logs_preserved']=all((result/name).read_bytes()==data for name,data in existing_logs.items())
    checks['temporary_logs_retired']={p.name for p in result.glob('LPC*.LOG')}==set(existing_logs)
    if a.case=='rejected':checks['rejected_source_has_no_ASX']=not(result/'LOGON.ASX').exists()
    for name in ['standalone/test_nested_compiler_memory_dos.py','standalone/test_connection_dos.py',
                 'standalone/test_terminal.py','standalone/modem_fixtures.py','standalone/test_directory_key_bindings_dos.py',
                 'src/aspect/compiler.py']:sources[name]=sha(ROOT/name)
    data=dict(passed=all(checks.values()),checks=checks,case=('chooser-'+a.case if a.chooser else a.case),port=a.port,products=hashes,sources=sources,connection=report,splash_key_sent=a.splash_key,log_collisions=a.log_collisions,
        artifacts={str(f.relative_to(ROOT)):sha(f)for folder in (out,result)for f in folder.iterdir()if f.is_file()},
        scope=__doc__+' Actual8086 COM1/2 modem, bare parent and sibling source-built compiler. '
        'Full-line nested parentheses, source/fallback/chained numeric+BREAK retention and rejected-source recovery. '
        'Exact ASX, no-TX-on-rejection, post-child RX/parser/TX, PRM and selected UART restoration checked. '
        'No physical or arbitrary-size compilation claim.')
    (out/'result.json').write_text(json.dumps(data,indent=2)+'\n');print(('PASS'if data['passed']else'FAIL')+' nested source '+a.case+' '+str(a.port)+' '+json.dumps(checks))
    return 0 if data['passed']else 1
if __name__=='__main__':raise SystemExit(main())
