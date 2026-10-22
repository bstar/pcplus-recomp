#!/usr/bin/env python3
"""Independent pre-CONNECT cancel audit, with explicit patched-backend scope."""
import argparse,json,runpy,shutil,struct,subprocess
from pathlib import Path
from audit_aspect_transmit_wait import ROOT,sha,read,ESC
from directory_test_support import accounting_check


def verify(folder,gap):
    r=read(folder/'checks.json');assert r['passed'] and r['gap_reproduced']==gap and r['compatibility_accepted']!=gap
    assert len(r['cases'])==2 and {c['case'] for c in r['cases']}=={'soft','both'}
    for name,digest in r['inputs'].items():assert sha(folder/'inputs'/name)==digest,name
    assert sha(folder/'admitted.EXE')==r['parent_sha256']
    backend=r['emulator'];assert backend['test_backend'] and '-dosbox-x-pcplus-dcd-lab-2026.07.02/' in backend['wrapper']
    wrapper=Path(backend['wrapper']);assert sha(wrapper)==backend['wrapper_sha256'] and sha(wrapper.with_name('.dosbox-x-wrapped'))==backend['binary_sha256']
    assert sha(folder/'inputs/nix/patches/dosbox-dcd-control.patch')==backend['patch_sha256']
    proof=read(folder/'inputs/build/dosbox-dcd-lab-build.json');assert len(proof)==1 and proof[0]['outputs']['out']==str(wrapper.parent.parent)
    assert 'pcplus-dcd-lab-2026.07.02.drv' in proof[0]['drvPath']
    outputs=subprocess.check_output(['nix-store','--query','--outputs',proof[0]['drvPath']],text=True).split()
    assert outputs==[str(wrapper.parent.parent)]
    patches=subprocess.check_output(['nix-store','--query','--binding','patches',proof[0]['drvPath']],text=True).split()
    assert len(patches)==1 and sha(Path(patches[0]))==backend['patch_sha256']
    patch=(folder/'inputs/nix/patches/dosbox-dcd-control.patch').read_text();assert 'if (rxchar&0x80) setCD((rxchar&0x8)!=0);' in patch
    rows={}
    for row in r['cases']:
        case=folder/row['case'];assert row['passed'] and all(row['checks'].values())
        for name,digest in row['captures'].items():assert sha(case/name)==digest,name
        assert sha(case/'TERMINAL.EXE')==r['parent_sha256']
        assert struct.unpack_from('<2H',(case/'TEST.PRM').read_bytes(),0x198)==(1,int(row['case']=='both'))
        before=(case/'BEFORE.BIN').read_bytes();assert len(before)==42 and before==(case/'AFTER.BIN').read_bytes()
        vectors=(case/'VECOLD.BIN').read_bytes();assert len(vectors)==8 and vectors==(case/'VECNEW.BIN').read_bytes()
        assert (case/'PASS.TXT').exists() and not (case/'FAIL.TXT').exists()
        # This fixture's initial directory is deterministic and contains no
        # dynamic TCP dial target. Rebuild it from its frozen owned source.
        fixture=runpy.run_path(str(folder/'inputs/standalone/directory_fixtures.py'))['directory'](profile=4)
        assert accounting_check(fixture,(case/'TEST.DIR').read_bytes(),1,0 if gap else 1)
        sample=struct.unpack('<12H',(case/'CANCEL.BIN').read_bytes())
        assert sample[0]==0x434d and sample[1]!=0 and sample[2]>18 and sample[3]>8
        assert sample[4]==sample[5]==0 and sample[6]>8
        assert sample[7:10]==(1,int(gap),0) and sample[11]==1
        assert sample[10]==0 if gap else sample[10]>18
        prefix=b'A';tail=b'ATZ\rATDCaseTest:23\r'+ESC+b'[1;16R'+ESC+b'[?62;2cready'+ESC+b'[1;16R+++ATH\r'
        wire=(case/'serial.bin').read_bytes();assert wire==prefix+(b'' if gap else tail)
        events=read(case/'peer-events.json');assert all(x['time']<=y['time'] for x,y in zip(events,events[1:]))
        assert wire==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive')
        decoded=bytearray();status=[];escape=False
        for event in events:
            if event['kind']!='transport-receive':continue
            for byte in bytes.fromhex(event['hex']):
                if escape:
                    escape=False
                    if byte==255:decoded.append(byte)
                    else:assert byte<=7;status.append(byte)
                elif byte==255:escape=True
                else:decoded.append(byte)
        assert not escape and bytes(decoded)==wire and status==[int(e['hex'],16) for e in events if e['kind']=='modem-status']
        first=[e for e in events if e['kind']=='DCD-low'];paused=[e for e in events if e['kind']=='XOFF-first-init'];low=[e for e in events if e['kind']=='cancel-DTR-low'];restored=[e for e in events if e['kind']=='cancel-DTR-restored']
        assert len(first)==len(paused)==len(low)==len(restored)==1 and first[0]['hex']=='ff81' and paused[0]['hex']=='13'
        assert first[0]['time']<paused[0]['time']<low[0]['time']<restored[0]['time']
        assert .8<restored[0]['time']-low[0]['time']<1.3
        assert not any(e['kind']=='receive' and paused[0]['time']<e['time']<restored[0]['time'] for e in events)
        high=[e for e in events if e['kind']=='DCD-high-CONNECT']
        assert len(high)==int(not gap)
        if high:assert high[0]['hex']=='ff8b' and high[0]['time']>restored[0]['time']
        assert sum(e['kind']=='DCD-low-hangup' for e in events)==int(not gap)
        cfg=(case/'dosbox.conf').read_text();assert 'transparent:0' in cfg and 'cputype=8086' in cfg and 'p1600 escape p3000 a-d p8000 r e a d y p700 a-x' in cfg
        rows[row['case']]=dict(passed=True,first_DCD_high_samples=sample[4],first_carrier_history_samples=sample[5],initialization_paused_ticks=sample[3],cancel_DTR_low_ticks=sample[6],idle_pause=sample[8],online_ticks=sample[10],wire_sha256=sha(case/'serial.bin'),modem_status_frames=len(status))
    return r,rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','fixed','cohort','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();old,old_rows=verify(a.baseline.resolve(),True);new,rows=verify(a.fixed.resolve(),False)
    assert old['parent_sha256']!=new['parent_sha256']==sha(ROOT/'build/terminal/TERMINAL.EXE') and old['emulator']==new['emulator']
    for name,digest in new['inputs'].items():assert sha(ROOT/name)==digest,name
    cohort=a.cohort.resolve();output=a.output.resolve();assert cohort.is_relative_to(ROOT/'build') and not cohort.exists()
    assert output.is_relative_to(ROOT/'docs/validation') and not output.exists();cohort.mkdir()
    for item in (a.baseline.resolve(),a.fixed.resolve(),Path(__file__)):
        target=cohort/item.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
        if item.is_dir():shutil.copytree(item,target)
        else:shutil.copy2(item,target)
    files={str(f.relative_to(cohort)):sha(f) for f in cohort.rglob('*') if f.is_file()};(cohort/'files.json').write_text(json.dumps(files,indent=2)+'\n')
    result=dict(passed=True,pre_CONNECT_cancel_lab_accepted=True,stock_emulator_accepted=False,physical_hardware_accepted=False,full_application_accepted=False,baseline_parent_sha256=old['parent_sha256'],parent_sha256=new['parent_sha256'],emulator=new['emulator'],modem_parser_policy='Owned peer discards its partial command buffer on observed DTR fall; retained-parser and physical Boca behavior remain unverified.',baseline=old_rows,fixed=rows,cohort=str(cohort.relative_to(ROOT)),files_manifest_sha256=sha(cohort/'files.json'),auditor_sha256=sha(Path(__file__)),
        scope='Two old/new actual8086 DOS SOFT/BOTH cancellation workflows on a pinned patched UART lab backend. Independent frame decoding, passive first-attempt DCD/carrier history/flow/DTR/controller samples, exact retry/ANSI/manual/hangup streams, accounting, hardware and observer-vector restoration. Stock nullmodem frames expose CTS/DSR only, so the opt-in DCD extension and binary/derivation identities are explicit. No stock-backend, physical modem or full F01-F16 acceptance follows.')
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows),patched_backend=True)))


if __name__=='__main__':main()
