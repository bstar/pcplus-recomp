#!/usr/bin/env python3
"""Owned upload route: binary+empty ZMODEM batch, stored metadata and NFO return."""
import argparse,asyncio,contextlib,json,re,shutil,subprocess,sys,time
from pathlib import Path
import test_dos
from test_transfer_dos import ObservedModem,timestamp,offset_after
from audit_zmodem import scan,packet,metadata as wire_metadata,audit_batch,audit_controls
from check_enigma_upload_audit import unknown_times,canceled_prefix
from enigma_upload_watch import SAMPLER,events as form_events
from enigma_key_stream_fixture import ROOT,PORT,owned,verify_running,pid
from enigma_notes_dos import sha,messages
from enigma_script_login import source as login_source


def metadata(candidate,names):
    code=r'''const root=process.argv[1];process.chdir(root);
const common=require(root+'/core/oputil/oputil_common');
common.initConfigAndDatabases(e=>{if(e)throw e;const F=require(root+'/core/file_entry');
const names=JSON.parse(process.argv[2]);const result=[];
function next(){const name=names.shift();if(!name){console.log(JSON.stringify(result));return process.exit(0);}
F.findByFileNameWildcard(name,(e,entries)=>{if(e&&e.code!==-33002)throw e;
result.push({name,entries:(entries||[]).map(f=>({fileId:f.fileId,fileName:f.fileName,areaTag:f.areaTag,storageTag:f.storageTag,filePath:f.filePath,fileSha256:f.fileSha256,meta:f.meta,desc:f.desc}))});next();});}next();});'''
    return json.loads(subprocess.check_output(['node','-e',code,str(candidate),json.dumps(names)],cwd=candidate,text=True))


