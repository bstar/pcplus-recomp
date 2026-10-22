#!/usr/bin/env python3
"""Reject diagnostic marker evidence at production helper/preparation/audio boundaries."""
import argparse,json,sys
from pathlib import Path
import audio_recording
import record_recording_audio as audio
import record_recording_audio_preparation as preparation
from synthmodem_vm_control import ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('normal','trace','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    normal=json.loads(a.normal.read_text());trace=json.loads(a.trace.read_text())
    assert normal['passed'] and trace['passed'] and not normal['diagnostic_marker_trace'] and trace['diagnostic_marker_trace']
    assert len(normal['cases'])==7 and len(trace['cases'])==8
    assert normal['production_helper_sha256']==trace['production_helper_sha256']
    audio_recording.inputs(a.normal)
    rows=[]
    def rejected(name,fn,message):
        try:fn()
        except AssertionError as error:assert message in str(error);rows.append(dict(case=name,rejected=True))
        else:raise AssertionError('Diagnostic evidence admitted: '+name)
    rejected('production-helper-proof',lambda:audio_recording.inputs(a.trace),'Diagnostic marker counters')
    fixture=out/'synthetic';fixture.mkdir()
    def write(name,data):(fixture/name).write_text(json.dumps(data)+'\n')
    # Untrusted owned metadata only. These fixtures cannot establish a real
    # audio result; they verify the named diagnostic guard runs before publish.
    write('result.json',dict(route='recording',recording_key_checks='synthetic',recording_tcp_checks='synthetic',recording_marker_trace=True))
    for name in ('independent-audit.json','serial-io-audit.json','offline-caller.json'):write(name,{})
    forbidden=ROOT/'docs/validation'/('never-publish-'+out.name+'.json');assert not forbidden.exists()
    sys.argv=[str(audio.__file__),str(fixture),'--output',str(forbidden)]
    rejected('production-audio-receipt',audio.main,'Diagnostic helper cannot establish production audio acceptance')
    write('tcp.json',dict(passed=True,checks={'synthetic':True},helper_sha256=normal['production_helper_sha256'],inputs={},captures_sha256={}))
    write('run-start.json',dict(route='recording',recording_marker_trace=True))
    sys.argv=[str(preparation.__file__),'--keys',str(a.normal.resolve()),'--tcp',str(fixture/'tcp.json'),'--runtime',str(fixture),'--runtime-proof',str(fixture/'tcp.json'),'--audio-cohort',str(fixture),'--cohort',str(out/'never-create'),'--output',str(forbidden)]
    rejected('production-preparation-receipt',preparation.main,'Diagnostic helper cannot establish production preparation')
    assert not forbidden.exists() and not (out/'never-create').exists()
    result=dict(passed=True,cases=rows,production_helper_sha256=normal['production_helper_sha256'],normal_proof_sha256=sha(a.normal),trace_proof_sha256=sha(a.trace),inputs={str(path.relative_to(ROOT)):sha(path) for path in (Path(__file__).resolve(),Path(audio.__file__),Path(preparation.__file__),Path(audio_recording.__file__))},scope=__doc__+' Controlled synthetic metadata for rejection only. No audio/preparation receipt or cohort is published.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,rejected=len(rows))))


if __name__=='__main__':main()
