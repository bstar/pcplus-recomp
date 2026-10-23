#!/usr/bin/env python3
"""Audit actual combined Setup/ASPECT captures and freeze their source custody."""
import argparse,hashlib,json,re,shutil,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--label',required=True);p.add_argument('--regression',required=True)
    p.add_argument('--cohort',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert all(re.fullmatch(r'[A-Za-z0-9_-]+',x) for x in (a.label,a.regression))
    stage=ROOT/'build/mouse-sound-live'/a.label;r=read(stage/'result.json')
    regression=ROOT/'build/program-sound-smoke'/a.regression;old=read(regression/'result.json')
    assert r['passed'] and old['passed'] and old['mouse'] and len(old['cases'])==3
    for base,report in ((stage,r),(regression,old)):
        for n,h in report['sources'].items():assert sha(ROOT/n)==sha(base/'sources'/n)==h,n
        assert sha(base/'RENDER.COM')==report['observer_sha256']
        for case in report['cases']:assert case['passed'] and all(case['checks'].values())
    for n,h in r['products'].items():assert sha(ROOT/n)==h
    assert old['parent_sha256']==r['products']['build/terminal-mouse-notice-sound/TERMINAL.EXE']
    assert old['child_sha256']==r['products']['build/aspect-notice-sound-parent/ASPECT.EXE']
    plan=[('enable',0,1,(9,5)),('disable',1,0,(9,5)),('nonzero',0,65535,(999,1)),
        ('discard',1,1,(8,4)),('invalid',1,1,(8,4))]
    assert [x['case'] for x in r['cases']]==[x[0] for x in plan];cases=[]
    for name,initial,want,scales in plan:
        folder=stage/name;case=read(folder/'result.json')
        for n,h in case['artifacts'].items():assert sha(folder/n)==h,n
        before=(folder/'BEFORE.PRM').read_bytes();expected=bytearray(before)
        assert len(before)==1264 and struct.unpack_from('<H',before,0x1bc)==(initial,)
        assert struct.unpack_from('<HH',before,0x4e4)==(8,4)
        struct.pack_into('<H',expected,0x1bc,want);struct.pack_into('<HH',expected,0x4e4,*scales)
        assert (folder/'TEST.PRM').read_bytes()==(folder/'EXPECTED.PRM').read_bytes()==bytes(expected)
        assert (folder/'BEFORE.BIN').stat().st_size==42
        assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes()
        assert (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists()
        assert not (folder/'PRMEDIT.BAK').exists() and not (folder/'PRMEDIT.$$$').exists()
        assert (folder/'SUCCESS.OK').read_bytes()==b'OK' and not (folder/'ABSENT.COM').exists()
        for binary,product in [('TERMINAL.EXE','terminal-mouse-notice-sound'),('ASPECT.EXE','aspect-notice-sound-parent'),('PRMEDIT.EXE','setup-mouse-notice-sound')]:
            assert sha(folder/binary)==r['products'][f'build/{product}/{binary}']
        wire=(folder/'serial.bin').read_bytes()
        assert wire.startswith(b'ATZ\rATDCaseTest:23\r') and b'BAD' not in wire
        assert wire.count(b'AFTERSETUP')==1 and wire.count(b'ready')==1
        raw=(folder/'RENDER.BIN').read_bytes();audio=struct.unpack_from('<H',raw,len(raw)-2)[0];raw=raw[:-2]
        assert bool(audio)==bool(want) and audio==case['speaker_active_timer_samples']
        header=struct.unpack_from('<7H',raw);assert header[:4]==(0x524e,1,1,1) and header[6]==0
        # The observer's all-EXEC name array starts at offset4972 for this
        # declared renderer snapshot layout. Read every64-byte name slot.
        names=[raw[4972+i*64:4972+(i+1)*64].split(b'\0',1)[0] for i in range(4)]
        assert [x.rsplit(b'\\',1)[-1] for x in names]==[b'PRMEDIT.EXE',b'ASPECT.EXE',b'ABSENT.COM',b'SUCCESS.COM']
        size=case['compared_parent_bytes'];owners_at=len(raw)-26-32*70-size*2
        owners=struct.unpack_from('<13H',raw,owners_at)
        assert owners[0]==2 and owners[2]==0 and owners[7]==0 and owners[8]==owners[9]>=2
        assert raw[14:34]==raw[34:54] and raw[54:470]==raw[470:886]
        assert raw[-size*2:-size]==raw[-size:]
        # Existing mouse probe layout:27 words, two2048-byte state buffers.
        mouse_at=owners_at-(27*2+4096);m=struct.unpack_from('<27H',raw,mouse_at)
        assert m[0]==1 and m[4]==11 and m[9]==0x40 and m[10:12]==scales
        assert m[7:9]==(65535,65535) and m[12:14]==(0,0)
        assert m[14:19]==(2,2,2,1,4) and m[19:22]==m[1:4] and m[23]==1 and m[24]==0
        count=m[22];state=mouse_at+54;assert 0<count<=2048
        assert raw[state:state+count]==raw[state+2048:state+2048+count]
        assert (folder/'PCPLUS.SCR').stat().st_size>0
        assert b'Command Menu' not in (folder/'PCPLUS.SCR').read_bytes()
        cases.append(dict(name=name,initial_sound=initial,active_sound=want,active_mouse_scales=scales,
            speaker_active_timer_samples=audio,driver_state_bytes=count,EXEC_names=[x.decode() for x in names],
            result=str((folder/'result.json').relative_to(ROOT)),result_sha256=sha(folder/'result.json')))
    cohort=a.cohort.resolve();output=a.output.resolve()
    assert cohort.is_relative_to(ROOT/'build') and not cohort.exists()
    assert output.is_relative_to(ROOT/'docs/validation') and not output.exists()
    selected={Path(__file__).resolve()}
    for base in (stage,regression,ROOT/'build/mouse-sound-live/live-01'):
        selected.update(x for x in base.rglob('*') if x.is_file())
    cohort.mkdir();kept={}
    for source in sorted(selected):
        target=cohort/'accepted'/source.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target);assert sha(target)==sha(source);kept[str(target.relative_to(ROOT))]=sha(target)
    result=dict(passed=True,selected_combined_live_Setup_accepted=True,full_PROGRAM_policy_accepted=False,
        full_application_accepted=False,cases=cases,products=r['products'],regression_actual_DOS_sessions=3,
        regression_result=str((regression/'result.json').relative_to(ROOT)),custody_sha256=kept,
        prerequisite_failure='build/mouse-sound-live/live-01/result.json',
        scope='Five actual8086 DOS AltF10 combined51-field editor workflows followed by ordinary ASPECT, missing-target PROGRAM notice, successful DOS child and serial input. Save on/off/nonzero plus simultaneous mouse scale changes; discard and invalid65536 retain the entire prior PRM and active settings. Exact UART/PIC/vector restoration and parent resource comparisons. Passive speaker-gate sampling; separate active INT33 callback/menu probe and576-byte driver restoration. Three ordinary startup regressions pass. Initial probe assumed fixed movement8 and selected the wrong menu item after Y-scale changes; preserved as failed, corrected probe uses twice the observed Y scale. Muted mixer, modeled Hayes peer. No physical/audio acceptance, mouse input inside ASPECT notices, broader views or full application acceptance.')
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,actual_DOS_sessions=8,custody_files=len(kept))))


if __name__=='__main__':main()