async def run(args):
    assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    assert 1<=args.upload_bytes<=65539
    candidate=owned(args.candidate);log=verify_running(candidate)
    cancel_first=getattr(args,'cancel_first',False)
    cleanup_error=getattr(args,'cleanup_error',False)
    assert not cleanup_error or cancel_first
    sampler=SAMPLER;decode_forms=form_events;temporary=None
    if cancel_first:
        assert args.upload_bytes>=32768
        from enigma_upload_cancel_watch import SAMPLER as sampler,events as decode_forms
        temporary=candidate/'runtime-tmp'
        assert temporary.is_dir() and not temporary.is_symlink()
        environment=(Path('/proc')/str(pid(candidate))/'environ').read_bytes().split(b'\0')
        assert b'TMPDIR='+str(temporary).encode() in environment,'Start the owned fixture with --private-tmp'
        assert not any(p.is_file() for p in temporary.rglob('*')),'Preserve earlier temporary files; use a fresh fixture'
        if cleanup_error:
            assert b'PCPLUS_ENIGMA_FAULT_LOG='+str(candidate/'cleanup-fault-events.jsonl').encode() in environment
            assert not (candidate/'cleanup-fault-events.jsonl').exists()
    fixture=json.loads((candidate/'search-instance.json').read_text());assert fixture['upload_fixture']
    inputs={p:candidate/p for p in [*fixture['fixture_inputs'],*fixture['source_modules']]}
    for p,h in {**fixture['fixture_inputs'],**fixture['source_modules']}.items():assert sha(inputs[p])==h,p
    out=ROOT/'build/bbs-lab/results/enigma'/args.label;out.mkdir(parents=True,exist_ok=False)
    send=out/'SEND';send.mkdir();stage=out/'program';stage.mkdir()
    expected={'PCUP01.BIN':bytes((i*73+(i>>8)*19)&255 for i in range(args.upload_bytes)),'EMPTY.BIN':b''}
    assert not any(row['entries'] for row in metadata(candidate,list(expected))),'Use a fresh owned fixture; no upload replacement'
    for name,data in expected.items():(send/name).write_bytes(data)
    stats={p.name:(p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns,sha(p)) for p in send.iterdir()}
    for rel in ('terminal/TERMINAL.EXE','aspect-runner/ASPECT.EXE','aspect-compiler-dos/ASPCOMP.EXE'):
        p=ROOT/'build'/rel;shutil.copyfile(p,stage/p.name);inputs[rel]=p;inputs['staged/'+p.name]=stage/p.name
    script=login_source();(stage/'LOGON.ASP').write_bytes(script.replace('\n','\r\n').encode('ascii'))
    inputs.update(runner=Path(__file__),login=stage/'LOGON.ASP',harness=Path(test_dos.__file__),
        observer=ROOT/'lab/bbs/test_transfer_dos.py',auditor=ROOT/'lab/bbs/audit_zmodem.py',
        time_auditor=ROOT/'lab/bbs/check_enigma_upload_audit.py',form_observer=ROOT/'lab/bbs/enigma_upload_watch.py',
        observer_base=ROOT/'lab/bbs/zmodem_label_watch.py')
    if cancel_first:inputs.update(cancel_observer=ROOT/'lab/bbs/enigma_upload_cancel_watch.py',fixture_owner=ROOT/'lab/bbs/enigma_key_stream_fixture.py')
    if cleanup_error:inputs['fault_preload']=ROOT/'lab/bbs/patches/enigma-transfer-owner/fault-once.js'
    before={p:sha(f) for p,f in inputs.items()};posts=messages(candidate)
    upload='U enter p1600 tab tab tab enter p1600 enter p1000 '
    sender='a-s p300 f2 f2 D : \\ S E N D \\ '
    nfo='c-y S enter p1600 P C P L U S space P R O B E space 0 1 enter p1800 enter p1500 n p1500 '
    keys='p85000 c-y F enter p1600 '+upload+sender
    if cancel_first:
        keys+='P C U P 0 1 . B I N enter p22000 escape p2000 '+nfo+'escape p1000 escape p1000 escape p1000 c-y '+upload+sender.replace('f2 f2 ','')
    keys+='* . B I N enter '+('p150000 ' if args.upload_bytes>32768 else 'p105000 ' if args.upload_bytes>8192 else 'p65000 ')+'p6000 '+nfo
    assert len('ADDKEY p1000 '+keys+' p2000 a-x')<500
    observed=[];snapshots=[];finished=asyncio.Event()
    class Observer(ObservedModem):
        def __init__(self,*a,**kw):super().__init__(*a,**kw);observed.append(self)
    original_modem=test_dos.Modem;original_directory=test_dos.directory_image;original_sampler=test_dos.SAMPLER
    def directory(**kwargs):
        data=bytearray(original_directory(**kwargs));at=250+(kwargs['entry']-1)*114
        data[at+52:at+61]=b'LOGON\0\0\0\0';return bytes(data)
    async def watch_cancel():
        while not finished.is_set():
            if observed and not snapshots and b'\x18'*8+b'\x08'*10 in observed[0].keyboard and b'NFO | lines 1-15/24' in observed[0].display:
                entries=await asyncio.to_thread(metadata,candidate,list(expected))
                snapshots.append(dict(entries=entries,installed=[p.name for p in (candidate/'file_base/pcplus_upload').iterdir()],
                    temporary_files=[str(p.relative_to(temporary)) for p in temporary.rglob('*') if p.is_file()],
                    source_files_unchanged=stats=={p.name:(p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns,sha(p)) for p in send.iterdir()}))
            await asyncio.sleep(.05)
    task=asyncio.create_task(watch_cancel()) if cancel_first else None
    test_dos.Modem=Observer;test_dos.directory_image=directory;test_dos.SAMPLER=sampler
    options=argparse.Namespace(name='enigma',label=args.label,port=PORT,com=2,baud=19200,flow='HARD',packet_delay_ms=0,
        dial_fixture=True,directory_fixture=True,directory_browser=False,entry=3,binary=stage/'TERMINAL.EXE',config_fixture=False,
        keymap_fixture=ROOT/'build/keyboard-profiles/NETWORK.KBD',server_log=log,keys=keys,wait=2,timeout=430 if cancel_first else 330)
    started=time.time_ns()
    try:
        with (out/'harness.log').open('w') as capture,contextlib.redirect_stdout(capture):code=await test_dos.run(options)
    finally:
        test_dos.Modem=original_modem;test_dos.directory_image=original_directory;test_dos.SAMPLER=original_sampler
        finished.set()
        if task:await task
    ended=time.time_ns();date_bounds=[started-2_000_000_000,ended+2_000_000_000]
    assert len(observed)==1
    modem=observed[0];stream=bytes(modem.keyboard);opposite=bytes(modem.display)
    (out/'trace.json').write_text(json.dumps(modem.trace,indent=2)+'\n')
    harness=json.loads((out/'result.json').read_text());errors=[];protocol={}
    installed=metadata(candidate,list(expected));(out/'server-upload-metadata.json').write_text(json.dumps(installed,indent=2)+'\n')
    metadata_checks={};date_checks={}
    for row in installed:
        name=row['name'];entries=row['entries'];valid=len(entries)==1
        if valid:
            e=entries[0];p=Path(e['filePath']);valid=(e['fileName']==name and e['areaTag']==e['storageTag']=='pcplus_upload' and
                p.resolve().parent==candidate/'file_base/pcplus_upload' and p.is_file() and p.read_bytes()==expected[name] and
                e['meta'].get('byte_size')==len(expected[name]) and e['fileSha256']==sha(send/name) and e['meta'].get('upload_by_username')=='loclab')
        metadata_checks[name]=valid
        date_checks[name]=valid and date_bounds[0]<=Path(entries[0]['filePath']).stat().st_mtime_ns<=date_bounds[1]
    sys.path.insert(0,str(ROOT/'src/aspect'));from compiler import compile_source
    checks=dict(DOS_harness=code==0 and harness['passed'],inputs_unchanged=before=={p:sha(f) for p,f in inputs.items()},
        source_files_unchanged=stats=={p.name:(p.stat().st_ino,p.stat().st_size,p.stat().st_mtime_ns,sha(p)) for p in send.iterdir()},
        no_post_saved=posts==messages(candidate),all_server_files_and_metadata=all(metadata_checks.values()),
        only_expected_installed_files={p.name for p in (candidate/'file_base/pcplus_upload').iterdir()}==set(expected),
        DOS_compiler_exact=(stage/'LOGON.ASX').is_file() and(stage/'LOGON.ASX').read_bytes()==compile_source(script),
        script_login_trace=(stage/'LOGIN.LOG').is_file() and(stage/'LOGIN.LOG').read_bytes()==b'STARTAUTHREADY')
    checks['received_creation_dates_current']=all(date_checks.values())
    if cancel_first:
        (out/'cancel-upload-snapshots.json').write_text(json.dumps(snapshots,indent=2)+'\n')
        checks['canceled_upload_not_installed']=len(snapshots)==1 and not snapshots[0]['installed'] and all(not r['entries'] for r in snapshots[0]['entries'])
        if not cleanup_error:checks['canceled_temporary_data_removed']=len(snapshots)==1 and not snapshots[0]['temporary_files']
        else:checks['cleanup_failure_retains_partial_for_retry']=len(snapshots)==1 and bool(snapshots[0]['temporary_files'])
        checks['source_files_unchanged_after_cancel']=len(snapshots)==1 and snapshots[0]['source_files_unchanged']
    forms=[]
    try:
        forms=decode_forms((out/'LABELS.BIN').read_bytes())
        (out/'upload-form-events.json').write_text(json.dumps(forms,indent=2)+'\n')
        checks['observed_two_complete_form_key_sequences']=True
    except (AssertionError,OSError,ValueError):checks['observed_two_complete_form_key_sequences']=False
    try:
        unknown_times(stream,expected);checks['explicit_unknown_time_on_wire']=True
    except (AssertionError,ValueError,UnicodeError):checks['explicit_unknown_time_on_wire']=False
    checks['observer_keys_delivered_exactly']=False
    canceled={};minimum=0
    if cancel_first:
        try:
            canceled=canceled_prefix(stream,opposite,modem.trace,expected);minimum=canceled['first_search']+2
            checks['cancel_after_valid_data_and_ACK']=True
        except (AssertionError,ValueError,StopIteration):checks['cancel_after_valid_data_and_ACK']=False
    try:
        protocol=audit_batch(stream,expected,minimum);end_time=timestamp(modem.trace,'dos',protocol['end']-1)
        if cancel_first:
            first_when=timestamp(modem.trace,'dos',canceled['first_search']);first_reply=offset_after(modem.trace,'bbs',first_when)
            retry_when=timestamp(modem.trace,'dos',protocol['start']);retry_reply=offset_after(modem.trace,'bbs',retry_when)
            assert b'NFO | lines 1-15/24' in opposite[first_reply:retry_reply] and b'PCPLUS NFO LINE 01 : synthetic game 01' in opposite[first_reply:retry_reply]
            checks['NFO_between_cancel_and_retry']=True
        post_at=stream.index(b'S\r',offset_after(modem.trace,'dos',end_time));when=timestamp(modem.trace,'dos',post_at)
        keys_expected=bytes(13 if e['key']=='Enter' else 9 for e in (forms[1:] if cancel_first else forms))
        assert bytes(c for c in stream[protocol['end']:post_at] if c in (9,13))==keys_expected,'Observed form keys did not reach the BBS exactly'
        checks['observer_keys_delivered_exactly']=True
        protocol['controls']=audit_controls(protocol,opposite,modem.trace,'dos',when,False)
        start=offset_after(modem.trace,'bbs',when);assert start is not None
        tail=opposite[start:]
        assert b'PCPLUS PROBE 01 (1991).ZIP' in tail and b'NFO | lines 1-15/24' in tail and b'PCPLUS NFO LINE 01 : synthetic game 01' in tail
        for f in protocol['files']:f.pop('source')
        checks['exact_binary_and_empty_batch_then_NFO']=True
    except (AssertionError,ValueError,TypeError,KeyError,StopIteration) as e:
        errors.append(str(e));checks['exact_binary_and_empty_batch_then_NFO']=False
        for f in protocol.get('files',[]):f.pop('source',None)
    boundary=json.loads((out/'server-log-start.json').read_text());assert log.stat().st_ino==boundary['inode']
    rows=[json.loads(l) for l in log.read_bytes()[boundary['byte_offset']:].splitlines() if l.strip()]
    sessions={r['sessionId'] for r in rows if r.get('msg')=='User "loclab" successfully logged in'}
    own=[r for r in rows if r.get('sessionId') in sessions];menus=[r['menuName'] for r in own if r.get('menuName')]
    (out/'server-session.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in own))
    checks['unique_authenticated_session']=len(sessions)==1
    cursor=0;route=True
    for menu in ['fileBaseUploadFiles','fileTransferProtocolSelection','recvFilesFromUser','fileBaseUploadFiles','fileBaseMainMenu','fileBaseSearch','blackFlagZipResults','locGameDetails']:
        try:cursor=menus.index(menu,cursor)+1
        except ValueError:route=False;break
    checks['actual_upload_and_return_route']=route
    if cancel_first:
        exits=[r.get('exitCode') for r in own if r.get('msg')=='Process exited']
        checks['failed_then_successful_protocol_process']=len(exits)==2 and exits[0]!=0 and exits[1]==0
    faults=[]
    if cleanup_error:
        fault_path=candidate/'cleanup-fault-events.jsonl'
        faults=[json.loads(line) for line in fault_path.read_text().splitlines()] if fault_path.exists() else []
        (out/'cleanup-fault-events.json').write_text(json.dumps(faults,indent=2)+'\n')
        checks['one_modeled_cleanup_error']=len(faults)==1 and faults[0].get('code')=='EACCES' and faults[0].get('operation')=='rm' and faults[0].get('injected') is True
        checks['cleanup_error_logged']=len([r for r in own if r.get('msg')=='Upload temporary cleanup failed' and r.get('code')=='EACCES'])==1
        checks['failed_owner_retired_on_retry']=not any(p.is_file() for p in temporary.rglob('*'))
    result=dict(passed=all(checks.values()) and not errors,checks=checks,errors=errors,metadata_checks=metadata_checks,
        protocol=protocol,menus=menus,terminal_sha256=before['terminal/TERMINAL.EXE'],input_hashes=before,
        received_date_bounds_ns=date_bounds,received_dates_current=date_checks,
        cancel_first=cancel_first,canceled_protocol=canceled,cancel_snapshots=snapshots,
        cleanup_error_expected=cleanup_error,filesystem_faults=faults,
        expected={name:dict(bytes=len(data),sha256=sha(send/name)) for name,data in expected.items()},
        scope='One actual DOS/owned ENiGMA session: DOS-built ASPECT login, real upload form/protocol selector, binary and empty ZMODEM batch, official FileEntry API/storage audit, details acceptance and NFO input afterward. Synthetic account/area, modeled19200/HARD UART; no live board or physical modem claim.')
    (out/'upload-checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=result['passed'],checks=checks,metadata_checks=metadata_checks,errors=errors,menus=menus),indent=2))
    return 0 if result['passed'] else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--label',required=True)
    p.add_argument('--upload-bytes',type=int,default=1501,help='Generated binary size1..65539; empty file is always included')
    p.add_argument('--cancel-first',action='store_true',help='Cancel a nonempty upload, open NFO, retry the batch, reopen NFO in the same DOS session')
    p.add_argument('--cleanup-error',action='store_true',help='Require one staged modeled cleanup denial, responsive NFO, and retirement on retry')
    raise SystemExit(asyncio.run(run(p.parse_args())))
