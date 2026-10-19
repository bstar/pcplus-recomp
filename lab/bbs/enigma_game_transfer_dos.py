#!/usr/bin/env python3
"""Characterize the actual custom game-details download, including wire names.

The existing protocol harness assumes DOS83 BIN fixture names. The driver here
changes only that fixture-input boundary to admit a generated archive's real
basename; the production DOS binary, modem and protocol audit stay unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from enigma_key_stream_fixture import ROOT,PORT,owned,verify_running
from enigma_notes_dos import sha,messages


def driver():
    # test_dos also exposes standalone diagnostics on sys.path. Select this
    # laboratory harness explicitly; a same-named standalone test exists.
    sys.path.insert(0,str(ROOT/'lab/bbs'))
    import test_zmodem_dos as probe
    assert Path(probe.__file__).resolve()==ROOT/'lab/bbs/test_zmodem_dos.py'
    def wire_files(values):
        assert len(values)==1
        name,sep,value=values[0].partition('=');path=probe.owned_file(value)
        assert sep and name==path.name and path.is_file()
        assert '/' not in name and '\\' not in name and name.endswith('.ZIP')
        return {name.upper():path}
    probe.parse_files=wire_files
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
        wire_offers=offers,archive=archive,received_files=[p.name for p in (output/'RECV').iterdir()],
        protocol_checks=result.get('checks',{}),protocol_errors=result.get('errors',[]),
        input_hashes=before,runner_sha256=sha(Path(__file__)),
        scope='Actual DOS custom search -> selected long-name ZIP -> game-details D -> ENiGMA ZMODEM. Only the test fixture basename admission differs from the standard BIN-only harness; no wire bytes or protocol replies synthesized. A characterization may retain failure; this is not a compatibility pass.')
    (wrapper/'characterization.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('transfer_passed','inputs_unchanged','no_post_saved','wire_offers','received_files','protocol_errors')},indent=2))
    return 0 if report['inputs_unchanged'] and report['wire_offers'] and report['no_post_saved'] else 1


if __name__=='__main__':
    if sys.argv[1:2]==['--driver']:
        sys.argv.pop(1);raise SystemExit(driver())
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--label',required=True)
    raise SystemExit(main(p.parse_args()))
