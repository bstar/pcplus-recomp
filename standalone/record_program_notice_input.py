#!/usr/bin/env python3
"""Audit native-input captures, matching products and source/exit/BBS receipts."""
import argparse,hashlib,json,re,shutil,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def symbols(p):return {n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)\s*$',p.read_text(),re.M|re.I)}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--selection',type=Path,required=True);p.add_argument('--cohort',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    selection=a.selection.resolve();assert selection.is_relative_to(ROOT/'build')
    chosen=read(selection);selected={selection,Path(__file__).resolve()};receipts={};summaries={}
    for key,name in chosen.items():
        path=(ROOT/name).resolve();assert path.is_relative_to(ROOT)
        r=read(path);assert r['passed'],key;receipts[key]=(path,r)
        if key=='bbs':selected.add(path)
        else:selected.update(x for x in path.parent.rglob('*') if x.is_file())
        for n,h in r.get('sources',{}).items():
            assert sha(ROOT/n)==h,(key,n);selected.add(ROOT/n)
            frozen=path.parent/'sources'/n
            if frozen.exists():assert sha(frozen)==h
        summaries[key]=dict(result=name,sha256=sha(path))
    checkers={'source':'standalone/prove_program_notices_sound_source.py','baseline':'standalone/prove_program_notices_sound_source.py',
        'exit':'standalone/test_notice_input_exit_dos.py','exit_source':'standalone/prove_notice_input_exit_source.py',
        'fallback':'standalone/test_notice_input_dos.py','fallback_source':'standalone/prove_notice_input_source.py',
        'legacy_exit':'standalone/test_exit_owner_dos.py'}
    for key,name in checkers.items():assert receipts[key][1]['checker_sha256']==sha(ROOT/name);selected.add(ROOT/name)
    products={name:sha(ROOT/'build'/name/binary) for name,binary in [('terminal-mouse-notice-input','TERMINAL.EXE'),('aspect-notice-input-parent','ASPECT.EXE'),('aspect-notice-input-fault','ASPECT.EXE')]}
    for name in products:
        base=ROOT/'build'/name;m=read(base/'manifest.json');assert m.get('original_inputs',[])==[]
        assert all(sha(ROOT/n)==h for n,h in m['sources'].items())
        assert m['binary_sha256']==products[name]
        selected.update([base/'manifest.json',base/('TERMINAL.EXE' if name.startswith('terminal') else 'ASPECT.EXE'),base/('terminal.map' if name.startswith('terminal') else 'ASPECT.map')])
    parent=symbols(ROOT/'build/terminal-mouse-notice-input/terminal.map')
    child=symbols(ROOT/'build/aspect-notice-input-parent/ASPECT.map')
    fault=symbols(ROOT/'build/aspect-notice-input-fault/ASPECT.map')
    size=sum([2,496,2,2,256,44,2,948,30,4096,4096,128,50,2])+2*len(re.findall(r'X\((\w+)\)',(ROOT/'src/aspect/renderer_policy.h').read_text()))
    def parent_frame(raw,case,folder,driver,scales,child_product):
        assert case['compared_parent_bytes']==size
        assert sha(folder/'TERMINAL.EXE')==case['binary_sha256']==products['terminal-mouse-notice-input']
        assert sha(folder/'ASPECT.EXE')==products[child_product]
        head=struct.unpack_from('<7H',raw);assert head[:4]==(0x524e,1,1,1)
        at=len(raw)-26-32*70-size*2;owner=struct.unpack_from('<13H',raw,at)
        assert owner[2]==owner[7]==0 and owner[8]==owner[9]>=2
        assert raw[14:34]==raw[34:54] and raw[54:470]==raw[470:886] and raw[-size*2:-size]==raw[-size:]
        assert (folder/'BEFORE.BIN').stat().st_size==42 and (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
        assert (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists()
        assert (folder/'SUCCESS.OK').read_bytes()==b'OK'
        wire=(folder/'serial.bin').read_bytes();assert b'BAD' not in wire and b'ready' in wire and wire.count(b'Synth42\r')==1
        if not driver:return head,None
        start=at-(54+4096);m=struct.unpack_from('<27H',raw,start)
        seg,off=parent['mouse_callback'];assert m[0]==1 and m[4:7]==(11,off,head[5]+0x10+seg)
        assert m[7:10]==(65535,65535,0x40) and m[10:12]==scales and m[12:14]==(0,0)
        assert m[14:19]==(2,2,2,1,4) and m[19:22]==m[1:4] and m[23]==1 and m[24]==0
        count=m[22];assert 0<count<=2048 and raw[start+54:start+54+count]==raw[start+54+2048:start+54+2048+count]
        assert (folder/'PCPLUS.SCR').stat().st_size>0 and b'Command Menu' not in (folder/'PCPLUS.SCR').read_bytes()
        return head,m
    ordinary=[];faults=[]
    for key,absence in [('ordinary',False),('bios',True)]:
        path,r=receipts[key];assert r['native_notice_input'] and r['no_driver']==absence and r['passed'] and len(r['cases'])==3
        assert r['parent_sha256']==products['terminal-mouse-notice-input'] and r['child_sha256']==products['aspect-notice-input-parent']
        for case,(sound,bios,scales) in zip(r['cases'],[(0,0,(8,4)),(1,16,(9,5)),(65535,16,(999,1))]):
            assert case['passed'] and all(case['checks'].values());folder=path.parent/case['case']
            assert sha(folder/'RENDER.COM')==case['observer_sha256']==r['observer_variants'][case['case']]
            raw=(folder/'RENDER.BIN').read_bytes();n=14 if absence else 19;c=struct.unpack_from('<'+str(n)+'H',raw,len(raw)-n*2);raw=raw[:-n*2]
            audio=struct.unpack_from('<H',raw,len(raw)-2)[0];raw=raw[:-2]
            assert bool(audio)==bool(sound) and audio==case['speaker_active_timer_samples']
            cfg=(folder/'TEST.PRM').read_bytes();assert struct.unpack_from('<H',cfg,0x1bc)==(sound,) and struct.unpack_from('<HH',cfg,0x4e4)==scales
            head,m=parent_frame(raw,case,folder,not absence,scales,'aspect-notice-input-parent');assert head[6]==0
            if absence:
                assert c[:2]==c[2:4] and (c[0] or c[1]) and c[4]==c[8]==c[13]==1 and c[6:8]==(bios,0) and c[9:13]==(1,1,13,0)
            else:
                event=8 if sound==1 else 2;cause=2 if event==8 else 1;value=27 if event==8 else 13
                assert c[0]==c[11]==1 and c[1:3]==(child['mouse_callback'][1],c[3]+0x10+child['mouse_callback'][0])
                assert c[4:11]==(*scales,bios,event,0x40,1,5 if event==8 else 4)
                assert c[12:16]==(cause,cause,value,0) and c[16:19]==m[24:27]
            ordinary.append(dict(group=key,case=case['case'],BIOS_mode=bios,configured_scales=scales,sound=sound,notice_key=13 if absence or sound!=1 else 27))
    for key,count in [('fault',5),('guard',3),('foreign',3),('speaker',3)]:
        path,r=receipts[key];assert r['native_notice_input'] and len(r['cases'])==count and r['parent_sha256']==products['terminal-mouse-notice-input'] and r['child_sha256']==products['aspect-notice-input-fault']
        for case in r['cases']:
            assert case['passed'] and all(case['checks'].values());folder=path.parent/case['case'];raw=(folder/'RENDER.BIN').read_bytes();c=struct.unpack_from('<19H',raw,len(raw)-38);raw=raw[:-38]
            head,m=parent_frame(raw,case,folder,True,(8,4),'aspect-notice-input-fault');assert head[6]==(5 if case['case'][1]=='A' else 12)
            assert c[0]==c[11]==1 and c[7]==0 and c[4:6]==(8,4) and c[16:19]==m[24:27]
            assert c[1:3]==(fault['mouse_callback'][1],c[3]+0x10+fault['mouse_callback'][0])
            w=struct.unpack('<72H',(folder/'NOTICE.BIN').read_bytes());assert list(w)==case['notice_words'] and w[59]==w[60]
            assert w[12]==(0 if case['case']=='1D' else 508) and w[18:20]==(0,2) and w[24:26]==(1,0)
            assert (folder/'WRITE.BIN').read_bytes()==b'FIRSTSECOND' and b'Q'*500+b'ENDMARK!' in (folder/'SCREEN.BIN').read_bytes()[::2]
            faults.append(dict(group=key,case=case['case'],before_DOS_exit_registration=list(c[16:19])))
    for key in ['source','baseline','exit_source','fallback_source']:
        _,r=receipts[key];assert r['original_inputs']==[]
        for n,h in r['products'].items():assert sha(ROOT/n)==h;selected.add(ROOT/n)
    assert receipts['source'][1]['products']['build/aspect-notice-input-parent/ASPECT.EXE']==products['aspect-notice-input-parent']
    reference=read(ROOT/'build/program-notices-sound/mouse-source-01/result.json');assert receipts['baseline'][1]['products']==reference['products']
    _,r=receipts['exit'];assert [c['mode'] for c in r['cases']]==['C','H','A'] and [c['status'] for c in r['cases']]==[77,778,778] and all(c['passed'] for c in r['cases'])
    assert r['products']['ASPECT.EXE']==products['aspect-notice-input-parent']
    for case in r['cases']:
        folder=receipts['exit'][0].parent/case['mode']
        for n,h in case['artifacts'].items():assert sha(folder/n)==h
    assert receipts['fallback'][1]['self_checks']==78 and receipts['fallback'][1]['driver_bytes']==576
    assert len(receipts['legacy_exit'][1]['cases'])==12
    bbs=receipts['bbs'][1];assert bbs['native_notice_input'] and bbs['selected_modern_BBS_recorder_workflows_accepted']
    for server in bbs['servers'].values():assert server['binary_sha256']==products['terminal-mouse-notice-input'] and server['runner_sha256']==products['aspect-notice-input-parent']
    for n,h in bbs['custody_sha256'].items():assert sha(ROOT/n)==h
    cohort=a.cohort.resolve();output=a.output.resolve();assert cohort.is_relative_to(ROOT/'build') and not cohort.exists();assert output.is_relative_to(ROOT/'docs/validation') and not output.exists();cohort.mkdir()
    # Preserve the failed initial retention fixture separately from acceptance.
    failed=ROOT/'build/notice-input-exit/dos-01';selected.update(x for x in failed.rglob('*') if x.is_file())
    custody={}
    for path in sorted(selected):
        target=cohort/'accepted'/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target);assert sha(target)==sha(path);custody[str(target.relative_to(ROOT))]=sha(target)
    result=dict(passed=True,selected_attached_native_notice_input_accepted=True,selected_retained_input_exit_accepted=True,full_native_notice_input_policy_accepted=False,full_PROGRAM_policy_accepted=False,full_application_accepted=False,
        capability=16,ordinary_sessions=6,fault_sessions=14,BBS_sessions=4,exit_sessions=3,component_checks=78,legacy_exit_sessions=12,ordinary=ordinary,faults=faults,products=products,evidence=summaries,custody_sha256=custody,
        failed_fixture='build/notice-input-exit/dos-01: timeout before witness. Corrected fixture removed manual CRT near-heap truncation and disabled code-bank packing; no single isolated root-cause claim. Not counted as acceptance.',
        scope='Ordinary native mouse Enter/Escape and no-driver BIOS input, configured scales/BIOS/sound, selected outer DIV/abort and window/speaker quarantine/retry with508 queued text bytes, child callback retirement before DOS exit, real retained native-input DOS31 and callback execution after largest-free-block pressure, fresh source-only builds and selected ENiGMA/Synchronet recording/compile/replay. Driver event/vector injection and known snapshot restoration are owned test actions. DOSBox-X8086, modeled Hayes peers and loopback BBSes; no physical clicks/modem/audio, complete contextual Alt-Z UI, broader native event/KEY macro routing, arbitrary faults or full application acceptance.')
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,ordinary=6,fault=14,exit=3,BBS=4,custody_files=len(custody))))
if __name__=='__main__':main()
