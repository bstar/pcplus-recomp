#!/usr/bin/env python3
"""Bind the compact DOS compiler to raw ownership, stack, serial and BBS evidence."""
import argparse,hashlib,json,re,struct,sys
from pathlib import Path
from record_hook_bbs import verify_case
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lab/bbs'))
from product_inputs import select_product
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source,CompileError

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def mz(p):
    raw=p.read_bytes();w=struct.unpack('<14H',raw[:28]);assert w[0]==0x5a4d
    file_bytes=w[2]*512-(512-w[1]if w[1]else 0);module=file_bytes-w[4]*16
    return dict(sha256=sha(p),file_bytes=len(raw),header_bytes=w[4]*16,module_bytes=module,
        minimum_process_bytes=(((module+15)//16)+w[5]+16)*16,initial_sp=w[8])

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--sync-label',required=True);p.add_argument('--enigma-label',required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    base=a.root.resolve();assert base.is_relative_to(ROOT/'build')
    terminal,_=select_product(ROOT/'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-apply/TERMINAL.EXE','TERMINAL.EXE')
    runner,_=select_product(ROOT/'build/aspect-register-parent/ASPECT.EXE','ASPECT.EXE')
    compiler,_=select_product(ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE','ASPCOMP.EXE')
    current=mz(compiler);prior=mz(ROOT/'build/hook-source-isolate/current/ASPCOMP.EXE')
    assert current['initial_sp']==prior['initial_sp']==24576 and current['minimum_process_bytes']<prior['minimum_process_bytes']
    listing=(compiler.parent/'ASPCOMP.map').read_text()
    segment,offset=re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})\s+__amblksiz\s*$',listing,re.M|re.I)[0]
    position=current['header_bytes']+int(segment,16)*16+int(offset,16)
    assert struct.unpack_from('<H',compiler.read_bytes(),position)[0]==512
    sources={};custody={}
    def bind(folder):
        for path in folder.rglob('*'):
            if path.is_file():custody[str(path.relative_to(ROOT))]=sha(path)
    def source_set(mapping):
        for name,digest in mapping.items():
            assert sha(ROOT/name)==digest,name
            assert name not in sources or sources[name]==digest,name
            sources[name]=digest
    workspace=load(base/'workspace-api-02/checks.json');assert workspace['passed'] and workspace['borrowed_cycles']==100
    assert workspace['summary']=='WORKSPACE 11306 bytes VALUE 18 NODE 24 CHECKS 12746 FAILURES 0'
    source_set(workspace['sources']);assert workspace['checker_sha256']==sha(ROOT/'standalone/check_aspect_compiler_workspace.py')
    bind(base/'workspace-api-02')
    stack_root=base/'final-stack-check-02';stack=load(stack_root/'stack-checks.json');corpus=load(stack_root/'checks.json')
    assert stack['passed'] and corpus['passed'] and stack['compiler_sha256']==corpus['binary_sha256']==sha(compiler)
    assert stack['candidate_CLI_stack_bytes']==stack['checked_CLI_stack_bytes']==24576
    assert stack['checked_API_stack_bytes']==16384 and stack['checked_CLI_cases']==18
    assert stack['checker_sha256']==sha(ROOT/'standalone/check_aspect_compiler_stack.py')
    assert corpus['checker_sha256']==sha(ROOT/'standalone/check_aspect_compiler_dos.py')
    cases=load(stack_root/'cases.json');assert sha(stack_root/'cases.json')==corpus['case_manifest_sha256']
    assert len(cases)==2043 and corpus['accepted']==1077 and corpus['rejected']==966
    for index,record in enumerate(cases):
        raw=(stack_root/'tests'/f'P{index:05}.ASP').read_bytes()
        assert hashlib.sha256(raw).hexdigest()==record['source_sha256']
        try:expected=compile_source(raw.decode('cp437'))
        except (CompileError,TypeError,OverflowError):expected=None
        actual=(stack_root/'tests'/f'P{index:05}.ASX').read_bytes()
        assert hashlib.sha256(actual).hexdigest()==record['asx_sha256']
        assert record['accepted'] == (expected is not None)
        if record['accepted']:assert expected is not None and actual==expected
    for stem,case in zip(sorted((stack_root/'checked-cli').glob('D*.ASP')),stack['depth_cases'].values()):
        assert sha(stem)==case['source_sha256']
        assert stem.with_suffix('.ASX').read_bytes()==compile_source(stem.read_bytes().decode('cp437'))
    assert b'stack overflow' in (stack_root/'checked-cli/STKVIDEO.BIN').read_bytes()[::2].lower()
    assert not (stack_root/'checked-cli/OVR.ASX').exists()
    bind(stack_root)
    bare=[]
    for port in (1,2):
        for case in ('explicit','fallback','chain','rejected'):
            folder=base/f'final-bare-{port}-{case}';r=load(folder/'result.json')
            assert r['passed'] and r['port']==port and r['case']==case
            assert r['products']=={'TERMINAL.EXE':sha(terminal),'ASPECT.EXE':sha(runner),'ASPCOMP.EXE':sha(compiler)}
            assert r['connection']['cpu']=='8086' and all(r['connection']['checks'].values())
            source_set(r['sources'])
            for name,digest in r['artifacts'].items():assert sha(ROOT/name)==digest;custody[name]=digest
            output=ROOT/'build/connection-dos'/('heap-'+folder.name);wire=(output/'serial.bin').read_bytes()
            assert wire.index(b'observe\r')<wire.rindex(b'\x1b[0n')
            assert wire.count(b'COMPILED\r')==(case!='rejected')
            assert (output/'BEFORE.BIN').read_bytes()==(output/'AFTER.BIN').read_bytes()
            for path in output.glob('*.ASP'):
                if case=='rejected':assert not path.with_suffix('.ASX').exists()
                else:assert path.with_suffix('.ASX').read_bytes()==compile_source(path.read_bytes().decode('cp437'))
            bind(folder);bare.append(dict(port=port,case=case,checks=r['connection']['checks']))
    bbs=[]
    for server,label,delay in [('synchronet',a.sync_label,0),('enigma',a.enigma_label,30)]:
        r=verify_case(server,label,'accept',delay,terminal,runner,expected_cpu='386')
        assert r['source_compilation'] and r['editor_passed']
        stage=ROOT/'build/bbs-lab/script-login'/label;report=load(stage/'checks.json')
        raw=(ROOT/'build/bbs-lab/results'/server/label/'SCRIPT.BIN').read_bytes()
        magic,bits,ticks,segment=struct.unpack('<4H',raw[:8])
        assert len(raw)==4008 and magic==0x4d43 and ticks and not bits&6 and segment>=0xa000
        assert report['observer_high'] and report['observer_segment']==segment
        assert (stage/'LOGON.ASX').read_bytes()==compile_source((stage/'LOGON.ASP').read_bytes().decode('cp437'))
        source_set(r.pop('sources'));custody.update(r.pop('artifacts'));bbs.append(dict(**r,cpu='386',observer_segment=segment))
    regressions={}
    for name in ('source-regressions','serial-regressions'):
        r=load(base/name/'checks.json');assert r['passed'] and r['compiler_sha256']==sha(compiler)
        assert r['checker_sha256']==sha(ROOT/('standalone/check_aspect_source_compile.py'if name=='source-regressions'else 'standalone/check_aspect_source_serial_dos.py'))
        if name=='serial-regressions':assert len(r['cases'])==7 and all(c['passed']and all(c['checks'].values())for c in r['cases'])
        else:assert r['DOS_summary']=='SOURCE_EXEC 22 cases 223 checks 0 failures'
        regressions[name]=r;bind(base/name)
    proof=load(base/'source-proof-02/result.json');assert proof['passed'] and not proof['original_inputs']
    assert proof['source_files']==713 and len(proof['products'])==7
    source_set(proof['sources'])
    for name,digest in proof['products'].items():assert sha(ROOT/name)==digest
    bind(base/'source-proof-02')
    for name in ['standalone/record_nested_compiler_memory.py','standalone/record_hook_bbs.py','Makefile']:
        sources[name]=sha(ROOT/name)
    result=dict(passed=True,compiler=current,prior_compiler=prior,CLI_stack_bytes=24576,CRT_heap_quantum=512,
        workspace=workspace['summary'],grammar_cases=2043,accepted=1077,rejected=966,
        checked_CLI_depth_cases=18,checked_API_stack_bytes=16384,bare_parent_cases=bare,BBS=bbs,
        regressions=regressions,original_free_products=proof['products'],source_files=713,sources=sources,artifacts=custody,
        limitations=['Bare serial cases execute8086 with no resident observer. BBS cases execute386 and require the passive observer in upper memory.',
            'Low-conventional-memory8086 BBS observer trials remain failed evidence; this is not an arbitrary-driver memory guarantee.',
            'Immediate ENiGMA framing, full native compiler/application families and physical hardware remain open.',
            'The card was not remounted or updated during this source work.'],
        scope='Compact workspace CLI under the full helper-enabled parent; unchanged24KB reserved stack and253-byte language bounds. '
            'Raw ASX, guarded stack, borrowed ownership, UART state, post-child query, actual source login/helper/editor and clean-source reproduction checked.')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS nested compiler memory:2043 grammar,18 CLI-depth,8 bare-parent,2 BBS,22 source and7 UART cases;713 sources/7 products')
if __name__=='__main__':main()
