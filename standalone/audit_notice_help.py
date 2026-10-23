#!/usr/bin/env python3
"""Decode actual help captures and preserve the selected integration cohort."""
import argparse,hashlib,json,re,shutil,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def words(data,count,offset=0):return struct.unpack_from('<'+str(count)+'H',data,offset)
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['selection','cohort','output']:ap.add_argument('--'+name,required=True)
    a=ap.parse_args();selection=json.loads((ROOT/a.selection).read_text());cohort=ROOT/a.cohort;cohort.mkdir(parents=True,exist_ok=False)
    custody={};sources={};coverage=set();accepted=[]
    def preserve(path):
        target=cohort/'accepted'/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
        assert sha(target)==sha(path);custody[str(target.relative_to(ROOT))]=sha(target)
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
    for name in selection['ordinary']:
        run=ROOT/name;d=json.loads((run/'result.json').read_text());assert d['passed'] and all(d['checks'].values());source_check(d)
        folder=run/'ordinary';raw=(folder/'RENDER.BIN').read_bytes();h=words(raw,7,len(raw)-12014);frames=raw[-12000:]
        assert h==(4,0,1,1,90,1,1)
        assert b'PCPlus // CONTEXT HELP' in frames[4000:8000:2]
        assert b'EXTERNAL PROGRAM / ERROR NOTICE' in frames[4000:8000:2]
        assert b'SERIAL SESSION / LOCAL INPUT' in frames[8000:12000:2]
        absent=d['no_driver'];count=14 if absent else 19;end=len(raw)-12014;c=words(raw,count,end-count*2)
        base=raw[:end-count*2];size=int(re.search(r'resource_before: times (\d+) db 0',(run/'observer.asm').read_text())[1])
        head,m=parent_capture(base,folder,size,not absent);assert head[6]==0
        assert c[6]==(16 if d['bios']=='ENHANCED' else 0)
        if absent:
            assert c[9:13]==(1,1,13,0) and c[13]==1
            assert c[:2]==c[2:4] and bool(c[0] or c[1])
        else:
            assert c[12:16]==(1,1,13,0) and c[16:19]==m[24:27]
        wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes()[::2]
        assert b'Q'*500+b'ENDMARK!' in screen and b'AFTER HELP' in screen
        assert b'BAD' not in wire and wire.count(b'Synth42\r')==1 and b'ready' in wire
        assert (folder/'SUCCESS.OK').read_bytes()==b'OK'
        assert sha(folder/'TERMINAL.EXE')==d['parent_sha256']==sha(ROOT/'build/terminal-mouse-notice-input/TERMINAL.EXE')
        assert sha(folder/'ASPECT.EXE')==d['child_sha256']==sha(ROOT/'build/aspect-notice-help-parent/ASPECT.EXE')
        coverage.add((absent,d['bios'],d['port']));accepted.append(dict(kind='ordinary',path=name))
    assert coverage=={(False,'STANDARD',1),(False,'ENHANCED',2),(True,'STANDARD',2),(True,'ENHANCED',1)}
    fault=ROOT/selection['faults'];d=json.loads((fault/'result.json').read_text());assert d['passed'] and len(d['cases'])==3;source_check(d)
    for mode in ['2D','2A','2F']:
        folder=fault/mode;r=json.loads((folder/'result.json').read_text());assert r['passed'] and all(r['checks'].values())
        raw=(folder/'RENDER.BIN').read_bytes();h=words(raw,7,len(raw)-12014);assert h[:5]==(5,0,1,0,90)
        assert b'PCPlus // CONTEXT HELP' in raw[-8000:-4000:2]
        c=words(raw,19,len(raw)-12014-38);base=raw[:-12014-38];head,m=parent_capture(base,folder,r['compared_parent_bytes'],True)
        assert c[16:19]==m[24:27] and head[6]==(5 if mode=='2A' else 12)
        w=words((folder/'NOTICE.BIN').read_bytes(),72)
        assert w[0]==0x4e46 and w[3]==1 and w[4]==head[6] and w[9:11]==(1,1) and w[12]==508
        assert w[14:16]==(1,65535) and w[17]==w[27]==1 and w[59]==w[60] and w[64:69]==(0,0,0,0,0)
        assert (folder/'WRITE.BIN').read_bytes()==b'FIRSTSECOND' and (folder/'SUCCESS.OK').read_bytes()==b'OK'
        assert sha(folder/'ASPECT.EXE')==d['child_sha256']==sha(ROOT/'build/aspect-notice-help-fault/ASPECT.EXE')
        assert b'Q'*500+b'ENDMARK!' in (folder/'SCREEN.BIN').read_bytes()[::2]
        accepted.append(dict(kind='outer_fault',path=str(folder.relative_to(ROOT))))
    for name in selection['input_regressions']:
        run=ROOT/name;d=json.loads((run/'result.json').read_text());assert d['passed'] and d['notice_help'] and len(d['cases'])==3;source_check(d)
        for case in d['cases']:
            assert case['passed'] and all(case['checks'].values())
            folder=run/case['case'];raw=(folder/'RENDER.BIN').read_bytes();absent=d['no_driver'];count=14 if absent else 19
            c=words(raw,count,len(raw)-count*2);base=raw[:-count*2]
            assert bool(words(base,1,len(base)-2)[0])==bool(case['sound'])
            head,m=parent_capture(base[:-2],folder,case['compared_parent_bytes'],not absent);assert head[6]==0
            if absent:assert c[9:14]==(1,1,13,0,1) and c[:2]==c[2:4]
            else:
                expected=(2,2,27,0) if case['sound']==1 else (1,1,13,0)
                assert c[12:16]==expected and c[16:19]==m[24:27]
            assert sha(folder/'ASPECT.EXE')==d['child_sha256']
        accepted.append(dict(kind='input_regression',path=name))
    component=ROOT/selection['component'];d=json.loads((component/'result.json').read_text());assert d['passed'] and d['self_checks']==36;source_check(d)
    assert (component/'OUTPUT.TXT').read_bytes()==b'HELPVIEW checks=36 failures=0\r\n'
    for name in selection['proofs']:
        run=ROOT/name;d=json.loads((run/'result.json').read_text());assert d['passed'] and not d['original_inputs'] and len(d['products'])==4;source_check(d)
        assert d['checker_sha256']==sha(ROOT/'standalone/prove_program_notices_sound_source.py')
        for n,h in d['products'].items():assert sha(ROOT/n)==h,n
    # Bind the current unchanged products to the preceding accepted receipts.
    for name in ['docs/validation/program-notice-input.json','build/program-notices-sound/native-input-final-baseline-01/result.json']:
        d=json.loads((ROOT/name).read_text())
        for n,h in d['products'].items():
            path=ROOT/n if n.startswith('build/') else ROOT/'build'/n/('TERMINAL.EXE' if n.startswith('terminal') else 'ASPECT.EXE')
            assert sha(path)==h,n
    bbs=ROOT/selection['bbs'];b=json.loads(bbs.read_text());assert b['passed'] and b['notice_help']
    for n,h in b['custody_sha256'].items():assert sha(ROOT/n)==h;custody[n]=h
    paths=[*selection['ordinary'],selection['faults'],*selection['input_regressions'],selection['component'],*selection['proofs']]
    for name in paths:
        for path in sorted((ROOT/name).rglob('*')):
            if path.is_file():preserve(path)
    for n,h in sources.items():
        path=ROOT/n;assert sha(path)==h
        target=cohort/'source'/n;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target);custody[str(target.relative_to(ROOT))]=h
    for path in [Path(__file__),ROOT/a.selection,bbs,ROOT/'standalone/prove_program_notices_sound_source.py',ROOT/'tools/dev',ROOT/'tools/bbs-dev',ROOT/'nix/flake.nix',ROOT/'nix/flake.lock']:preserve(path)
    result=dict(passed=True,selected_PROGRAM_context_help_accepted=True,full_contextual_help_accepted=False,full_application_accepted=False,
        ordinary_sessions=4,outer_fault_sessions=3,input_regression_sessions=6,component_checks=36,BBS_sessions=4,
        accepted=accepted,selection=selection,custody_sha256=custody,
        failed_earlier_attempts=['ordinary-01:20s observation timeout','ordinary-02:raw captures expose native3second countdown expiring despite service deadline pause; fixed both clocks','absent-01:oversized observer COM; fixed compact collector and enforced COM bound','absent-02:help passed, post-help command menu needed explicit Escape without mouse driver'],
        scope='Maintained child-owned two-topic PROGRAM help view. Owned BIOS key/event/vector probes; exact screen/cursor and driver/resource/UART snapshots; selected outer DIV/typed-abort/foreign-DS recovery; native/no-driver input; source-only647/641/632-file four-product rebuilds and selected current ENiGMA/Synchronet workflows. Original helper UI/content/search, all application contexts, combined helper/window/speaker corruption, arbitrary faults, real DOS kernels, physical modem/mouse/audio and full application acceptance remain open.')
    out=ROOT/a.output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(custody),'preserved files')
if __name__=='__main__':main()
