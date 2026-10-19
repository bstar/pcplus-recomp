#!/usr/bin/env python3
"""Actual DOS: receive a long-name ZIP, skip it, then receive another ZIP.

The existing DOS keyboard/UART harness is unchanged. Its modem class is replaced
only by the passive stream observer; synthetic PRM fields enable automatic
ZMODEM reception into the owned test drive. No protocol response is fabricated.
"""
import argparse,asyncio,contextlib,hashlib,json,re,shutil,struct,sys,zlib
from pathlib import Path
import test_dos
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'lab/bbs'))
from test_transfer_dos import ObservedModem,timestamp,offset_after
from audit_zmodem import scan,packet,metadata,audit_batch,audit_controls
from enigma_key_stream_fixture import owned,verify_running,PORT
from enigma_notes_dos import sha,messages


def alias(name):return f'{zlib.crc32(name.upper().encode("ascii")):08X}.ZIP'
def file_state(directory):
    result={}
    for p in directory.iterdir():
        st=p.stat();result[p.name]=dict(inode=st.st_ino,size=st.st_size,mtime_ns=st.st_mtime_ns,ctime_ns=st.st_ctime_ns,sha256=sha(p))
    return result


def audit(stream,opposite,trace,names,payloads):
    finishes=[h for h in scan(stream) if h['type']==8 and stream[h['end']:h['end']+2]==b'OO']
    assert len(finishes)==3,('Expected three complete sessions',len(finishes))
    results=[];previous=0
    for i,finish in enumerate(finishes):
        expected=names[0 if i<2 else 1];offers=[]
        headers=list(scan(stream,previous));headers=[h for h in headers if h['offset']<finish['offset']]
        for h in headers:
            if h['type']!=4:continue
            p=packet(stream,h['end'],h['format']);name,size=metadata(p['payload'])
            assert name==expected and size==len(payloads[expected]) and p['ending']==107
            offers.append((h,p))
        assert offers,('Missing validated offer',i)
        first=offers[0][0];offer_time=timestamp(trace,'bbs',first['offset'])
        end_time=timestamp(trace,'bbs',finish['end']+1)
        lower=offset_after(trace,'dos',end_time);assert lower is not None
        post=opposite.find(b'n',lower);assert post>=0
        post_time=timestamp(trace,'dos',post)
        next_start=finishes[i+1]['offset'] if i<2 else len(stream)
        tail_at=offset_after(trace,'bbs',post_time);assert tail_at is not None
        tail=stream[tail_at:next_start]
        game=1 if i<2 else 2
        assert b'NFO | lines 1-15/24' in tail and f'PCPLUS NFO LINE 01 : synthetic game {game:02d}'.encode() in tail
        invitations=[h for h in headers if h['type']==0 and h['format']==66 and h['position']>>24==0 and h['offset']<first['offset']]
        assert invitations,'Missing automatic receive invitation'
        invitation_time=timestamp(trace,'bbs',invitations[-1]['end']-1)
        replies=[h for h in scan(opposite) if h['type']==1 and invitation_time<=timestamp(trace,'dos',h['offset'])<=offer_time]
        assert replies,'Missing actual receiver negotiation'
        if i!=1:
            transaction=audit_batch(stream,{expected:payloads[expected]},first['offset'])
            assert transaction['end']==finish['end']+2
            controls=audit_controls(transaction,opposite,trace,'bbs',post_time,False)
            assert len(transaction['files'])==1
            for f in transaction['files']:f.pop('source')
            results.append(dict(kind='received',wire_name=expected,local_name=alias(expected),post_menu=True,protocol=transaction,controls=controls))
        else:
            assert not any(h['type'] in (10,11) for h in headers),'Skipped transfer contained file data/EOF'
            skip=[h for h in scan(opposite) if h['type']==5 and h['position']==0 and timestamp(trace,'bbs',offers[-1][1]['crc_end']-1)<=timestamp(trace,'dos',h['offset'])<=end_time]
            assert skip,'No CRC-valid ZSKIP after the offer'
            finish_reply=[h for h in scan(opposite) if h['type']==8 and h['position']==0 and timestamp(trace,'bbs',finish['offset'])<=timestamp(trace,'dos',h['offset'])<=post_time]
            assert finish_reply,'No receiver ZFIN for skipped session'
            results.append(dict(kind='skipped-existing',wire_name=expected,local_name=alias(expected),post_menu=True,offer=first,finish=finish,skip=skip[0],finish_reply=finish_reply[0]))
        previous=finish['end']+2
    return results


