#!/usr/bin/env python3
"""Seal a complete normal DOS recorder/ASP compiler/replay software-audio run."""
import argparse,json,re,struct,subprocess
from pathlib import Path
import enigma
from synthmodem_vm_control import ROOT,sha
from synthmodem_buffered_runtime import validate as validate_runtime


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.cohort.resolve();target=a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and target.is_relative_to(ROOT/'docs/validation') and not target.exists()
    read=lambda name:json.loads((out/name).read_text())
    r=read('result.json');audit=read('independent-audit.json');io=read('serial-io-audit.json');offline=read('offline-caller.json')
    assert r['route']=='recording' and r['recording_key_checks'] and r['recording_tcp_checks']
    assert r['buffered_runtime_proof'] and r['posttrain_hold'] and r['input_sequence_timeout_ms']==250
    assert r['server_fixture'] is None and Path(r['server_root'])==enigma.SOURCE and r['server_revision']==enigma.COMMIT
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=enigma.SOURCE,text=True).strip()==enigma.COMMIT
    subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=enigma.SOURCE,check=True)
    for report in (r,audit):assert report['passed'] and all(report['checks'].values())
    assert io['evidence_consistent'] and all(io['checks'].values()) and not io['error_events']
    assert all(io['counters'][name]==0 for name in ('pendingBytes','failedCallbackBytes','skippedBytes'))
    def inputs(group):
        for name,digest in group.items():assert sha(ROOT/name)==digest,name
    def captures(group):
        for name,digest in group.items():assert sha(out/name)==digest,name
    for group in ('frozen_inputs','runtime_inputs','tool_inputs'):inputs(r[group])
    for group in ('generated_inputs','captures_sha256'):captures(r[group])
    for name,digest in r['frozen_inputs'].items():assert sha(out/'frozen-source'/name)==digest,name
    inputs(audit['audit_inputs']);captures(io['capture_sha256'])
    assert audit['producer_sha256']==sha(out/'result.json')
    assert audit['auditor_sha256']==r['frozen_inputs']['lab/bbs/audit_synthmodem_audio_dos.py']
    assert io['auditor_sha256']==r['frozen_inputs']['lab/bbs/audit_serial_io_evidence.py']
    assert read('exit-status.json')==dict(DOS=0,node=0)
    assert read('node-result.json')==r['gateway'] and r['gateway']['pool']=='stopped' and r['gateway']['VM_exited']
    start=read('run-start.json')
    for group in ('frozen_inputs','runtime_inputs','tool_inputs','generated_inputs','server_inputs'):assert start[group]==r[group],group
    assert start['route']=='recording' and start['profile_sha256']==sha(out/'MODEM.PRM')
    assert 'program/PCPLUS.ASP' not in start['generated_inputs'] and 'program/PCPLUS.ASX' not in start['generated_inputs']
    journal=read('server-log-capture/result.json');assert journal['passed']
    assert journal['boundary']==read('server-log-boundary.json') and journal['boundary_sha256']==sha(out/'server-log-boundary.json')
    all_rows=[]
    for segment in journal['segments']:
        path=out/'server-log-capture'/segment['capture'];body=path.read_bytes()
        assert sha(path)==segment['sha256'] and len(body)==segment['end']-segment['start']
        all_rows.extend(json.loads(line) for line in body.splitlines() if line.strip())
    assert len(all_rows)==journal['records']
    rows=[json.loads(line) for line in (out/'server-session.jsonl').read_text().splitlines()]
    ids={row['sessionId'] for row in rows if row.get('msg')=='User "loclab" successfully logged in'}
    assert len(ids)==1;session=ids.pop()
    assert [row for row in all_rows if row.get('sessionId')==session]==rows
    for name,digest in r['server_inputs'].items():assert sha(enigma.SOURCE/name)==digest,name
    first=Path(next(iter(r['runtime_inputs'])))
    runtime=next(path for path in first.parents if (path/'source/config.js').is_file())
    assert validate_runtime(runtime,ROOT/r['buffered_runtime_proof'])==r['runtime_inputs']
    keys=json.loads((ROOT/r['recording_key_checks']).read_text());tcp=json.loads((ROOT/r['recording_tcp_checks']).read_text())
    assert keys['passed'] and len(keys['cases'])==6 and all(case['passed'] and all(case['checks'].values()) for case in keys['cases'])
    assert tcp['passed'] and all(tcp['checks'].values());inputs(keys['inputs']);inputs(tcp['inputs'])
    assert sha(out/'program/EXITKEY.COM')==keys['production_helper_sha256']==tcp['helper_sha256']
    for name,path in (('TERMINAL.EXE','build/terminal/TERMINAL.EXE'),('ASPECT.EXE','build/aspect-runner/ASPECT.EXE'),('ASPCOMP.EXE','build/aspect-compiler-dos/ASPCOMP.EXE')):
        assert sha(out/'program'/name)==r['frozen_inputs'][path]
    source=(out/'program/PCPLUS.ASP').read_bytes()
    payload=b''.join(bytes.fromhex(value.decode()) for value in re.findall(rb'^transmitraw "([0-9A-F]*)"\r?$',source,re.M))
    assert payload==b'S\r\x1b' and source.endswith(b'endproc\r\n')
    assert audit['recording']['source_sha256']==r['recording']['source_sha256']==sha(out/'program/PCPLUS.ASP')
    assert audit['recording']['bytecode_sha256']==r['recording']['bytecode_sha256']==sha(out/'program/PCPLUS.ASX')
    helper=struct.unpack('<8H',(out/'RECKEY.BIN').read_bytes());assert helper[:4]==(0x524b,14,26,1)
    before=(out/'BEFORE.BIN').read_bytes();after=(out/'AFTER.BIN').read_bytes()
    assert len(before)==42 and before==after
    assert (out/'KEYOLD.BIN').read_bytes()==(out/'KEYNEW.BIN').read_bytes() and len((out/'KEYOLD.BIN').read_bytes())==4
    serial=(out/'serial-in.bin').read_bytes();assert serial.startswith(b'ATZ\rATD1\r');online=serial[9:]
    assert offline['checker_sha256']==r['frozen_inputs']['lab/bbs/diagnose_audio_caller.js']
    assert offline['capture_sha256']==sha(out/'rtp-from-caller.bin')
    assert offline['decoder_sha256']==sha(runtime/'source/src/dsp/protocols/V22Demodulator.js')
    assert bytes.fromhex(''.join(row['hex'] for row in offline['received']))==online
    names=list(dict.fromkeys([*r['captures_sha256'],*r['generated_inputs'],'result.json','node-result.json','dosbox.conf',
        'independent-audit.json','serial-io-audit.json','offline-caller.json']))
    result=dict(passed=True,actual_ENiGMA_recording_audio_accepted=True,full_F13_accepted=False,
        cohort=str(out.relative_to(ROOT)),check_counts=dict(producer=len(r['checks']),independent=len(audit['checks']),
            serial=len(io['checks']),BIOS=sum(len(case['checks']) for case in keys['cases']),TCP=len(tcp['checks'])),
        producer_checks=r['checks'],independent_checks=audit['checks'],serial_checks=io['checks'],
        recording=audit['recording'],helper_report=helper,exact_online_bytes=len(online),payloads=audit['payloads'],
        hardware_snapshot=audit['hardware_snapshot'],serial_counters=io['counters'],
        terminal_sha256=sha(out/'program/TERMINAL.EXE'),ASPECT_sha256=sha(out/'program/ASPECT.EXE'),ASPCOMP_sha256=sha(out/'program/ASPCOMP.EXE'),
        server_revision=r['server_revision'],server_root=r['server_root'],server_inputs=r['server_inputs'],
        producer_inputs=r['frozen_inputs'],runtime_inputs=r['runtime_inputs'],tool_inputs=r['tool_inputs'],audit_inputs=audit['audit_inputs'],
        buffered_runtime_proof=r['buffered_runtime_proof'],helper_proof=r['recording_key_checks'],TCP_proof=r['recording_tcp_checks'],
        captures_sha256={name:sha(out/name) for name in names},recorder_sha256=sha(Path(__file__)),
        scope='One normal source-built DOS File/C recording, File/A explicit ASP DOS compilation/replay and subsequent manual Search on the pinned owned stock ENiGMA through software SIP/RTP/V22-1200 DSP/Telnet at38400DTE. Exact recorded user bytes, compiled file, BBS route, full byte streams, independent caller waveform, hardware/timer/SIP/VM cleanup and source/runtime custody pass. No generated recording edits or prebuilt target ASX. Other profiles, peers, arbitrary prompts, physical Boca/SPA2102,14.4 negotiation and all full F01-F16 gates remain open.')
    with target.open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,actual_ENiGMA_recording_audio_accepted=True,checks=result['check_counts'])))


if __name__=='__main__':main()
