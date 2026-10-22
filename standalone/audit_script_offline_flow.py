#!/usr/bin/env python3
"""Independent raw audit of local File/A launch after observed MODEM loss."""
import argparse,json,re,runpy,shutil,struct
from pathlib import Path
from audit_aspect_transmit_wait import ROOT,sha,read,ESC


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('run','cohort','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();run=a.run.resolve();cohort=a.cohort.resolve();output=a.output.resolve()
    assert run.is_relative_to(ROOT/'build') and cohort.is_relative_to(ROOT/'build') and not cohort.exists()
    assert output.is_relative_to(ROOT/'docs/validation') and not output.exists()
    r=read(run/'checks.json');assert r['passed'] and {row['case'] for row in r['cases']}=={'soft','both'} and len(r['cases'])==2
    for name,digest in r['inputs'].items():
        assert sha(run/'inputs'/name)==digest,name
        if not name.startswith('build/'):assert sha(ROOT/name)==digest,name
    assert 'src/aspect/compiler.py' in r['inputs']
    compiler=runpy.run_path(str(run/'inputs/src/aspect/compiler.py'))['compile_source']
    rows={}
    for row in r['cases']:
        case=run/row['case'];assert row['passed'] and all(row['checks'].values())
        for name,digest in row['captures'].items():assert sha(case/name)==digest,name
        assert sha(case/'TERMINAL.EXE')==r['parent_sha256'] and sha(case/'ASPECT.EXE')==r['runner_sha256']
        assert struct.unpack_from('<2H',(case/'TEST.PRM').read_bytes(),0x198)==(1,int(row['case']=='both'))
        before=(case/'BEFORE.BIN').read_bytes();assert len(before)==42 and before==(case/'AFTER.BIN').read_bytes()
        assert (case/'PASS.TXT').exists() and not (case/'FAIL.TXT').exists()
        raw=(case/'RENDER.BIN').read_bytes();head=struct.unpack_from('<7H',raw)
        assert head[:4]==(0x524e,1,1,1) and head[6]==0
        assert raw[14:34]==raw[34:54] and raw[54:470]==raw[470:886]
        assert struct.unpack('<4H',raw[-8:])==(0,6,1,0)
        assert (case/'LOCAL.OK').read_bytes()==b'OFFLINE SCRIPT'
        assert (case/'GO.ASP').read_bytes()==b'proc main\nfopen 5 "LOCAL.OK" "wb"\nfputs 5 "OFFLINE SCRIPT"\nfclose 5\nendproc\n'
        assert compiler((case/'GO.ASP').read_text())==(case/'GO.ASX').read_bytes()
        log=(case/'dosbox.log').read_text();dial=(case/'DIAL.IN').read_bytes()[275:296].split(b'\0',1)[0].decode();assert dial.startswith('127.0.0.1:')
        assert re.findall(r'Command sent to modem: ->(.*?)<-',log)==['ATZ','ATD'+dial,'ATZ','ATD'+dial]
        assert re.findall(r'Modem response: (.*)',log)==['OK','CONNECT 57600','NO CARRIER','OK','CONNECT 57600','NO CARRIER']
        wire=(case/'serial.bin').read_bytes();prefix=ESC+b'[1;16R'+ESC+b'[?62;2c'
        assert wire==prefix+prefix+b'ready'+ESC+b'[1;16R'
        events=read(case/'peer-events.json');assert all(x['time']<=y['time'] for x,y in zip(events,events[1:]))
        assert wire==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive')
        assert [e['session'] for e in events if e['kind']=='connected']==[1,2]
        assert next(e['time'] for e in events if e['kind']=='first-hangup')<next(e['time'] for e in events if e['kind']=='connected' and e['session']==2)
        assert sum(e['kind']=='completed-hangup' for e in events)==1
        cfg=(case/'dosbox.conf').read_text();assert 'cputype=8086' in cfg and 'a-z p200 a p200 g o . a s x enter p2400 a-d' in cfg
        rows[row['case']]=dict(passed=True,actual_child_exit=0,offline_sample=[0,6,1,0],local_file_bytes=14,wire_sha256=sha(case/'serial.bin'),clean_initializations=2,connections=2)
    cohort.mkdir();shutil.copytree(run,cohort/run.relative_to(ROOT))
    target=cohort/Path(__file__).relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(__file__,target)
    files={str(f.relative_to(cohort)):sha(f) for f in cohort.rglob('*') if f.is_file()};(cohort/'files.json').write_text(json.dumps(files,indent=2)+'\n')
    result=dict(passed=True,local_offline_Script_component_accepted=True,physical_hardware_accepted=False,full_application_accepted=False,parent_sha256=r['parent_sha256'],runner_sha256=r['runner_sha256'],cases=rows,
        cohort=str(cohort.relative_to(ROOT)),files_manifest_sha256=sha(cohort/'files.json'),auditor_sha256=sha(Path(__file__)),
        earlier_fixture_failure='build/script-offline-modem-dos/offline-program-01/checks.json: extra acknowledgement space sent after immediate adopted-render return; unaccepted. Corrected recipe removes that key, not a product behavior change.',
        scope=__doc__+' Two actual8086 SOFT/BOTH workflows: passive direct-EXEC snapshot, source-built ASPECT marker and cleanup, clean ATZ/OK after real virtual-modem DCD loss, exact manual/query and BBS streams, hardware/JFT/file-owner restoration. Selected success paths only; helper errors, other DCD/flow paths, physical and full F01-F16 gates remain open.')
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows))))


if __name__=='__main__':main()
