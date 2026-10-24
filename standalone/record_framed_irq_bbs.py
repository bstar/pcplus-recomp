#!/usr/bin/env python3
"""Verify immediate stock/framed ENiGMA comparisons with current IRQ products."""
import argparse
import json
from pathlib import Path
import socket
import sqlite3

from build_guarded_helper import ROOT, LOOKUP
from record_hook_bbs import verify_case, sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--stock-label',required=True)
    p.add_argument('--accept-label',required=True)
    p.add_argument('--reject-label',required=True)
    p.add_argument('--counterexamples',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    candidate=args.candidate.resolve();assert candidate.is_relative_to(ROOT/'build')
    terminal=ROOT/'build'/(LOOKUP+'-custom-irq')/'TERMINAL.EXE'
    runner=ROOT/'build/aspect-register-parent-custom-irq/ASPECT.EXE'
    stock=ROOT/'build/bbs-lab/enigma/source'
    replay_path=candidate.parent/'report.json'
    replay=json.loads(replay_path.read_text())
    instance=json.loads((candidate/'instance.json').read_text())
    assert replay['passed'] and replay['stock_client_unchanged']
    assert instance['candidate']==str(candidate) and instance['address']=='127.0.0.1' and instance['port']==23234
    assert replay['upstream_revision']==instance['upstream_revision']
    assert replay['stock_client_sha256']==sha(stock/'core/client.js')==instance['stock_client_sha256']
    assert replay['candidate_client_sha256']==sha(candidate/'core/client.js')==instance['client_sha256']
    assert replay['candidate_key_stream_sha256']==sha(candidate/'core/key_stream.js')==instance['key_stream_sha256']
    assert sha(candidate/'core/multi_line_edit_text_view.js')==sha(stock/'core/multi_line_edit_text_view.js')
    assert sha(candidate/'config/config.hjson')==instance['config_sha256']
    assert replay['nix_lock_sha256']==sha(ROOT/'nix/flake.lock')
    assert replay['upstream_package_lock_sha256']==sha(stock/'package-lock.json')
    for name,test in ((test['name'],test)for test in replay['tests']):
        assert test['exit_code']==0 and sha(replay_path.parent/(name+'.log'))==test['log_sha256']
    tests={test['name']:test['result']for test in replay['tests']if'result'in test}
    assert tests['stock-counterexample']['demonstrated_fragmentation_failures']==84
    assert tests['stock-counterexample']['editor_fragmentation_failures']==9
    assert tests['candidate-client-editor']['demonstrated_fragmentation_failures']==0
    assert tests['candidate-client-editor']['editor_fragmentation_failures']==0
    sources={};artifacts={};rows=[]
    def merge(mapping):
        for name,digest in mapping.items():
            assert sha(ROOT/name)==digest and(name not in sources or sources[name]==digest),name
            sources[name]=digest
    for product in (terminal,runner):
        m=json.loads((product.parent/'manifest.json').read_text())
        assert m['experimental_custom_irq'] and sha(product)==m['binary_sha256']
        merge(m['sources'])
    for name,digest in replay['inputs'].items():merge({'lab/bbs/patches/enigma-key-stream/'+name:digest})
    specs=[(args.stock_label,'accept',7,None),(args.accept_label,'accept',7,candidate),
           (args.reject_label,'reject',5,candidate)]
    for label,mode,irq,selected in specs:
        row=verify_case('enigma',label,mode,0,terminal,runner,immediate=selected is None,
                        expected_irq=irq,server_instance=selected)
        assert row['source_compilation'] and row['editor_passed']==(selected is not None)
        if selected is None:
            assert not row['editor_checks']['home_moves_before_marker'] and not row['editor_checks']['insert_toggled_overtype']
        else:
            assert all(row['editor_checks'].values())
        merge(row.pop('sources'));artifacts.update(row.pop('artifacts'))
        rows.append(row)
    # The main comparison has identical executables, bytecode, key recipe and
    # input key profile. Endpoint/server selection is explicit, not buffering.
    stages=[ROOT/'build/bbs-lab/script-login'/label for label,_,_,_ in specs]
    outputs=[ROOT/'build/bbs-lab/results/enigma'/label for label,_,_,_ in specs]
    first,second=[json.loads((path/'result.json').read_text())for path in outputs[:2]]
    for key in ('keyboard','keyboard_input','cpu','modem_packet_delay_ms','keyboard_profile'):
        assert first[key]==second[key],key
    assert first['serial']==second['serial'] and first['modem_packet_delay_ms']==0
    for leaf in ('TERMINAL.EXE','ASPECT.EXE','ASPCOMP.EXE','LOGON.ASP','LOGON.ASX','SCRIPT.COM','ACTIONS.KEY','APPLYCH.EXE'):
        assert sha(stages[0]/leaf)==sha(stages[1]/leaf),leaf
    assert (outputs[0]/'TEST.PRM').read_bytes()==(outputs[1]/'TEST.PRM').read_bytes()
    assert (outputs[0]/'BOARD.KBD').read_bytes()==(outputs[1]/'BOARD.KBD').read_bytes()
    for directory in ('db','logs','drop','file_base'):
        path=candidate/directory
        assert not path.is_symlink() and path.resolve().is_relative_to(candidate)
    with sqlite3.connect(f'file:{candidate/"db/user.sqlite3"}?mode=ro',uri=True)as db:
        assert {row[0]for row in db.execute('SELECT user_name FROM user')}=={'locadmin','loclab'}
    config=json.loads((candidate/'config/config.hjson').read_text())
    assert str(stock)not in json.dumps(config) and'paths'not in config
    assert config['loginServers']['telnet']['address']=='127.0.0.1' and config['loginServers']['telnet']['port']==23234
    # Final record is published after stopping only this owned experiment.
    import sys
    sys.path.insert(0,str(ROOT/'lab/bbs'))
    from enigma_key_stream_fixture import pid
    assert pid(candidate)is None
    with socket.socket()as check:check.bind(('127.0.0.1',23234))
    for path in [candidate/'instance.json',candidate/'config/config.hjson',replay_path,
                 *[replay_path.parent/(test['name']+'.log')for test in replay['tests']]]:
        artifacts[str(path.relative_to(ROOT))]=sha(path)
    for name in ('standalone/record_framed_irq_bbs.py','standalone/record_hook_bbs.py','lab/bbs/enigma_key_stream_fixture.py','nix/flake.lock'):
        merge({name:sha(ROOT/name)})
    counter_path=args.counterexamples.resolve();counter=json.loads(counter_path.read_text())
    assert counter['passed']and counter['files_unchanged']and len(counter['cases'])==4
    assert all(case['rejected']for case in counter['cases'])
    assert counter['checker_sha256']==sha(ROOT/'standalone/check_framed_irq_evidence.py')
    assert counter['verifier_sha256']==sha(ROOT/'standalone/record_hook_bbs.py')
    for name,digest in counter['inputs'].items():assert sha(ROOT/name)==digest,name
    merge({'standalone/check_framed_irq_evidence.py':counter['checker_sha256']})
    result=dict(outcomes_verified=True,compatibility_complete=False,terminal_sha256=sha(terminal),runner_sha256=sha(runner),
                cases=rows,sources=sources,artifacts=artifacts,decoder_replay=replay,
                exact_comparison=['executables','ASP/ASX','KEY','helper','compact observer','PRM','keyboard schedule','serial settings','zero buffering'],
                isolated_server_stopped=True,stock_server_changed=False,
                counterexamples=counter,counterexamples_sha256=sha(counter_path),
                scope='Current DOS8086 custom IRQ product: stock immediate Home/Insert failure versus isolated framed '
                'server pass with identical client inputs; IRQ5 failed-helper retention/retry also passes. Fresh decoder '
                'tests and source hashes bound. Dependencies reused, not clean-built. No live LAN deployment, arbitrary '
                'network latency, transfers, physical hardware or full native application acceptance.')
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS framed IRQ comparison: stock failure and two immediate candidate passes; isolated server stopped')


if __name__=='__main__':main()
