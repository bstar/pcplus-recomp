#!/usr/bin/env python3
"""Audit raw missing-runner/script/header recovery after MODEM loss."""
import argparse,json,re,runpy,shutil,struct
from pathlib import Path
from audit_aspect_transmit_wait import ROOT,sha,read,ESC


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('run','cohort','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();run=a.run.resolve();cohort=a.cohort.resolve();output=a.output.resolve()
    assert all(p.is_relative_to(ROOT/'build') for p in (run,cohort)) and not cohort.exists()
    assert output.is_relative_to(ROOT/'docs/validation') and not output.exists()
    r=read(run/'checks.json');assert r['passed']
    assert {c['case'] for c in r['cases']}=={kind+'-'+flow for kind in ('missing-runner','missing-script','bad-header') for flow in ('soft','both')} and len(r['cases'])==6
    for name,digest in r['inputs'].items():
        assert sha(run/'inputs'/name)==digest,name
        if not name.startswith('build/'):assert sha(ROOT/name)==digest,name
    compiler=runpy.run_path(str(run/'inputs/src/aspect/compiler.py'))['compile_source'];rows={}
    for row in r['cases']:
        assert row['passed'] and all(row['checks'].values());case=run/row['case'];kind=row['case'].rsplit('-',1)[0];missing=kind=='missing-runner'
        for name,digest in row['captures'].items():assert sha(case/name)==digest,name
        assert sha(case/'TERMINAL.EXE')==r['parent_sha256']
        assert (case/'ASPECT.EXE').exists()!=missing
        if not missing:assert sha(case/'ASPECT.EXE')==r['runner_sha256']
        assert (case/'GO.ASX').exists()!=(kind=='missing-script')
        if missing:assert (case/'GO.ASX').read_bytes()==compiler((case/'GO.ASP').read_text())
        if kind=='bad-header':assert (case/'GO.ASX').read_bytes()==b'\x81'
        assert not (case/'BAD.OK').exists()
        assert struct.unpack_from('<2H',(case/'TEST.PRM').read_bytes(),0x198)==(1,int(row['case'].endswith('both')))
        before=(case/'BEFORE.BIN').read_bytes();assert len(before)==42 and before==(case/'AFTER.BIN').read_bytes()
        assert (case/'PASS.TXT').exists() and not (case/'FAIL.TXT').exists()
        raw=(case/'RENDER.BIN').read_bytes();head=struct.unpack_from('<7H',raw);sample=struct.unpack('<6H',raw[-12:])
        assert head[:3]==(0x524e,1,1) and sample[:4]==(0,6,1,0)
        assert (head[3],head[6])==((0,65535) if missing else (1,1 if kind=='missing-script' else 2))
        if missing:assert sample[4]==2 and sample[5]&1
        else:assert not sample[5]&1
        assert raw[14:34]==raw[34:54] and raw[54:470]==raw[470:886]
        log=(case/'dosbox.log').read_text();dial=(case/'DIAL.IN').read_bytes()[275:296].split(b'\0',1)[0].decode();assert dial.startswith('127.0.0.1:')
        assert re.findall(r'Command sent to modem: ->(.*?)<-',log)==['ATZ','ATD'+dial,'ATZ','ATD'+dial]
        assert re.findall(r'Modem response: (.*)',log)==['OK','CONNECT 57600','NO CARRIER','OK','CONNECT 57600','NO CARRIER']
        wire=(case/'serial.bin').read_bytes();prefix=ESC+b'[1;16R'+ESC+b'[?62;2c';assert wire==prefix+prefix+b'ready'+ESC+b'[1;16R'
        events=read(case/'peer-events.json');assert all(x['time']<=y['time'] for x,y in zip(events,events[1:]))
        assert wire==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive')
        assert [e['session'] for e in events if e['kind']=='connected']==[1,2]
        assert next(e['time'] for e in events if e['kind']=='first-hangup')<next(e['time'] for e in events if e['kind']=='connected' and e['session']==2)
        assert sum(e['kind']=='completed-hangup' for e in events)==1
        cfg=(case/'dosbox.conf').read_text();assert 'cputype=8086' in cfg and 'a-z p200 a p200 g o . a s x enter' in cfg
        assert ('p1600 space p800 a-d' if missing else 'p2400 a-d') in cfg
        rows[row['case']]=dict(passed=True,offline_sample=list(sample[:4]),actual_child_exits=head[3],child_exit=None if missing else head[6],DOS_EXEC_carry=bool(sample[5]&1),DOS_EXEC_error=sample[4] if missing else None,wire_sha256=sha(case/'serial.bin'),connections=2)
    cohort.mkdir();shutil.copytree(run,cohort/run.relative_to(ROOT))
    target=cohort/Path(__file__).relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(__file__,target)
    files={str(f.relative_to(cohort)):sha(f) for f in cohort.rglob('*') if f.is_file()};(cohort/'files.json').write_text(json.dumps(files,indent=2)+'\n')
    result=dict(passed=True,selected_offline_error_recovery_accepted=True,physical_hardware_accepted=False,full_application_accepted=False,parent_sha256=r['parent_sha256'],runner_sha256=r['runner_sha256'],cases=rows,cohort=str(cohort.relative_to(ROOT)),files_manifest_sha256=sha(cohort/'files.json'),auditor_sha256=sha(Path(__file__)),
        scope=__doc__+' Six actual8086 SOFT/BOTH cases. Absent helper causes real DOS EXEC CF1/error2 and no child exit; present helper returns1 for absent script and2 for one-byte invalid header. Passive offline/return flags, unreachable-file absence, exact modem/BBS/query streams and hardware/JFT/file-owner cleanup checked. Known synthetic file faults only; allocation/media/error families, other DCD/flow paths, physical and all full F01-F16 gates remain open.')
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=len(rows))))


if __name__=='__main__':main()
