#!/usr/bin/env python3
"""Preserve recorder/BBS failures without promoting partial checks to acceptance."""
import argparse,hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cohort',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    cohort=a.cohort.resolve();output=a.output.resolve()
    assert cohort.is_relative_to(ROOT/'build') and not cohort.exists()
    assert output.is_relative_to(ROOT/'docs/validation') and not output.exists()
    selected={Path(__file__).resolve()};attempts={}
    for label in ('recorder-current-01','recorder-current-02','recorder-current-03'):
        attempts[label]={}
        for name in ('synchronet','enigma'):
            stage=ROOT/'build/bbs-lab/recording'/name/label;result=read(stage/'result.json')
            assert not result['passed'] and not result['checks']['both_sessions']
            assert result['checks']['sources_unchanged'] and result['checks']['no_retained_temporary_files']
            assert result['sessions']['record']['checks']['exact_user_payload']
            assert result['sessions']['record']['checks']['DOS_and_hardware']
            for source,digest in result['inputs'].items():assert sha(stage/'frozen-source'/source)==digest,source
            for path,digest in result['artifacts'].items():assert sha(stage/path)==digest,path
            assert sha(stage/'TERMINAL.EXE')==result['binary_sha256']
            selected.update(p for p in stage.rglob('*') if p.is_file())
            for mode,session in result['sessions'].items():
                folder=(ROOT/session['result']).parent
                for path,digest in session['artifacts'].items():assert sha(folder/path)==digest,path
                selected.update(p for p in folder.rglob('*') if p.is_file())
                if label!='recorder-current-01' and mode=='replay':
                    assert not session['passed'] and not session['checks']['DOS_and_hardware']
            attempts[label][name]=dict(binary_sha256=result['binary_sha256'],
                result=str((stage/'result.json').relative_to(ROOT)),
                source_sha256=sha(stage/'PCPLUS.ASP'),
                sessions={mode:dict(passed=session['passed'],checks=session['checks'],user_hex=session['user_hex'])
                          for mode,session in result['sessions'].items()})
    cohort.mkdir();kept={}
    for path in sorted(selected):
        target=cohort/'retained'/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target);assert sha(target)==sha(path)
        kept[str(target.relative_to(ROOT))]=sha(target)
    report=dict(diagnostic_evidence_preserved=True,modern_BBS_recording_replay_accepted=False,
        attempts=attempts,custody_sha256=kept,
        scope='Recording and DOS compilation succeed on both synthetic local BBS accounts. Initial audit mistakes are distinct from genuine fresh-session replay failures. The mapped-lead correction improves Synchronet output but does not establish normal replay exit, parent return or hardware cleanup. ENiGMA replay remains incomplete. No audio, physical modem or full application acceptance.')
    with output.open('x') as f:f.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(diagnostic_evidence_preserved=True,accepted=False,files=len(kept))))


if __name__=='__main__':main()
