#!/usr/bin/env python3
"""Actual DOS Escape during owned ENiGMA ZMODEM, then retry on the same link."""
import argparse,asyncio,contextlib,hashlib,json,re,shutil,struct,sys,zlib
from pathlib import Path
import test_dos
from test_transfer_dos import ObservedModem,timestamp,offset_after
from audit_zmodem import scan,packet,metadata,audit_batch,audit_controls
from enigma_key_stream_fixture import ROOT,PORT,owned,verify_running
from enigma_notes_dos import sha,messages


async def run(args):
    assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    candidate=owned(args.candidate);log=verify_running(candidate)
    fixture=json.loads((candidate/'search-instance.json').read_text())
    assert fixture['transfer_bytes']>=32768
    inputs={p:candidate/p for p in [*fixture['fixture_inputs'],*fixture['source_modules']]}
    for p,h in {**fixture['fixture_inputs'],**fixture['source_modules']}.items():assert sha(inputs[p])==h,p
    archive=fixture['archives'][1];source=candidate/'file_base/pcplus_games'/archive['name']
    payload=source.read_bytes();assert sha(source)==archive['sha256']
    name=archive['name'].upper();local=f'{zlib.crc32(name.encode()):08X}.ZIP'
    out=ROOT/'build/bbs-lab/results/enigma'/args.label;out.mkdir(parents=True,exist_ok=False)
    target=out/'RECV';target.mkdir();stage=out/'program';stage.mkdir()
    binary=ROOT/'build/terminal/TERMINAL.EXE';shutil.copyfile(binary,stage/'TERMINAL.EXE')
    inputs.update(terminal=binary,staged_terminal=stage/'TERMINAL.EXE',archive=source,runner=Path(__file__),
        harness=Path(test_dos.__file__),observer=ROOT/'lab/bbs/test_transfer_dos.py',auditor=ROOT/'lab/bbs/audit_zmodem.py',
        cancel_observer=ROOT/'lab/bbs/zmodem_cancel_watch.py',label_observer=ROOT/'lab/bbs/zmodem_label_watch.py',
        sampler_base=ROOT/'standalone/test_terminal.py',modem=ROOT/'lab/bbs/modem.py',
        terminal_manifest=binary.parent/'manifest.json')
    before={p:sha(f) for p,f in inputs.items()};posts=messages(candidate)
    canonical=json.loads((ROOT/'lab/bbs/editor-recipes.json').read_text())['enigma_unsaved']['keyboard_input']
    prefix=canonical[:canonical.index('M enter')].replace('n p6000 n p3000 enter','n p6000 enter')
    keys=prefix+('c-y F enter p1600 S enter p1600 P C P L U S space P R O B E space 0 1 enter p2000 enter p1600 '
        'd p1500 a p1000 enter p10000 enter p1600 n p1500 '
        'd p1200 a p800 enter p40000 enter p1200 n p1600')
    assert len('ADDKEY p1000 '+keys+' p2000 a-x')<500
    observed=[];snapshots=[];finished=asyncio.Event()
    class Observer(ObservedModem):
        def __init__(self,*a,**kw):super().__init__(*a,**kw);observed.append(self)
    original_modem=test_dos.Modem;original_fixture=test_dos.modem_fixture;original_sampler=test_dos.SAMPLER
    from zmodem_cancel_watch import SAMPLER
    test_dos.SAMPLER=SAMPLER
    def settings(**kwargs):
        data=bytearray(original_fixture(**kwargs));data[0x42c:0x42e]=b'\x01\0'
        path=b'D:\\RECV\\\0';data[0x31c:0x31c+len(path)]=path;return bytes(data)
    async def watch():
        while not finished.is_set():
            if observed and not snapshots:
                raw=bytes(observed[0].keyboard);at=raw.find(b'\x18'*8+b'\x08'*10)
                if at>=0 and raw.find(b'n',at+18)>=0:
                    snapshots.append(dict(files={p.name:sha(p) for p in target.iterdir()},cancel_offset=at))
            await asyncio.sleep(.05)
    task=asyncio.create_task(watch());test_dos.Modem=Observer;test_dos.modem_fixture=settings
    options=argparse.Namespace(name='enigma',label=args.label,port=PORT,com=2,baud=19200,flow='HARD',packet_delay_ms=0,
        dial_fixture=True,directory_fixture=False,directory_browser=False,entry=3,binary=stage/'TERMINAL.EXE',config_fixture=False,
        keymap_fixture=ROOT/'build/keyboard-profiles/NETWORK.KBD',server_log=log,keys=keys,wait=2,timeout=190)
    try:
        with (out/'harness.log').open('w') as capture,contextlib.redirect_stdout(capture):code=await test_dos.run(options)
    finally:
        test_dos.Modem=original_modem;test_dos.modem_fixture=original_fixture;test_dos.SAMPLER=original_sampler;finished.set();await task
    assert len(observed)==1
    modem=observed[0];stream=bytes(modem.display);opposite=bytes(modem.keyboard)
    (out/'trace.json').write_text(json.dumps(modem.trace,indent=2)+'\n')
    (out/'cancel-snapshots.json').write_text(json.dumps(snapshots,indent=2)+'\n')
    harness=json.loads((out/'result.json').read_text());errors=[];protocol={}
    checks=dict(DOS_harness=code==0 and harness['passed'],inputs_unchanged=before=={p:sha(f) for p,f in inputs.items()},
        no_post_saved=posts==messages(candidate),partial_and_stage_removed=bool(snapshots) and snapshots[0]['files']=={},
        retry_file_exact=(target/local).is_file() and (target/local).read_bytes()==payload,
        only_expected_file={p.name for p in target.iterdir()}=={local},decoded_offsets_match=modem.bbs_offset==len(stream) and modem.dos_offset==len(opposite))
    labels=(out/'LABELS.BIN').read_bytes() if (out/'LABELS.BIN').exists() else b''
    checks['BIOS_Escape_after_visible_KiB']=len(labels)==2566 and struct.unpack_from('<H',labels)[0]==0x4e5a and bool(struct.unpack_from('<H',labels,4)[0]&0x8000)
    try:
        cancel_at=opposite.index(b'\x18'*8+b'\x08'*10);cancel_time=timestamp(modem.trace,'dos',cancel_at)
        first=[]
        for h in scan(stream):
            if h['type']==4 and timestamp(modem.trace,'bbs',h['offset'])<cancel_time:
                p=packet(stream,h['end'],h['format']);assert metadata(p['payload'])==(name,len(payload));first.append(h)
        assert first,'No CRC-valid ZFILE before local cancel'
        data=[h for h in scan(stream) if h['type']==10 and first[0]['offset']<h['offset'] and timestamp(modem.trace,'bbs',h['offset'])<cancel_time]
        assert data,'Cancel did not interrupt actual data transfer'
        first_data=packet(stream,data[0]['end'],data[0]['format'])
        assert first_data['payload']==payload[:len(first_data['payload'])] and first_data['payload'],'First data packet is not CRC-valid source data'
        assert not any(h['type']==11 and first[0]['offset']<h['offset'] and timestamp(modem.trace,'bbs',h['offset'])<cancel_time for h in scan(stream)),'Transfer already completed before Escape'
        post=opposite.index(b'n',cancel_at+18);post_time=timestamp(modem.trace,'dos',post)
        tail_at=offset_after(modem.trace,'bbs',post_time);assert tail_at is not None
        retry=audit_batch(stream,{name:payload},tail_at)
        assert b'NFO | lines 1-15/24' in stream[tail_at:retry['start']],'No NFO response between cancel and retry'
        end_time=timestamp(modem.trace,'bbs',retry['end']-1)
        post2=opposite.index(b'n',offset_after(modem.trace,'dos',end_time));post2_time=timestamp(modem.trace,'dos',post2)
        retry['controls']=audit_controls(retry,opposite,modem.trace,'bbs',post2_time,False)
        after=offset_after(modem.trace,'bbs',post2_time);assert after is not None
        assert b'NFO | lines 1-15/24' in stream[after:] and b'PCPLUS NFO LINE 01 : synthetic game 01' in stream[after:]
        for f in retry['files']:f.pop('source')
        protocol=dict(cancel_offset=cancel_at,first_offer=first[0],data_before_cancel=len(data),retry=retry)
        checks['cancel_during_data_then_NFO_then_exact_retry_then_NFO']=True
    except (AssertionError,ValueError,TypeError) as e:
        errors.append(str(e));checks['cancel_during_data_then_NFO_then_exact_retry_then_NFO']=False
    boundary=json.loads((out/'server-log-start.json').read_text());assert log.stat().st_ino==boundary['inode']
    with log.open('rb') as f:f.seek(boundary['byte_offset']);rows=[json.loads(l) for l in f if l.strip()]
    sessions={r['sessionId'] for r in rows if r.get('msg')=='User "loclab" successfully logged in'}
    own=[r for r in rows if r.get('sessionId') in sessions]
    (out/'server-session.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in own))
    executions=[i for i,r in enumerate(own) if r.get('msg')=='Executing external protocol']
    exits=[(i,r.get('exitCode')) for i,r in enumerate(own) if r.get('msg')=='Process exited']
    checks['unique_authenticated_session']=len(sessions)==1
    checks['two_protocol_processes_returned']=len(executions)==len(exits)==2 and executions[0]<exits[0][0]<executions[1]<exits[1][0] and exits[0][1]!=0 and exits[1][1]==0
    result=dict(passed=all(checks.values()) and not errors,checks=checks,errors=errors,protocol=protocol,
        terminal_sha256=sha(binary),input_hashes=before,source_modules=fixture['source_modules'],snapshots=snapshots,
        wire_name=name,local_name=local,archive_bytes=len(payload),server_exit_codes=[v for i,v in exits],
        scope='Actual DOS local Escape during owned ENiGMA ZMODEM data; same-connection NFO, full retry, NFO. Generated archive, unchanged real protocol peer and byte-transparent modem. Modeled19200/HARD; no live-server or physical modem claim.')
    (out/'cancel-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'],checks=checks,errors=errors),indent=2))
    return 0 if result['passed'] else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--label',required=True)
    raise SystemExit(asyncio.run(run(p.parse_args())))
