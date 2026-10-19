#!/usr/bin/env python3
"""Characterize the actual custom game-details download, including wire names.

The protocol harness assumes DOS83 BIN fixtures and the stock file-list route.
The driver admits the real wire name, checks its independently computed DOS
alias and audits the custom return route. CRC/payload/handshake checks remain.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import types
import zlib

from enigma_key_stream_fixture import ROOT,PORT,owned,verify_running
from enigma_notes_dos import sha,messages


def driver():
    # test_dos also exposes standalone diagnostics on sys.path. Select this
    # laboratory harness explicitly; a same-named standalone test exists.
    sys.path.insert(0,str(ROOT/'lab/bbs'))
    source=ROOT/'lab/bbs/test_zmodem_dos.py';text=source.read_text()
    original="checks['DOS_exact_length_'+name]=(target/name).is_file() and (target/name).read_bytes()==data"
    replacement="checks['DOS_exact_length_'+name]=(target/WIRE_LOCAL_NAMES[name]).is_file() and (target/WIRE_LOCAL_NAMES[name]).read_bytes()==data"
    assert text.count(original)==1;text=text.replace(original,replacement)
    original="{p.name.upper() for p in target.iterdir()}==set(expected)"
    assert text.count(original)==1;text=text.replace(original,"{p.name.upper() for p in target.iterdir()}==set(WIRE_LOCAL_NAMES.values())")
    probe=types.ModuleType('owned_game_protocol_probe');probe.__file__=str(source);probe.WIRE_LOCAL_NAMES={}
    exec(compile(text,str(source),'exec'),probe.__dict__)
    def wire_files(values):
        assert len(values)==1
        name,sep,value=values[0].partition('=');path=probe.owned_file(value)
        assert sep and name==path.name and path.is_file()
        assert '/' not in name and '\\' not in name and name.endswith('.ZIP')
        probe.WIRE_LOCAL_NAMES[name.upper()]=f'{zlib.crc32(name.upper().encode("ascii")):08X}.ZIP'
        return {name.upper():path}
    probe.parse_files=wire_files
    original_audit=probe.audit_enigma_server
    def route_audit(output,mode):
        result=original_audit(output,mode)
        rows=[json.loads(line) for line in (Path(output)/'server-session.jsonl').read_text().splitlines() if line.strip()]
        own=[r for r in rows if r.get('sessionId')==result['session_id']]
        executions=[i for i,r in enumerate(own) if r.get('msg')=='Executing external protocol']
        exits=[i for i,r in enumerate(own) if r.get('msg')=='Process exited' and r.get('exitCode')==0]
        ordered=False
        if len(executions)==len(exits)==1 and executions[0]<exits[0]:
            before=[r.get('menuName') for r in own[:executions[0]]];after=[r.get('menuName') for r in own[exits[0]+1:]]
            try:ordered=before.index('fileBaseSearch')<before.index('blackFlagZipResults')<before.index('locGameDetails')<before.index('fileTransferProtocolSelection') and 'locGameDetails' in after
            except ValueError:pass
        result['checks'].pop('ordered_protocol_return_and_file_list')
        result['checks']['ordered_custom_game_download_return']=ordered
        result['passed']=all(result['checks'].values());result['scope']+=' Custom game search/details route and return replace the stock file-list routing predicate.'
        return result
    probe.audit_enigma_server=route_audit
    return probe.main()


def main(args):
    from audit_zmodem import scan,packet,metadata as wire_metadata
    assert args.label.replace('-','').replace('_','').isalnum()
    candidate=owned(args.candidate);verify_running(candidate)
    fixture=json.loads((candidate/'search-instance.json').read_text());archive=fixture['archives'][1]
    source=candidate/'file_base/pcplus_games'/archive['name']
    assert sha(source)==archive['sha256']
    output=ROOT/'build/bbs-lab/results/enigma'/args.label
    wrapper=output.with_name(args.label+'-wrapper');wrapper.mkdir(parents=True,exist_ok=False)
    inputs={p:candidate/p for p in [*fixture['source_modules'],*fixture['fixture_inputs']]}
    inputs.update({'terminal':ROOT/'build/terminal/TERMINAL.EXE','archive':source,'runner':Path(__file__),
                   'protocol_harness':ROOT/'lab/bbs/test_zmodem_dos.py'})
    before={p:sha(f) for p,f in inputs.items()};posts=messages(candidate)
    canonical=json.loads((ROOT/'lab/bbs/editor-recipes.json').read_text())['enigma_unsaved']['keyboard_input']
    prefix=canonical[:canonical.index('M enter')].replace('n p6000 n p3000 enter','n p6000 enter')
    keys=prefix+('c-y F enter p1600 S enter p1600 P C P L U S space P R O B E space 0 1 enter '
                 'p2000 enter p1600 d p1500 a p1000 enter p1000 p20000 enter p1600 n p1500')
    command=[sys.executable,str(Path(__file__)), '--driver','enigma','--port',str(PORT),
        '--server-instance',str(candidate/'instance.json'),'--label',args.label,'--sha256',before['terminal'],
        '--mode','download','--file',archive['name']+'='+str(source),'--auto-download','--dial-fixture',
        '--keys',keys,'--start-input-hex',b'd'.hex(),'--post-input-hex',b'n'.hex(),
        '--post-menu','NFO | lines','--timeout','190']
    (wrapper/'command.json').write_text(json.dumps(command,indent=2)+'\n')
    with (wrapper/'harness.log').open('w') as log:code=subprocess.call(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    result=json.loads((output/'result.json').read_text())
    stream=(output/'display.bin').read_bytes() if (output/'display.bin').exists() else b''
    offers=[]
    for header in scan(stream):
        if header['type']!=4:continue
        try:
            data=packet(stream,header['end'],header['format']);name,size=wire_metadata(data['payload'])
            offers.append(dict(name=name,size=size,header_offset=header['offset'],data_crc_verified=True))
        except (AssertionError,ValueError,UnicodeError):continue
    report=dict(transfer_passed=result['passed'],harness_exit=code,terminal_sha256=before['terminal'],
        inputs_unchanged=before=={p:sha(f) for p,f in inputs.items()},no_post_saved=posts==messages(candidate),
        wire_offers=offers,archive=archive,expected_local_name=f'{zlib.crc32(archive["name"].upper().encode("ascii")):08X}.ZIP',received_files=[p.name for p in (output/'RECV').iterdir()],
        protocol_checks=result.get('checks',{}),protocol_errors=result.get('errors',[]),
        input_hashes=before,runner_sha256=sha(Path(__file__)),
        scope='Actual DOS custom search -> selected long-name ZIP -> game-details D -> ENiGMA ZMODEM. Fixture wire/local filename and custom menu-route adapters retain the original CRC/payload/handshake/storage/hardware checks. No wire bytes or protocol replies synthesized; compatibility passes only when every protocol check passes.')
    (wrapper/'characterization.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('transfer_passed','inputs_unchanged','no_post_saved','wire_offers','received_files','protocol_errors')},indent=2))
    return 0 if report['inputs_unchanged'] and report['wire_offers'] and report['no_post_saved'] else 1


if __name__=='__main__':
    if sys.argv[1:2]==['--driver']:
        sys.argv.pop(1);raise SystemExit(driver())
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--label',required=True)
    raise SystemExit(main(p.parse_args()))
