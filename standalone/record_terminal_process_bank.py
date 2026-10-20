#!/usr/bin/env python3
"""Bind bank placement, real DOS/UI/exit workflows and source-only proof."""
import argparse,json,re,struct
from pathlib import Path
from build_aspect_process import ROOT,sha
def read(p):return json.loads(p.read_text())
def current(sources):
    for n,h in sources.items():assert sha(ROOT/n)==h,n
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mouse-label',required=True);args=p.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+',args.mouse_label)
    exits=read(ROOT/'docs/validation/terminal-process-bank-exit.json')
    assert exits['passed'] and exits['banked_process'] and exits['checker_sha256']==sha(ROOT/'standalone/record_terminal_exit.py')
    current(exits['source_proof']['sources'])
    assert len(exits['source_proof']['products'])==22
    banks={}
    for name in ['terminal-process-bank','terminal-process-bank-mouse']:
        out=ROOT/'build'/name;bank=read(out/'bank-checks.json');assert bank['passed'];current(bank['sources'])
        assert bank['binary_sha256']==sha(out/'TERMINAL.EXE') and bank['checker_sha256']==sha(ROOT/'standalone/check_terminal_process_bank.py')
        objects=[f for f in out.glob('unit-*.obj') if b'src/process/dos_exec.asm' in f.read_bytes()]
        assert len(objects)==1 and bank['object_sha256']==sha(objects[0])
        assert bank['listing_sha256']==sha(out/'process-bank-audit.dis')
        banks[name]={n:bank[n] for n in ['binary_sha256','object_sha256','near_code_saved','near_spare','bank_bytes','transfers']}
    component=ROOT/'build/process-bank';manifest=read(component/'manifest.json');current(manifest['sources'])
    for n,h in manifest['outputs'].items():assert sha(component/n)==h,n
    model=read(component/'checks.json');dos=read(component/'dos-results.json')
    assert model['passed'] and model['banked_process'] and model['inputs']==68
    assert model['binary_sha256']==manifest['outputs']['PROCESS.EXE']
    assert model['checker_sha256']==sha(ROOT/'standalone/check_process.py') and model['loader_sha256']==sha(ROOT/'standalone/dos_image.py')
    assert dos['passed'] and dos['banked_process'] and all(dos['checks'].values())
    assert dos['checker_sha256']==sha(ROOT/'standalone/test_process_dos.py')
    for n,h in dos['outputs'].items():assert h==manifest['outputs'][n]
    tail=b' ALPHA.TXT BETA.DAT'
    assert (component/'CHILD.OUT').read_bytes()==bytes([len(tail)])+tail+b'\r'
    assert (component/'ENV.OUT').read_bytes()==b'SYNTHETIC-ENV'
    fcbs=(component/'FCBS.OUT').read_bytes();assert fcbs[1:12]==b'ALPHA   TXT' and fcbs[17:28]==b'BETA    DAT'
    shell=read(ROOT/'build/program-process-bank-dos/checks.json')
    assert shell['passed'] and shell['banked_process'] and len(shell['cases'])==5
    assert shell['checker_sha256']==sha(ROOT/'standalone/test_program_process_dos.py')
    for n,h in shell['outputs'].items():assert h==manifest['outputs'][n]
    for case in shell['cases']:
        folder=ROOT/'build/program-process-bank-dos'/case['case']
        assert case['passed'] and all(case['checks'].values())
        assert struct.unpack('<4H',(folder/'RESULT.OUT').read_bytes())[:3]==(0,0,0)
        assert (folder/'ENV.OUT').read_bytes()==b'SYNTHETIC-ENV'
    mouse_folder=ROOT/'build/terminal-mouse-tests'/args.mouse_label;mouse=read(mouse_folder/'checks.json')
    assert mouse['passed'] and mouse['sources_unchanged'];current(mouse['sources'])
    assert mouse['binary_sha256']==sha(ROOT/'build/terminal-process-bank-mouse/TERMINAL.EXE')
    for n,h in mouse['sources'].items():assert sha(mouse_folder/'sources'/n)==h,n
    assert {c['case'] for c in mouse['cases']}=={'program','quarantine','startup-repair','live-save'}
    observed=[]
    for case in mouse['cases']:
        assert case['passed'] and all(case['checks'].values());folder=mouse_folder/case['case']
        assert case==read(folder/'result.json') and case['production_binary_sha256']==mouse['binary_sha256']
        assert sha(folder/'TERMINAL.EXE')==mouse['binary_sha256']
        text=(folder/'MOUSE.OUT').read_text()
        m=re.fullmatch(r'MOUSEOBS checks=(\d+) failures=(\d+) child=(\d+) retained=(\d+) driver_bytes=(\d+) stage=(\d+) callback=(\d+) registrations=(\d+)\s*',text)
        assert m;checks,failures,child,retained,size,stage,callback,registrations=map(int,m.groups())
        assert failures==0 and size==576
        assert (child,retained)==((0x030e,1) if case['case']=='quarantine' else (0,0))
        if case['case']=='quarantine':assert callback==1 and stage==1
        if case['case'] in ['live-save','startup-repair']:assert stage==2 and (folder/'PCPLUS.SCR').is_file()
        observed.append(dict(case=case['case'],checks=checks,child=child,retained=retained,stage=stage,report_sha256=sha(folder/'MOUSE.OUT')))
    baseline=read(ROOT/'docs/validation/application-components-source-build.json')['outputs']
    controls={}
    for n in ['process/PROCESS.EXE','process/PROGRAM.EXE','process/CHILD.COM']:
        controls[n]=sha(ROOT/'build'/n);assert baseline[n]['sha256']==controls[n]
    controls.update(exits['stock_terminals_unchanged'])
    result=dict(passed=True,whole_application_gates_closed=[],banks=banks,component_model=model,component_DOS=dos,
        command_processor=shell,mouse_workflows=observed,mouse_checks=sum(c['checks'] for c in observed),unchanged_controls=controls,
        exit_receipt_sha256=sha(ROOT/'docs/validation/terminal-process-bank-exit.json'),source_products=exits['source_proof']['products'],
        evidence={str(component.relative_to(ROOT)):{n:sha(component/n) for n in ['checks.json','dos-results.json','CHILD.OUT','ENV.OUT','FCBS.OUT']},
            str(mouse_folder.relative_to(ROOT)):{'checks.json':sha(mouse_folder/'checks.json')}},
        checker_sha256=sha(Path(__file__)),limits=['Process-bank entry retains the three-word near ABI through explicit copies; modeled kernel faults remain separate from actual DOS evidence',
            'Final guard audits DOS-restored22/23/24 targets from the PSP; this is not asynchronous Ctrl-Break or critical-error trapping',
            'Mouse quarantine repair/reclaim occurs only in the independent controlled observer, not the product',
            'Application-wide traps, full ownership, normal publication and physical/BBS acceptance remain open'])
    (ROOT/'docs/validation/terminal-process-bank.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Terminal process bank:68 modeled inputs,actual DOS/5 shell routes,4 mouse workflows and22 source products audited')
if __name__=='__main__':main()
