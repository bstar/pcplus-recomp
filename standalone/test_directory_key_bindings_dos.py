#!/usr/bin/env python3
"""Real DOS selected-directory KEY/KBD imports, precedence and startup failures."""
import argparse,hashlib,json,re,shutil,struct,sys
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import directory,prm
ROOT=harness.ROOT
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def actions(text,kind=3):
    raw=bytearray(540)
    for n in range(10):struct.pack_into('<H',raw,n*54,3)
    struct.pack_into('<H',raw,0,kind);raw[2:2+len(text)]=text;return bytes(raw)
def table(text):
    raw=bytearray(948*7);raw[6*948+16*12:6*948+16*12+len(text)]=text;return bytes(raw)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True)
    p.add_argument('--case',required=True,choices=['selected','script','environment','cwd-first','cli','fallback','missing','bad-key','bad-kbd','bad-name','blank'])
    p.add_argument('--port',type=int,choices=[1,2],default=1)
    p.add_argument('--process-bank',action='store_true');p.add_argument('--session-projection',action='store_true');p.add_argument('--register-handoff',action='store_true');a=p.parse_args();assert re.fullmatch('[A-Za-z0-9_-]+',a.label)
    if a.session_projection:assert a.process_bank
    if a.register_handoff:assert a.session_projection
    out=ROOT/'build/directory-keys'/a.label;out.mkdir(parents=True,exist_ok=False)
    parent_name='terminal-directory-keys'+('-process-bank' if a.process_bank else '')+('-session-capture-projection' if a.session_projection else '')
    if a.register_handoff:parent_name+='-bound-registers'
    parent=ROOT/'build'/parent_name/'TERMINAL.EXE';child=ROOT/('build/aspect-register-parent/ASPECT.EXE' if a.register_handoff else 'build/aspect-help-resource-parent/ASPECT.EXE')
    parent_manifest=json.loads((parent.parent/'manifest.json').read_text())
    assert parent_manifest['banked_process']==a.process_bank
    sources={}
    for binary in (parent,child):
        m=json.loads((binary.parent/'manifest.json').read_text());assert sha(binary)==m['binary_sha256']
        for n,h in m['sources'].items():assert n not in sources or sources[n]==h,n;sources[n]=h
    for n in ['standalone/test_directory_key_bindings_dos.py','standalone/test_connection_dos.py','standalone/test_terminal.py','standalone/directory_test_support.py','standalone/directory_fixtures.py','standalone/terminal_config_fixtures.py','standalone/modem_fixtures.py','src/aspect/compiler.py']:sources[n]=sha(ROOT/n)
    for n,h in sources.items():
        assert sha(ROOT/n)==h,n
        target=out/'sources'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,target)
    raw=bytearray(directory(port=a.port));raw[250+0x56:250+0x56+9]=b'actions\0\0';raw[250+0x5f:250+0x5f+9]=b'board\0\0\0\0'
    files={'ACTIONS.KEY':actions(b'DIRKEY^M'),'BOARD.KBD':table(b'DIRKBD')};env={};extra='';want_key=b'DIRKEY\r';want_map=b'DIRKBD'
    if a.case=='script':
        files['ACTIONS.KEY']=actions(b'TEST.ASX',0)
        files['TEST.ASX']=compile_source('proc main\ntransmit "DIRSCRIPT^M"\nendproc\n');want_key=b'DIRSCRIPT\r'
    if a.case in ('environment','cwd-first'):
        files.update({'ENV/ACTIONS.KEY':actions(b'ENVKEY^M'),'ENV/BOARD.KBD':table(b'ENVKBD')});env={'PCPLUS':'D:\\ENV'}
        if a.case=='environment':del files['ACTIONS.KEY'];del files['BOARD.KBD'];want_key=b'ENVKEY\r';want_map=b'ENVKBD'
    if a.case=='cli':
        files.update({'EXPLICIT.KEY':actions(b'CLIKEY^M'),'EXPLICIT.KBD':table(b'CLIKBD')});extra=' /T:D:\\EXPLICIT.KEY /K:D:\\EXPLICIT.KBD';want_key=b'CLIKEY\r';want_map=b'CLIKBD'
    if a.case=='fallback':del files['BOARD.KBD'];files['PCPLUS.KBD']=table(b'FALLBACK');want_map=b'FALLBACK'
    if a.case=='missing':files={};want_key=b'';want_map=b'\x1bOP'
    if a.case=='blank':raw[250+0x56:250+0x56+9]=b' \0ignore!';raw[250+0x5f:250+0x5f+9]=b'\0ignored!';files={};want_key=b'';want_map=b'\x1bOP'
    if a.case=='bad-key':files['ACTIONS.KEY']=bytes(539)
    if a.case=='bad-kbd':files['BOARD.KBD']=bytes(947)
    if a.case=='bad-name':raw[250+0x56:250+0x56+9]=b'CON\0\0\0\0\0\0'
    bad=a.case.startswith('bad-');settings=bytearray(prm(port=a.port));struct.pack_into('<HH',settings,0x4e4,8,4)
    package=out/'package';package.mkdir();shutil.copyfile(parent,package/'TERMINAL.EXE');shutil.copyfile(child,package/'ASPECT.EXE')
    harness.BINARY=package/'TERMINAL.EXE'
    result=harness.run('dirkeys-'+a.label,'reject' if bad else 'success','p3000 a-1 p1800 f1 p300 r e a d y p600 a-x',
        directory=bytes(raw),prm=bytes(settings),com=a.port,working_drive='d',environment=env,expected=7 if bad else 0,
        arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1'+extra,files=files)
    folder=ROOT/'build/connection-dos'/('dirkeys-'+a.label);wire=(folder/'serial.bin').read_bytes()
    if not bad:
        result['checks']['directory_keyboard_wire']=(want_key+want_map+b'ready') in wire
        result['checks']['unselected_keys_absent']=all(x not in wire for x in [b'DIRKEY\r',b'ENVKEY\r',b'CLIKEY\r',b'DIRSCRIPT\r'] if x!=want_key)
    result['checks']['sources_current']=all(sha(ROOT/n)==h for n,h in sources.items())
    result.update(passed=all(result['checks'].values()),banked_process=a.process_bank,sources=sources,case=a.case,port=a.port,expected_wire_hex=(want_key+want_map+b'ready').hex() if not bad else '',child_sha256=sha(child),scope='Actual DOS selected-directory startup import, bounded KEY/KBD lookup and unchanged resources; synthetic files/modem only. Explicit CLI precedence, missing fallback and pre-UART rejection are maintained policy; physical hardware/native post-connect parity remain open.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed'],{k:result[k] for k in ('case','checks','errors')}
    print('PASS',a.case,flush=True)
if __name__=='__main__':main()
