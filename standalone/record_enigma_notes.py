#!/usr/bin/env python3
"""Bind actual owned-module replay and DOS baseline/candidate navigation."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()


def main(server):
    server=server.resolve();stage='build/bbs-lab/owned-enigma-notes-01'
    core_hash='d66207f46af13ae4acb0ac430b1d0f2572a03722c79f4bcb7125dcd01e98e788'
    module='mods/loc_game_details/loc_game_details.js';helper='mods/black_flag_files/helpers.js'
    modules={p:hashlib.sha256((server/p).read_bytes()).hexdigest() for p in (module,helper)}
    assert hashlib.sha256((server/'core/client.js').read_bytes()).hexdigest()==core_hash
    unit={}
    for mode,leaf in [('baseline','module-baseline.json'),('framed','module-framed.json')]:
        path=stage+'/'+leaf;data=read(path)
        assert data['passed'] and data['fixed']==(mode=='framed') and data['checks']==180
        assert data['checker_sha256']==sha('lab/bbs/patches/enigma-key-stream/check_game_details.js')
        assert data['module_sha256']==modules[module] and data['helper_sha256']==modules[helper]
        assert data['fragmented_differences']==(164 if mode=='baseline' else 0)
        assert data['unexpected_leaves']==(120 if mode=='baseline' else 0)
        if mode=='baseline':assert data['client_sha256']==core_hash
        unit[mode]=dict(path=path,sha256=sha(path),checks=data['checks'],
            fragmented_differences=data['fragmented_differences'],unexpected_leaves=data['unexpected_leaves'],
            client_sha256=data['client_sha256'],node=data['node'],scope=data['scope'])
    assert read(stage+'/module-baseline.json')['unfragmented']==read(stage+'/module-framed.json')['unfragmented']
    prepared=read(stage+'/report.json')
    assert prepared['passed'] and prepared['stock_client_unchanged']
    assert prepared['candidate_client_sha256']==unit['framed']['client_sha256']
    assert prepared['nix_lock_sha256']==sha('nix/flake.lock')
    assert unit['baseline']['node']==unit['framed']['node']==prepared['node']
    terminal=sha('build/terminal/TERMINAL.EXE');dos={}
    for mode,label in [('baseline','owned-notes-baseline-01'),('framed','owned-notes-framed-02')]:
        path=f'build/bbs-lab/results/enigma/{label}/notes-checks.json';data=read(path)
        assert data['decoder']==mode and data['source_modules']==modules
        assert data['terminal_sha256']==terminal
        assert data['runner_sha256']==sha('lab/bbs/enigma_notes_dos.py')
        assert data['fixture_sha256']==sha('lab/bbs/enigma_notes_fixture.py')
        assert data['input_hashes']['source_board/core/client.js']==core_hash
        assert data['input_hashes']['candidate/core/client.js']==unit[mode]['client_sha256']
        checks=data['checks']
        for key in ['DOS_harness','unique_authenticated_session','exact_owned_module','inputs_unchanged','no_post_saved','diz_page','nfo_page','actual_profile_key_bytes']:
            assert checks[key],(mode,key)
        if mode=='framed':assert data['passed'] and all(checks.values()) and data['pages']==data['expected_pages']
        else:assert not data['passed'] and not checks['exact_navigation'] and not checks['bottom_content'] and data['pages']==[[1,15,24],[1,15,24]]
        dos[mode]=dict(path=path,sha256=sha(path),navigation_passed=data['passed'],checks=checks,
            observed_pages=data['pages'],expected_pages=data['expected_pages'],modem_packet_delay_ms=data['modem_packet_delay_ms'],scope=data['scope'])
    proof_path='docs/validation/application-components-source-build.json';proof=read(proof_path)
    assert proof['passed'] and proof['outputs']['terminal/TERMINAL.EXE']['sha256']==terminal
    result=dict(passed=True,defect_reproduced=True,isolated_fix_verified=True,live_server_modified=False,
        terminal_sha256=terminal,owned_upstream_revision=prepared['upstream_revision'],source_modules=modules,
        unit=unit,DOS=dos,node=prepared['node'],nix_lock_sha256=sha('nix/flake.lock'),
        source_build_proof=dict(path=proof_path,sha256=sha(proof_path),outputs=proof['output_count']),
        recorder_sha256=sha(Path(__file__).relative_to(ROOT)),whole_application_gates_closed=[],
        retained_prerequisite_failure=dict(label='owned-notes-framed-01',reason='Explicit server-log guard rejected an unsupported harness owner before connecting; corrected runner uses enigma and a fresh label.'),
        limitations=['Exact owned details/helper source with generated DIZ/NFO and a dedicated test-menu route; live custom index/search routing and its real catalog remain unverified after patching.',
          'The staged decoder remains uninstalled on the live board; retained live failures are not superseded by these isolated passes.',
          'Incomplete key deadline remains100ms; physical RS-232 Wi-Fi modem latency/flow control and other BBS implementations need separate testing.',
          'Game-details HTTP/browser/queue/transfer actions are outside this navigation fixture; editor/ZMODEM handoffs have separate records.',
          'Pinned Nix shells reuse existing node_modules; this is not a fresh dependency-reproducibility proof.'])
    (ROOT/'docs/validation/enigma-notes.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Recorded exact owned notes module:180 Client checks per decoder and DOS before/after navigation; live board unchanged')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--server-root',type=Path,required=True)
    main(p.parse_args().server_root)
