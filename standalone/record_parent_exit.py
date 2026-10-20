#!/usr/bin/env python3
"""Audit retained-child handoff to the actual attached terminal."""
import argparse,json,re,struct
from pathlib import Path
from build_aspect_process import ROOT,sha
def read(path):return json.loads(path.read_text())
def current(sources):
    for name,digest in sources.items():assert sha(ROOT/name)==digest,name
def mouse_evidence(sub,case,parent,retained):
    """Decode the independent observer bytes rather than trusting PASS flags."""
    names=('seen before_mask before_off before_seg resume_mask resume_off resume_seg '
        'depth_before depth_after returned_ds scale_x scale_y count_before count_after '
        'menu_stage menu_count menu_code button_count button_code after_mask after_off '
        'after_seg state_bytes state_equal suspended_mask suspended_off suspended_seg').split()
    raw=(sub/'RENDER.BIN').read_bytes()
    at=len(raw)-26-32*70-case['compared_parent_bytes']*2-(30 if retained else 0)-4150
    fields=dict(zip(names,struct.unpack_from('<27H',raw,at)))
    assert fields==case['mouse_probe']
    header=struct.unpack_from('<7H',raw)
    symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',(parent.parent/'terminal.map').read_text(),re.M|re.I)}
    seg,off=symbols['mouse_callback']
    assert (fields['seen'],fields['resume_mask'],fields['resume_off'],fields['resume_seg'])==(1,11,off,header[5]+16+seg)
    assert fields['suspended_mask']==0
    assert fields['depth_before']==fields['depth_after']==65535 and fields['returned_ds']==64
    assert (fields['scale_x'],fields['scale_y'])==(8,4)
    assert fields['count_before']==fields['count_after']==0
    assert tuple(fields[n] for n in ['menu_stage','menu_count','menu_code','button_count','button_code'])==(2,2,2,1,4)
    assert tuple(fields['before_'+n] for n in ['mask','off','seg'])==tuple(fields['after_'+n] for n in ['mask','off','seg'])
    size=fields['state_bytes'];assert 0<size<=2048 and fields['state_equal']==1
    at+=54;assert raw[at:at+size]==raw[at+2048:at+2048+size]
    capture=(sub/'PCPLUS.SCR').read_bytes();assert capture and b'Command Menu' not in capture
    return dict(driver_bytes=size,state_restored=True,native_menu_stage=fields['menu_stage'],capture_sha256=sha(sub/'PCPLUS.SCR'))
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exit-label',action='append',required=True)
    parser.add_argument('--normal-label',action='append',required=True)
    parser.add_argument('--raw-label',required=True);parser.add_argument('--source-label',required=True)
    parser.add_argument('--mouse',action='store_true')
    args=parser.parse_args()
    for label in [*args.exit_label,*args.normal_label,args.raw_label,args.source_label]:assert re.fullmatch(r'[A-Za-z0-9_-]+',label)
    parent=ROOT/'build/terminal-process/TERMINAL.EXE';child=ROOT/'build/aspect-exit-parent/ASPECT.EXE'
    if args.mouse:parent=ROOT/'build/terminal-mouse-process/TERMINAL.EXE'
    manifest=read(child.parent/'manifest.json');current(manifest['sources'])
    assert manifest['exit_probe_attached'] and manifest['experimental_parent_render']
    symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',(child.parent/'ASPECT.map').read_text(),re.M|re.I)}
    code_seg,code_off=symbols['_aspect_exit_foreign'];data_seg,hits=symbols['_aspect_exit_hits']
    observed=[];seen=set();evidence={}
    for label in args.exit_label:
        folder=ROOT/('build/aspect-parent-exit-mouse' if args.mouse else 'build/aspect-parent-exit')/label;run=read(folder/'result.json')
        assert run['experimental_mouse']==args.mouse
        assert run['passed'] and run['exit_probe'] and run['experimental_break_owner']
        assert run['parent_sha256']==sha(parent) and run['child_sha256']==sha(child)
        assert run['checker_sha256']==sha(ROOT/'standalone/test_aspect_parent_process_dos.py')
        assert run['observer_sha256']==sha(folder/'RENDER.COM');current(run['source_hashes'])
        for name,digest in run['source_hashes'].items():assert sha(folder/'sources'/name)==digest,name
        for case in run['cases']:
            sub=folder/case['case'];config=case['configuration'];item=(config['port'],config['flow'])
            assert item not in seen;seen.add(item)
            assert case==read(sub/'result.json') and case['passed'] and all(case['checks'].values())
            assert sha(sub/'TERMINAL.EXE')==sha(parent) and sha(sub/'ASPECT.EXE')==sha(child)
            raw=(sub/'RENDER.BIN').read_bytes();at=len(raw)-26-32*70-case['compared_parent_bytes']*2
            header=struct.unpack_from('<7H',raw);words=struct.unpack_from('<15H',raw,at-30)
            assert list(words)==case['retained_words'] and header[:4]==(0x524e,1,1,1) and header[6]==10
            assert words[0]==0x31 and words[10]==0x030a
            assert words[1]==words[2]==words[4] and words[3]==words[5]>0
            assert words[6:8]==(code_off,words[1]+0x10+code_seg) and words[8:10]==(0,1)
            assert words[12]==words[1] and words[13:15]==(0x20,0xa55a)
            witness=struct.unpack('<13H',(sub/'EXITWIT.BIN').read_bytes())
            assert witness[:4]==(0x5845,ord('Q'),words[1],words[3])
            assert witness[4:8]==(words[11],0x20,*words[6:8])
            assert witness[8:12]==(hits,words[1]+0x10+data_seg,4,0) and witness[12]!=0
            assert case['resource_words'][7:11]==[0,1,1,0]
            assert raw[14:34]==raw[34:54] and raw[54:470]==raw[470:886]
            wire=(sub/'serial.bin').read_bytes();screen=(sub/'SCREEN.BIN').read_bytes()[::2]
            assert b'Synth42\r' not in wire and b'ready' in wire
            assert b'\x1b[2;1R' in wire[wire.find(b'ready')+5:]
            assert b'ASPECT returned an error.' in screen and b'ASPECT memory retained.' in screen
            assert b'AFTER CHILD' not in screen and b'FAIL' not in screen
            assert (sub/'CHILD.LOG').read_bytes()==b'G'
            observed.append(dict(label=label,port=item[0],flow=item[1],checks=len(case['checks']),
                child_status=words[10],child_PSP=words[1],retained_paragraphs=words[3],
                extra_segment=words[11],callback_hits=words[9],parent_lease=case['resource_words'][7]))
            if args.mouse:observed[-1]['mouse']=mouse_evidence(sub,case,parent,True)
            evidence[str(sub.relative_to(ROOT))]={n:sha(sub/n) for n in ['RENDER.BIN','EXITWIT.BIN','serial.bin','SCREEN.BIN','result.json']}
    assert seen=={(p,f) for p in [1,2] for f in 'NSHB'}
    normal=[];names=set()
    for label in args.normal_label:
        folder=ROOT/('build/aspect-parent-break-mouse' if args.mouse else 'build/aspect-parent-break')/label;run=read(folder/'result.json')
        assert run['experimental_mouse']==args.mouse
        assert run['passed'] and not run['exit_probe'] and run['parent_sha256']==sha(parent)
        assert run['checker_sha256']==sha(ROOT/'standalone/test_aspect_parent_process_dos.py');current(run['source_hashes'])
        assert run['observer_sha256']==sha(folder/'RENDER.COM')
        for name,digest in run['source_hashes'].items():assert sha(folder/'sources'/name)==digest,name
        assert run['child_sha256']==sha(ROOT/'build/aspect-process-break/ASPECT.EXE')
        for case in run['cases']:
            assert case['case'] not in names;names.add(case['case'])
            assert case['passed'] and all(case['checks'].values())
            sub=folder/case['case'];assert (sub/'BEFORE.BIN').read_bytes()==(sub/'AFTER.BIN').read_bytes()
            assert sha(sub/'TERMINAL.EXE')==sha(parent) and sha(sub/'ASPECT.EXE')==run['child_sha256']
            assert b'ASPECT memory retained.' not in (sub/'SCREEN.BIN').read_bytes()[::2]
            normal.append(dict(label=label,case=case['case'],checks=len(case['checks'])))
            if args.mouse:normal[-1]['mouse']=mouse_evidence(sub,case,parent,False)
            assert case==read(sub/'result.json')
            evidence[str(sub.relative_to(ROOT))]={n:sha(sub/n) for n in ['RENDER.BIN','serial.bin','SCREEN.BIN','result.json']}
    assert names=={'G','T','W','R','F'}|{f'full-{p}-{f}' for p in [1,2] for f in 'NSHB'}
    proof=read(ROOT/'build/exit-owner/source-proofs'/args.source_label/'result.json')
    assert proof['passed'] and proof['attached'] and len(proof['products'])==(33 if args.mouse else 31)
    if args.mouse:assert proof['mouse']
    assert proof['checker_sha256']==sha(ROOT/'standalone/check_exit_source.py');current(proof['sources'])
    for name,pair in proof['products'].items():assert pair['expected']==pair['actual']==sha(ROOT/'build'/name),name
    raw=read(ROOT/'build/aspect-exit-break/runs'/args.raw_label/'result.json')
    assert raw['passed'] and raw['actual_ASPECT_CLI'] and raw['cases'][0]['checks']==277
    assert raw['cases'][0]['status']==0x030a and raw['checker_sha256']==sha(ROOT/'standalone/test_exit_owner_dos.py');current(raw['sources'])
    base=read(ROOT/'docs/validation/enigma-upload-time.json')['source_products']
    stock={n:sha(ROOT/'build'/n) for n in ['terminal/TERMINAL.EXE','aspect-runner/ASPECT.EXE']}
    for name,digest in stock.items():assert base[name]==digest,name
    layout=read(parent.parent/'manifest.json')['memory_layout']
    stock_layout=read(ROOT/('build/terminal-mouse/manifest.json' if args.mouse else 'build/terminal/manifest.json'))['memory_layout']
    memory={name:layout[name] for name in ['near_bytes','near_spare_bytes','resident_code_bytes','resident_code_spare_bytes']}
    assert memory=={name:stock_layout[name] for name in memory}
    assert memory['near_bytes']<65536 and memory['resident_code_bytes']<65536
    result=dict(passed=True,experimental_mouse=args.mouse,whole_application_gates_closed=[],quarantine_routes=observed,
        quarantine_checks=sum(c['checks'] for c in observed),normal_routes=normal,
        normal_checks=sum(c['checks'] for c in normal),raw_memory_pressure=dict(label=args.raw_label,checks=277),
        source_proof=proof,stock_products_unchanged=stock,parent_memory=memory,evidence=evidence,
        checker_sha256=sha(Path(__file__)),parent_sha256=sha(parent),child_sha256=sha(child),
        limits=['Timer/BIOS-key mutation is controlled test stimulus; no physical keyboard/modem acceptance',
                'Observer invokes only the known retained source-owned ISR and does not repair vector/lease state',
                'Attached test validates MCBs/callback after return; memory-pressure allocation is a separate recovered-parent run',
                'Retained memory/remaining handles intentionally persist; automatic repair/unload is not implemented',
                'Normal dispatch publication, application-wide ownership and all full application gates remain open'])
    (ROOT/('docs/validation/parent-exit-mouse.json' if args.mouse else 'docs/validation/parent-exit.json')).write_text(json.dumps(result,indent=2)+'\n')
    print('Eight retained-child routes, thirteen normal routes, raw memory pressure and',len(proof['products']),'source products audited')
if __name__=='__main__':main()