async def run(args):
    assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    candidate=owned(args.candidate);log=verify_running(candidate)
    fixture=json.loads((candidate/'search-instance.json').read_text())
    for p,h in fixture['fixture_inputs'].items():assert sha(candidate/p)==h,p
    for p,h in fixture['source_modules'].items():assert sha(candidate/p)==h,p
    archives=fixture['archives'][1:3];names=[a['name'].upper() for a in archives]
    payloads={a['name'].upper():(candidate/'file_base/pcplus_games'/a['name']).read_bytes() for a in archives}
    for a in archives:assert hashlib.sha256(payloads[a['name'].upper()]).hexdigest()==a['sha256']
    out=ROOT/'build/bbs-lab/results/enigma'/args.label;out.mkdir(parents=True,exist_ok=False)
    target=out/'RECV';target.mkdir();stage=out/'program';stage.mkdir()
    binary=ROOT/'build/terminal/TERMINAL.EXE';shutil.copyfile(binary,stage/'TERMINAL.EXE')
    inputs={p:candidate/p for p in [*fixture['fixture_inputs'],*fixture['source_modules']]}
    inputs.update({'terminal':binary,'staged_terminal':stage/'TERMINAL.EXE','runner':Path(__file__),
        'harness':Path(test_dos.__file__),'observer':ROOT/'lab/bbs/test_transfer_dos.py','auditor':ROOT/'lab/bbs/audit_zmodem.py'})
    if args.observe_labels:inputs['label_observer']=ROOT/'lab/bbs/zmodem_label_watch.py'
    before={p:sha(f) for p,f in inputs.items()};posts=messages(candidate)
    canonical=json.loads((ROOT/'lab/bbs/editor-recipes.json').read_text())['enigma_unsaved']['keyboard_input']
    prefix=canonical[:canonical.index('M enter')].replace('n p6000 n p3000 enter','n p6000 enter')
    cycle='d p1200 a p800 enter p1000 p8000 enter p1200 n p1000 '
    keys=prefix+('c-y F enter p1400 S enter p1400 P C P L U S space P R O B E enter p1600 down enter p1400 '+
        cycle+cycle+'q p1000 down down enter p1400 '+cycle)
    assert len('ADDKEY p1000 '+keys+' p2000 a-x')<500
    observed=[];snapshots=[];finished=asyncio.Event()
    class Observer(ObservedModem):
        def __init__(self,*a,**kw):super().__init__(*a,**kw);observed.append(self)
    original_modem=test_dos.Modem;original_fixture=test_dos.modem_fixture;original_sampler=test_dos.SAMPLER
    if args.observe_labels:
        from zmodem_label_watch import SAMPLER
        test_dos.SAMPLER=SAMPLER
    def settings(**kwargs):
        data=bytearray(original_fixture(**kwargs));data[0x42c:0x42e]=b'\x01\0';path=b'D:\\RECV\\\0';data[0x31c:0x31c+len(path)]=path;return bytes(data)
    async def watch():
        seen=set()
        while True:
            if observed:
                stream=bytes(observed[0].display)
                for h in scan(stream):
                    if h['type']==8 and stream[h['end']:h['end']+2]==b'OO' and h['offset'] not in seen:
                        seen.add(h['offset']);snapshots.append(dict(finish_offset=h['offset'],files=file_state(target)))
            if finished.is_set():return
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
    (out/'finish-file-snapshots.json').write_text(json.dumps(snapshots,indent=2)+'\n')
    harness=json.loads((out/'result.json').read_text());errors=[];transactions=[]
    try:transactions=audit(stream,opposite,modem.trace,names,payloads)
    except (AssertionError,ValueError,UnicodeError) as e:errors.append(str(e))
    boundary=json.loads((out/'server-log-start.json').read_text());assert log.stat().st_ino==boundary['inode']
    with log.open('rb') as f:f.seek(boundary['byte_offset']);rows=[json.loads(l) for l in f if l.strip()]
    sessions={r['sessionId'] for r in rows if r.get('msg')=='User "loclab" successfully logged in'}
    own=[r for r in rows if r.get('sessionId') in sessions]
    (out/'server-session.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in own))
    executions=[i for i,r in enumerate(own) if r.get('msg')=='Executing external protocol']
    exits=[i for i,r in enumerate(own) if r.get('msg')=='Process exited' and r.get('exitCode')==0]
    ordered=len(executions)==len(exits)==3 and all(executions[i]<exits[i] and (i==2 or exits[i]<executions[i+1]) for i in range(3))
    a,b=map(alias,names)
    checks=dict(DOS_harness=code==0 and harness['passed'],inputs_unchanged=before=={p:sha(f) for p,f in inputs.items()},
        unique_authenticated_session=len(sessions)==1,three_protocol_processes_in_order=ordered,
        no_post_saved=posts==messages(candidate) and not any('posted message to' in r.get('msg','') for r in own),
        receive_skip_receive=len(transactions)==3 and [t['kind'] for t in transactions]==['received','skipped-existing','received'],
        file_A_exact=(target/a).is_file() and (target/a).read_bytes()==payloads[names[0]],
        file_B_exact=(target/b).is_file() and (target/b).read_bytes()==payloads[names[1]],
        only_expected_files={p.name for p in target.iterdir()}=={a,b},
        finish_snapshots=len(snapshots)==3,
        existing_alias_unchanged=len(snapshots)==3 and snapshots[0]['files'].get(a)==snapshots[1]['files'].get(a)==snapshots[2]['files'].get(a),
        no_stage_after_each_finish=all('PCRX.$$$' not in s['files'] for s in snapshots))
    labels=[]
    if args.observe_labels:
        raw=(out/'LABELS.BIN').read_bytes();assert len(raw)==2566
        magic,count,ticks=struct.unpack_from('<3H',raw);assert magic==0x4e5a and 0<count<=16 and ticks
        frames=[raw[6+i*160:6+(i+1)*160] for i in range(count)]
        wanted=[]
        for wire,skip in [(names[0],False),(names[0],True),(names[1],False)]:
            text=('Remote: '+wire.ljust(46)+('  Skip: ' if skip else '  Save: ')+alias(wire).ljust(12)).ljust(80).encode()
            wanted.append(b''.join(bytes((c,0x1f)) for c in text))
        at=0
        for frame in frames:
            if at<3 and frame==wanted[at]:at+=1
        checks['actual_DOS_save_skip_save_labels']=at==3
        labels=[f[::2].decode('cp437') for f in frames]
    result=dict(passed=all(checks.values()) and not errors,checks=checks,errors=errors,transactions=transactions,
        terminal_sha256=sha(binary),input_hashes=before,snapshots=snapshots,wire_names=names,local_names=[a,b],
        runner_sha256=sha(Path(__file__)),observed_labels=labels,source_modules=fixture['source_modules'],
        scope='One actual DOS/ENiGMA connection: receive long-name ZIP A, explicitly ZSKIP existing alias A, then receive ZIP B. Passive CRC/data/receiver-control/ZFIN-OO and NFO input-response audits; per-finish inode/mtime/ctime/hash snapshots, checked real DOS storage and restored hardware. Isolated staged server and modeled19200/HARD modem; no live/physical claim.')
    (out/'repeat-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'],checks=checks,errors=errors),indent=2))
    return 0 if result['passed'] else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--label',required=True);p.add_argument('--observe-labels',action='store_true')
    a=p.parse_args();raise SystemExit(asyncio.run(run(a)))
