#!/usr/bin/env python3
"""Audit terminal exit lifetime using raw witnesses, linked maps and rebuilds."""
import argparse,json,re,struct
from pathlib import Path
from build_aspect_process import ROOT,sha
def read(p):return json.loads(p.read_text())
def current(sources):
    for n,h in sources.items():assert sha(ROOT/n)==h,n
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dos-label',action='append',required=True)
    p.add_argument('--normal-label',action='append',required=True)
    p.add_argument('--retry-label',action='append',required=True)
    p.add_argument('--source-label',required=True)
    args=p.parse_args()
    for label in [*args.dos_label,*args.normal_label,*args.retry_label,args.source_label]:assert re.fullmatch(r'[A-Za-z0-9_-]+',label)
    dos=[];seen=set();evidence={}
    for label in args.dos_label:
        folder=ROOT/'build/terminal-exit-tests'/label;run=read(folder/'result.json')
        assert run['passed'] and run['checker_sha256']==sha(ROOT/'standalone/test_terminal_exit_dos.py');current(run['sources'])
        for n,h in run['sources'].items():assert sha(folder/'sources'/n)==h,n
        for case in run['cases']:
            sub=folder/case['case'];mode=case['mode'];initial=case['initial_break'];mouse=case['mouse'];key=(mouse,mode,initial)
            assert key not in seen;seen.add(key)
            assert case==read(sub/'result.json') and case['passed'] and all(case['checks'].values())
            product='terminal-exit-mouse-probe-' if mouse else 'terminal-exit-probe-'
            product=ROOT/'build'/(product+str(mode));manifest=read(product/'manifest.json')
            assert sha(sub/'TERMINAL.EXE')==sha(product/'TERMINAL.EXE')==case['child_sha256']
            assert sha(sub/'TEOBS.EXE')==sha(folder/('parent-'+str(mode))/'TEOBS.EXE')==case['parent_sha256']
            syms={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',(product/'terminal.map').read_text(),re.M|re.I)}
            record=struct.unpack('<16H',(sub/'TERMEXIT.BIN').read_bytes())
            assert record[:2]==(0x5445,mode) and record[2]!=0
            assert record[3]==manifest['memory_layout']['retained_parent_paragraphs'] and record[4]>=record[3]
            assert record[5:7]==(1 if mode==1 else 2 if mode==2 else 0,0x60 if mode==1 else 0xffff)
            cseg,coff=syms['terminal_exit_probe_isr'];dseg,hits=syms['terminal_exit_probe_hits']
            assert record[7:11]==(coff,record[2]+16+cseg,hits,record[2]+16+dseg)
            assert record[11:13]==(record[2],0)
            match=re.fullmatch(r'TERMEXIT mode=(\d+) break=(\d+) checks=(\d+) failures=(\d+) status=(\d+) retained=(\d+) pressure=(\d+)\s*',(sub/'TERMPAR.OUT').read_text())
            assert match
            m,b,checks,failures,status,retained,pressure=map(int,match.groups())
            assert (m,b)==(mode,initial) and failures==0 and checks>=13
            assert retained==int(mode in [1,2]) and status==(0x030f if retained else 0)
            assert not retained or pressure>0
            assert b'ready' in (sub/'serial.bin').read_bytes()
            assert (sub/'BEFORE.BIN').read_bytes()==(sub/'AFTER.BIN').read_bytes()
            dos.append(dict(label=label,mouse=mouse,mode=mode,initial_break=initial,checks=checks,status=status,
                PSP=record[2],floor_paragraphs=record[3],retained_paragraphs=record[4],reason=record[5],vector=record[6],pressure_paragraphs=pressure,
                startup_gateway_hex=struct.pack('<3H',*record[13:])[:5].hex()))
            evidence[str(sub.relative_to(ROOT))]={n:sha(sub/n) for n in ['TERMEXIT.BIN','TERMPAR.OUT','serial.bin','BEFORE.BIN','AFTER.BIN','result.json']}
    assert seen=={(m,p,b) for m in [False,True] for p in range(4) for b in [0,1]}
    normals=[];normal_seen=set();retries=[];retry_seen=set()
    for retry,labels in [(False,args.normal_label),(True,args.retry_label)]:
        for label in labels:
            candidates=[ROOT/'build'/(name+suffix)/label for name in ['aspect-parent-break','aspect-parent-exit'] for suffix in ['-guarded','-mouse-guarded','-retry-guarded','-mouse-retry-guarded']]
            folders=[f for f in candidates if (f/'result.json').exists()];assert len(folders)==1,label
            folder=folders[0];run=read(folder/'result.json')
            assert run['passed'] and run['terminal_exit_guard'] and run['same_session_retry']==retry
            assert run['checker_sha256']==sha(ROOT/'standalone/test_aspect_parent_process_dos.py');current(run['source_hashes'])
            for n,h in run['source_hashes'].items():assert sha(folder/'sources'/n)==h,n
            parent=ROOT/'build'/('terminal-exit-mouse' if run['experimental_mouse'] else 'terminal-exit')/'TERMINAL.EXE'
            assert run['parent_sha256']==sha(parent)
            for case in run['cases']:
                sub=folder/case['case'];key=(run['experimental_mouse'],case['case'])
                assert case==read(sub/'result.json') and case['passed'] and all(case['checks'].values())
                assert sha(sub/'TERMINAL.EXE')==sha(parent)
                entry=dict(label=label,mouse=key[0],case=key[1],checks=len(case['checks']))
                if retry:
                    assert key not in retry_seen;retry_seen.add(key)
                    assert case['retained_words'][10]==0x030a and case['retry_probe']['status']==0
                    assert case['retry_probe']['callback_after']==2 and (sub/'RETRY.OUT').read_bytes()==b'retry-owned'
                    retries.append(entry)
                else:
                    assert key not in normal_seen;normal_seen.add(key);normals.append(entry)
                    assert b'ASPECT memory retained.' not in (sub/'SCREEN.BIN').read_bytes()[::2]
                evidence[str(sub.relative_to(ROOT))]={n:sha(sub/n) for n in ['RENDER.BIN','serial.bin','SCREEN.BIN','result.json']}
    expected={'G','T','W','R','F'}|{f'full-{p}-{f}' for p in [1,2] for f in 'NSHB'}
    assert normal_seen=={(m,n) for m in [False,True] for n in expected}
    assert retry_seen=={(False,'Q-1-H'),(True,'Q-2-B')}
    model=read(ROOT/'build/terminal-exit-mouse/model-checks.json')
    assert model['passed'] and model['IVT_slots']==256 and len(model['boundaries'])==6 and len(model['held_decisions'])==9
    assert len(model['rejected_admissions'])==10 and len(model['leases'])==5 and model['normal_decisions']==2
    assert len(model['gateways'])==5
    assert model['checker_sha256']==sha(ROOT/'standalone/check_terminal_exit.py')
    assert model['loader_sha256']==sha(ROOT/'standalone/dos_image.py')
    assert model['binary_sha256']==sha(ROOT/'build/terminal-exit-mouse/TERMINAL.EXE')
    proof=read(ROOT/'build/terminal-exit-source'/args.source_label/'result.json')
    assert proof['passed'] and len(proof['products'])==14 and proof['original_inputs']==[];current(proof['sources'])
    assert proof['checker_sha256']==sha(ROOT/'standalone/check_terminal_exit_source.py')
    for n,v in proof['products'].items():assert v['expected']==v['actual']==sha(ROOT/'build'/n/'TERMINAL.EXE'),n
    baseline=read(ROOT/'docs/validation/parent-retry.json')['source_proof']['products']
    stock={n:sha(ROOT/'build'/n/'TERMINAL.EXE') for n in ['terminal','terminal-process','terminal-mouse','terminal-mouse-process']}
    for n,h in stock.items():assert baseline[n+'/TERMINAL.EXE']['expected']==h,n
    memory={n:read(ROOT/'build'/n/'manifest.json')['memory_layout'] for n in ['terminal-exit','terminal-exit-mouse']}
    result=dict(passed=True,whole_application_gates_closed=[],DOS_routes=dos,DOS_parent_checks=sum(c['checks'] for c in dos),normal_routes=normals,
        normal_checks=sum(c['checks'] for c in normals),retained_retry_controls=retries,model=model,source_proof=proof,
        stock_terminals_unchanged=stock,memory=memory,evidence=evidence,checker_sha256=sha(Path(__file__)),
        limits=['Opt-in final DOS4C boundary; asynchronous DOS Ctrl-Break/critical-error interception remains open',
            'MCB corruption and invalid-context holding paths are instruction models, not live DOS-kernel corruption tests',
            'Busy/foreign-PSP diagnostics supply controlled state/tokens rather than an actual abandoned child process',
            'IVT scan covers the full validated main PSP block; it is not a universal ownership proof for foreign driver tables or arbitrary heap-generated callbacks',
            'Existing mouse-owner quarantine still has its own DOS31 error14 path; this guard runs after successful mouse close',
            'Retained allocations are not automatically reclaimed; normal publication, full lifetime and physical/BBS acceptance remain open'])
    (ROOT/'docs/validation/terminal-exit.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Terminal exit:16 DOS cases,26 normal workflows,2 retained retries,linked model and14 source products audited')
if __name__=='__main__':main()
