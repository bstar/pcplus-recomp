#!/usr/bin/env python3
"""Production nested source compilation under the full helper parent, without a TSR."""
import argparse,hashlib,json,shutil,struct,sys
from pathlib import Path
import test_connection_dos as connection
from modem_fixtures import fixture
from test_directory_key_bindings_dos import actions
ROOT=connection.ROOT
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--port',type=int,choices=[1,2],required=True)
    p.add_argument('--case',choices=['explicit','fallback','chain','rejected'],required=True)
    p.add_argument('--terminal',type=Path);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    products={'TERMINAL.EXE':'terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-apply',
              'ASPECT.EXE':'aspect-register-parent','ASPCOMP.EXE':'aspect-compiler-dos'}
    sources={};hashes={}
    for leaf,folder in products.items():
        src=a.terminal.resolve() if leaf=='TERMINAL.EXE' and a.terminal else ROOT/'build'/folder/leaf
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
    files={leaf:text.encode('cp437')for leaf,text in scripts.items()};files['ACTIONS.KEY']=actions(path,0)
    connection.BINARY=out/'TERMINAL.EXE';label='heap-'+out.name
    report=connection.run(label,'success','p2000 a-1 p6500 o b s e r v e enter p800 r e a d y p700 a-x',
        prm=bytes(raw),com=a.port,working_drive='d',files=files,cpu='8086',
        arguments='@D:\\TEST.PRM /D:CaseTest:23 /T:D:\\ACTIONS.KEY',
        online_triggers=[(b'observe\r',b'\x1b[5n')])
    result=ROOT/'build/connection-dos'/label;wire=(result/'serial.bin').read_bytes()
    assert report['passed'] and wire.index(b'observe\r')<wire.rindex(b'\x1b[0n')
    assert wire.count(b'COMPILED\r')==(0 if a.case=='rejected' else 1)
    for leaf,data in expected.items():assert (result/leaf).read_bytes()==data,leaf
    if a.case=='rejected':assert not (result/'LOGON.ASX').exists()
    assert (result/'TEST.PRM').read_bytes()==raw
    assert (result/'BEFORE.BIN').read_bytes()==(result/'AFTER.BIN').read_bytes()
    for name in ['standalone/test_nested_compiler_memory_dos.py','standalone/test_connection_dos.py',
                 'standalone/test_terminal.py','standalone/modem_fixtures.py','standalone/test_directory_key_bindings_dos.py',
                 'src/aspect/compiler.py']:sources[name]=sha(ROOT/name)
    data=dict(passed=True,case=a.case,port=a.port,products=hashes,sources=sources,connection=report,
        artifacts={str(f.relative_to(ROOT)):sha(f)for folder in (out,result)for f in folder.iterdir()if f.is_file()},
        scope=__doc__+' Actual8086 COM1/2 modem, bare parent and sibling source-built compiler. '
        'Full-line nested parentheses, source/fallback/chained numeric+BREAK retention and rejected-source recovery. '
        'Exact ASX, no-TX-on-rejection, post-child RX/parser/TX, PRM and selected UART restoration checked. '
        'No physical or arbitrary-size compilation claim.')
    (out/'result.json').write_text(json.dumps(data,indent=2)+'\n');print('PASS nested source',a.case,a.port)
if __name__=='__main__':main()
