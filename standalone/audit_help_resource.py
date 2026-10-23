#!/usr/bin/env python3
"""Independently decode the resource-help DOS captures and freeze their evidence."""
import argparse, hashlib, json, re, shutil, struct
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def words(data, count, offset=0): return struct.unpack_from('<'+str(count)+'H', data, offset)
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('selection','cohort','output'): ap.add_argument('--'+name,required=True)
    a=ap.parse_args(); selection=json.loads((ROOT/a.selection).read_text())
    cohort=ROOT/a.cohort; cohort.mkdir(parents=True,exist_ok=False)
    custody={}; sources={}; accepted=[]; coverage=set()
    def preserve(path):
        target=cohort/'accepted'/path.relative_to(ROOT)
        target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(path,target)
        assert sha(target)==sha(path); custody[str(target.relative_to(ROOT))]=sha(target)
    def source_check(d):
        for n,h in d.get('sources',{}).items():
            assert n not in sources or sources[n]==h,n
            assert sha(ROOT/n)==h,n
            sources[n]=h
    def parent_capture(raw,folder,resource_size,mouse):
        head=words(raw,7);assert head[:4]==(0x524e,1,1,1)
        assert raw[14:34]==raw[34:54] and raw[54:470]==raw[470:886]
        at=len(raw)-26-2240-resource_size*2;o=words(raw,13,at)
        assert o[2]==o[7]==0 and o[8]==o[9] and o[8]>=2
        assert raw[-resource_size*2:-resource_size]==raw[-resource_size:]
        assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
        if mouse:
            start=at-4150;m=words(raw,27,start);n=m[22]
            assert m[0]==m[23]==1 and m[4]==11 and m[7]==m[8]==65535
            assert (m[19],m[20],m[21])==(m[1],m[2],m[3])
            assert 0<n<=2048 and raw[start+54:start+54+n]==raw[start+54+2048:start+54+2048+n]
            return head,m
        return head,None
    resource=ROOT/'build/aspect-help-resource-parent/LOCHELP.HLP'
    payload=resource.read_bytes(); assert len(payload)==9111 and words(payload,1,1)==(131,) and payload[0]==26
    for name in selection['ordinary']:
        run=ROOT/name; d=json.loads((run/'result.json').read_text())
        assert d['passed'] and all(d['checks'].values()) and d['help_resource']; source_check(d)
        folder=run/'ordinary'; raw=(folder/'RENDER.BIN').read_bytes(); case=d['resource_case']
        if case=='normal':
            assert words(raw,5,len(raw)-8010)==(1,1,1,1,1)
            frames=raw[-8000:]; assert b'Receive files' in frames[:4000:2] and b'XMODEM' in frames[:4000:2]
            assert b'Send files' in frames[4000::2]
            raw=raw[:-8010]; assert (folder/'LOCHELP.HLP').read_bytes()==payload
        elif case=='bad': assert (folder/'LOCHELP.HLP').read_bytes()==b'bad'
        else: assert case=='missing' and not (folder/'LOCHELP.HLP').exists()
        h=words(raw,7,len(raw)-12014); frames=raw[-12000:]
        assert h==(4,0,1,int(case!='bad'),90,1,1)
        if case=='bad': assert b'HELP RESOURCE ERROR' in frames[4000:8000:2]
        else:
            assert b'EXTERNAL PROGRAM / ERROR NOTICE' in frames[4000:8000:2]
            assert b'SERIAL SESSION / LOCAL INPUT' in frames[8000::2]
        absent=d['no_driver']; count=14 if absent else 19; end=len(raw)-12014
        c=words(raw,count,end-count*2); base=raw[:end-count*2]
        size=int(re.search(r'resource_before: times (\d+) db 0',(run/'observer.asm').read_text())[1])
        head,m=parent_capture(base,folder,size,not absent); assert head[6]==0
        assert c[6]==(16 if d['bios']=='ENHANCED' else 0)
        if absent:
            assert c[9:14]==(1,1,13,0,1) and c[:2]==c[2:4] and bool(c[0] or c[1])
        else: assert c[12:16]==(1,1,13,0) and c[16:19]==m[24:27]
        wire=(folder/'serial.bin').read_bytes(); screen=(folder/'SCREEN.BIN').read_bytes()[::2]
        assert b'Q'*500+b'ENDMARK!' in screen and b'AFTER HELP' in screen
        assert b'BAD' not in wire and wire.count(b'Synth42\r')==1 and b'ready' in wire
        assert (folder/'SUCCESS.OK').read_bytes()==b'OK'
        assert sha(folder/'TERMINAL.EXE')==d['parent_sha256']==sha(ROOT/'build/terminal-mouse-notice-input/TERMINAL.EXE')
        assert sha(folder/'ASPECT.EXE')==d['child_sha256']==sha(ROOT/'build/aspect-help-resource-parent/ASPECT.EXE')
        coverage.add((case,absent,d['bios'],d['port'])); accepted.append(dict(kind='ordinary',path=name))
    assert coverage=={('normal',False,'STANDARD',1),('normal',False,'ENHANCED',2),('normal',True,'STANDARD',2),('normal',True,'ENHANCED',1),('bad',False,'ENHANCED',1),('missing',False,'ENHANCED',2)}
    combined_modes=set()
    for name in selection.get('combined_faults',[]):
        run=ROOT/name;d=json.loads((run/'result.json').read_text());assert d['passed'] and len(d['cases'])==3;source_check(d)
        kind={'guard':1,'foreign':2,'speaker':3,'help-guard':4,'help-speaker':5,'help-foreign':6}[d['quarantine']]
        phase={1:0,2:2,3:0,4:3,5:3,6:2}[kind]
        window_phase={1:2,2:1,3:0,4:1,5:1,6:1}[kind]
        allocations=2 if kind in (2,6) else 1
        for mode in ['2D','2A','2F']:
            folder=run/mode;r=json.loads((folder/'result.json').read_text());assert r['passed'] and all(r['checks'].values())
            raw=(folder/'RENDER.BIN').read_bytes();h=words(raw,7,len(raw)-12014);assert h[:5]==(5,0,1,0,90)
            assert b'PCPlus // CONTEXT HELP' in raw[-8000:-4000:2]
            c=words(raw,19,len(raw)-12014-38);head,m=parent_capture(raw[:-12014-38],folder,r['compared_parent_bytes'],True)
            assert c[16:19]==m[24:27] and head[6]==(5 if mode=='2A' else 12)
            w=words((folder/'NOTICE.BIN').read_bytes(),72)
            assert w[0]==0x4e46 and w[3]==1 and w[4]==head[6] and w[9]==0 and w[10]==int(kind==3) and w[12]==508
            assert w[14:16]==(1,65535) and w[17]==w[27]==1
            assert w[32:35]==(phase,phase,0)
            assert w[37:44]==(kind,1,1,6,1,1,window_phase)
            assert w[44]==w[58]==9 and w[45:50]==(10,1,1,10,10)
            assert w[50:56]==(0,0,1,1,1,0) and w[56:58]==(allocations,allocations)
            assert w[59]==w[60]==allocations+1 and w[61]==0
            assert w[65:69]==((1,3,0,0) if kind in (3,5) else (0,0,0,0))
            assert (folder/'WRITE.BIN').read_bytes()==b'FIRSTSECOND' and (folder/'SUCCESS.OK').read_bytes()==b'OK'
            screen=(folder/'SCREEN.BIN').read_bytes()[::2];wire=(folder/'serial.bin').read_bytes()
            assert b'Q'*500+b'ENDMARK!' in screen and b'RECOVERY OK' in screen and b'BAD' not in wire and b'ready' in wire
            assert sha(folder/'ASPECT.EXE')==d['child_sha256']==sha(ROOT/'build/aspect-help-resource-fault/ASPECT.EXE')
            combined_modes.add((kind,mode));accepted.append(dict(kind='combined_fault',path=str(folder.relative_to(ROOT))))
    if selection.get('combined_faults'):assert combined_modes=={(kind,mode) for kind in range(1,7) for mode in ['2D','2A','2F']}
    for name,checks,prefix in [('build/help-document/DOS-final-01',168,'HELPDOC'),('build/help-resource/DOS-final-01',49,'HELPRESOURCE'),('build/help-format/resource-regression-01',52,'HELPFMT'),('build/help-format/resource-compat-01',52,'HELPFMT')]:
        folder=ROOT/name; d=json.loads((folder/'result.json').read_text()); source_check(d)
        assert d['passed'] and all(d['checks'].values()) and d['self_checks']==checks
        assert (prefix+' checks='+str(checks)+' failures=0').encode() in (folder/'OUTPUT.TXT').read_bytes()
        if prefix=='HELPDOC':
            assert (folder/'HOST.TXT').read_bytes().replace(b'\r\n',b'\n')==(folder/'OUTPUT.TXT').read_bytes().replace(b'\r\n',b'\n')
            assert (folder/'host/DOCUMENT.HLP').read_bytes()==(folder/'DOCUMENT.HLP').read_bytes()
        if name.endswith('compat-01'): assert (folder/'COMPAT.TXT').read_bytes()==b'HELP INDEX topics=47 lines=463 bytes=23558\r\n'
    for name in selection['proofs']:
        d=json.loads((ROOT/name/'result.json').read_text()); source_check(d)
        assert d['passed'] and d['original_inputs']==[]
        assert len(d['products'])==(6 if d.get('help_resource') else 4)
        assert d['checker_sha256']==sha(ROOT/'standalone/prove_program_notices_sound_source.py')
        for n,h in d['products'].items(): assert sha(ROOT/n)==h,n
    for name in ['build/notice-help/combined-source-final-01/result.json','build/notice-help/combined-input-baseline-source-01/result.json','build/program-notices-sound/native-input-final-baseline-01/result.json']:
        d=json.loads((ROOT/name).read_text())
        for n,h in d['products'].items(): assert sha(ROOT/n)==h,n
    bbs=ROOT/'docs/validation/bbs-help-resource.json'; b=json.loads(bbs.read_text())
    assert b['passed'] and b['help_resource']
    for n,h in b['custody_sha256'].items(): assert sha(ROOT/n)==h; custody[n]=h
    paths=selection['ordinary']+selection['combined_faults']+selection['proofs']+selection['components']
    for name in paths:
        for path in sorted((ROOT/name).rglob('*')):
            if path.is_file(): preserve(path)
    for n,h in sources.items():
        target=cohort/'source'/n; target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/n,target); custody[str(target.relative_to(ROOT))]=h
    for path in [Path(__file__),ROOT/a.selection,bbs,ROOT/'Makefile',ROOT/'tools/dev',ROOT/'tools/bbs-dev',ROOT/'nix/flake.nix',ROOT/'nix/flake.lock']: preserve(path)
    result=dict(passed=True,selected_PROGRAM_resource_help_accepted=True,full_contextual_help_accepted=False,full_application_accepted=False,
        ordinary_sessions=6,combined_fault_sessions=len(combined_modes),document_checks=168,resource_view_checks=49,format_checks=52,BBS_sessions=4,
        resource_sha256=sha(resource),topics=26,lines=131,bytes=9111,accepted=accepted,selection=selection,custody_sha256=custody,
        scope='Optional PROGRAM notice help with current-directory LOCHELP.HLP, incremental reader and literal ASCII-folded title/body search. Exact video/cursor, driver, DOS/UART resources, serial continuation and next EXEC verified in selected emulator cases. BBS sessions exercise coexistence, not help interactions. Missing/damaged resources covered. Baseline products unchanged. Full context mapping, original PCHELP ABI/UI parity, arbitrary OS failure/corruption, real DOS kernels and physical modem/mouse/audio acceptance remain open.')
    out=ROOT/a.output; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS',len(custody),'preserved files')
if __name__=='__main__': main()
