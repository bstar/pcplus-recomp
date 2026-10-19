#!/usr/bin/env python3
"""Record the frozen WHEN runtime composition, without changing older proofs."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = 'dacbd777fbd5afaf441ad46ec559be2b95c53fd5ba9c1219ebfb865cd48e66ae'
CHILD = '0f00aa3e44da029ca7727f38f1e1af6db08a84a712cb30b03e990219cf3c60ef'


def main():
    sources, evidence, reports, manifests = {}, {}, {}, {}

    def sha(path):
        return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()

    def bind(path, digest):
        assert sha(path) == digest, ('changed source', path)
        assert path not in sources or sources[path] == digest, path
        sources[path] = digest

    def read(path):
        evidence[path] = sha(path)
        return json.loads((ROOT/path).read_text())

    def passed(path):
        value = read(path)
        assert value['passed'] and value.get('original_inputs', []) == [], path
        assert all(value.get('checks', {}).values()), path
        if isinstance(value.get('cases'), list):
            for case in value['cases']:
                assert case.get('passed', True) and all(case.get('checks', {}).values()), (path, case)
        return value

    def report(path, checker, folder='aspect-runner', count=None):
        value = passed(path)
        assert value['manifest_sha256'] == evidence['build/'+folder+'/manifest.json'], path
        assert value['binary_sha256'] == manifests[folder]['binary_sha256'], path
        bind(checker, value.get('checker_sha256', value.get('check_sha256')))
        if count is not None:
            assert len(value['cases']) == count, path
        reports[path] = dict(passed=True, cases=count, scope=value.get('scope', value.get('limitations')))
        return value

    for folder, leaf, identity in [('terminal','TERMINAL.EXE',PARENT),
                                   ('aspect-runner','ASPECT.EXE',CHILD),
                                   ('aspect-runtime','EXECUTE.EXE',None)]:
        value = read('build/'+folder+'/manifest.json')
        assert value.get('original_inputs', []) == [], folder
        for path,digest in value['sources'].items():
            bind(path,digest)
        assert sha('build/'+folder+'/'+leaf) == value['binary_sha256'], folder
        assert identity is None or value['binary_sha256'] == identity, folder
        manifests[folder] = value

    runtime = report('build/aspect-runtime/checks.json','standalone/check_aspect_runtime.py','aspect-runtime')
    assert runtime['DOS_summary'] == 'ASPECT_RUNTIME 825 cases 18298 checks 0 failures'
    native = manifests['aspect-runtime']
    assert native['fixture_count'] == runtime['fixture_count'] == 402
    assert len(native['supported_slots']) == 66 and runtime['unsupported_slot_cases'] == 149
    assert native['diagnostic_case_count'] == 825
    assert native['SET_family']['supported_subcommands'] == {'56':'WHENCASE'}
    assert native['SET_family']['unsupported_subcommands_tested'] == 255
    assert native['SET_family']['truncated_or_invalid_boolean_cases'] == 4
    assert sha('build/aspect-runtime/CASES.DAT') == runtime['fixture_data_sha256']
    reports['build/aspect-runtime/checks.json'].update(cases=825,checks=18298,
        authored_fixtures=402,supported_slots=66,unsupported_opcodes=149,
        unsupported_SET_subcommands=255,invalid_WHENCASE=4)

    overrides_path = 'standalone/fixtures/aspect_receive_runtime_overrides.json'
    overrides = read(overrides_path)
    assert len(overrides['overrides']) == 9
    assert native['composed_receive_overrides'] == overrides
    bind(overrides['component_fixture'],overrides['component_fixture_sha256'])
    bind(overrides_path,sha(overrides_path))
    bind('docs/ASPECT_WHEN_SERVICE_TIMING.md',sha('docs/ASPECT_WHEN_SERVICE_TIMING.md'))

    cli = report('build/aspect-runner/checks.json','standalone/check_aspect_runner.py',count=21)
    assert cli['DOS_summary'] == 'RUNNER 21 cases 105 checks 0 failures'
    bind('src/aspect/compiler.py',cli['compiler_sha256'])
    reports['build/aspect-runner/checks.json']['checks'] = 105
    carrier = report('build/aspect-when-carrier/checks.json','standalone/check_aspect_when_carrier.py',count=5)
    assert carrier['inputs'] == 1061
    for path,digest in carrier['harness_sources'].items():
        bind(path,digest)
    reports['build/aspect-when-carrier/checks.json']['inputs'] = 1061
    client = report('build/aspect-render-client/checks.json','standalone/check_aspect_render_client.py',count=14)
    assert client['inputs'] == 38
    reports['build/aspect-render-client/checks.json']['inputs'] = 38
    report('build/aspect-render-client-dos/checks.json','standalone/test_aspect_render_client_dos.py',count=5)

    for folder,checker,count in [('aspect-script-serial-dos','test_aspect_script_serial_dos.py',28),
                                 ('aspect-script-directory-dos','test_aspect_script_directory_dos.py',15)]:
        path='build/'+folder+'/checks.json';value=passed(path)
        assert value['runner_sha256'] == CHILD and len(value['cases']) == count, path
        assert value['runner_manifest_sha256'] == evidence['build/aspect-runner/manifest.json']
        bind('standalone/'+checker,value['checker_sha256'])
        bind('src/aspect/compiler.py',value['compiler_sha256'])
        bind('src/aspect/serial_handoff.h',value['handoff_header_sha256'])
        if folder == 'aspect-script-directory-dos':
            assert sha('build/'+folder+'/expectations.json') == value['expectations_sha256']
            bind('src/terminal/translation.asm',value['actual_mapper_source_sha256'])
        previous_path='build/aspect-when-attempts/f53-native-idle-'+folder+'/checks.json'
        previous=read(previous_path)
        assert previous['checker_sha256'] == value['checker_sha256'], previous_path
        if folder=='aspect-script-directory-dos':
            assert previous['expectations_sha256'] == value['expectations_sha256']
        else:
            assert previous['fixture_sha256'] == value['fixture_sha256']
        reports[path]=dict(passed=True,cases=count,scope=value['scope'],assertions_unchanged=True,
                           identical_checker_to_preserved_f53_attempt=previous_path)

    path='build/aspect-when-raw-dos/final-0f00/checks.json'
    raw_when=passed(path)
    assert raw_when['runner_sha256'] == CHILD and len(raw_when['cases']) == 5
    bind('standalone/test_aspect_when_raw_dos.py',raw_when['checker_sha256'])
    for source,digest in raw_when['inputs'].items():
        if source.startswith('build/'):
            assert sha(source) == digest, source
            evidence[source]=digest
        else:
            bind(source,digest)
    assert sha('build/aspect-when-raw-dos/final-0f00/predictions.json') == raw_when['predictions_sha256']
    reports[path]=dict(passed=True,cases=5,scope=raw_when['scope'])

    path='build/aspect-when-renderer-dos/final-04-raw-guard/checks.json'
    renderer=passed(path)
    assert renderer['terminal_sha256'] == PARENT and renderer['runner_sha256'] == CHILD
    assert len(renderer['cases']) == 8 and sum(len(c['checks']) for c in renderer['cases']) == 315
    bind('standalone/test_aspect_when_renderer_dos.py',renderer['checker_sha256'])
    bind('standalone/test_aspect_renderer_dos.py',renderer['reused_renderer_checker_sha256'])
    pending={}
    for case in renderer['cases']:
        state=case['passive_pending_when'];pending[case['case']]=state
        if case['case']=='CSI-continuations-bypass-WHEN':
            assert state['timer_samples'] == state['maximum_native_depth'] == 0
        else:
            assert state['timer_samples'] > 0 and state['maximum_native_depth'] > 0 and state['maximum_native_gate'] > 0
        if case['case']=='two-pending-LIFO':
            assert state['maximum_native_depth'] >= 2 and state['maximum_native_gate'] >= 2
    bindings=read('build/aspect-when-renderer-dos/final-04-raw-guard/observer-bindings.json')
    assert bindings['child_binary_sha256'] == CHILD
    # Linker-map timestamps can change on a byte-identical metadata rebuild.
    # Independently reconcile every child symbol consumed by the observer.
    child_map=(ROOT/'build/aspect-runner/ASPECT.map').read_text()
    group=int(re.search(r'DGROUP\s+([0-9a-fA-F]{4}):0000',child_map)[1],16)
    assert group == bindings['child_DGROUP_relative_segment']
    for symbol,offset in bindings['child_DS_relative_words'].items():
        match=re.search(r'^\s*([0-9a-fA-F]{4}):([0-9a-fA-F]{4,8})[+*]?\s+'+re.escape(symbol)+r'$',child_map,re.M)
        assert match and int(match[1],16)*16+int(match[2],16)-group*16 == offset, symbol
    evidence['build/aspect-runner/ASPECT.map']=sha('build/aspect-runner/ASPECT.map')
    assert bindings['observer_source_sha256'] == renderer['observer_source_sha256']
    reports[path]=dict(passed=True,cases=8,checks=315,observed_pending=pending,scope=renderer['scope'],
                       executed_child_map_sha256=bindings['child_map_sha256'],
                       current_child_observer_symbol_bindings_identical=True)

    for label,name in [('when-0f00-sync-pattern','synchronet'),('when-0f00-enigma-buffer30','enigma')]:
        path='build/bbs-lab/script-login/'+label+'/checks.json';value=passed(path)
        assert value['terminal_sha256'] == PARENT and value['runner_sha256'] == CHILD
        assert value['run']['passed'] and value['editor']['passed']
        assert all(value['run']['checks'].values()) and all(value['editor']['checks'].values())
        assert value['run']['name'] == name
        for source,digest in value['sources'].items():
            bind(source,digest)
        if name=='enigma':
            assert value['editor']['modem_packet_delay_ms'] == 30
        else:
            assert b'when ' in (ROOT/'build/bbs-lab/script-login'/label/'LOGON.ASP').read_bytes().lower()
        reports[path]=dict(passed=True,editor_checks=len(value['editor']['checks']),
                          scope=value['scope'],modem_packet_delay_ms=value['editor']['modem_packet_delay_ms'])

    proof=passed('docs/validation/application-components-source-build.json')
    assert proof['output_count'] == 91
    assert not proof['original_executable_present'] and not proof['original_install_present'] and not proof['REA_database_present']
    for path,entry in proof['outputs'].items():
        assert entry['matches_workspace'] and sha('build/'+path) == entry['sha256'],path
    assert proof['outputs']['aspect-runner/ASPECT.EXE']['sha256'] == CHILD
    assert proof['outputs']['terminal/TERMINAL.EXE']['sha256'] == PARENT
    reports['docs/validation/application-components-source-build.json']=dict(passed=True,outputs=91,scope=proof['scope'])

    # Retain failure identities without publishing private captures or binaries.
    history=[
      'build/aspect-when-renderer-dos/attempt-history.json',
      'build/aspect-when-renderer-dos/actual-02/incomplete.json',
      'build/aspect-when-renderer-dos/final-03/checks.json',
      'build/aspect-render-client-history/pre-CLI-transition/transition-window-failure.json',
    ]
    for folder in (ROOT/'build/aspect-when-attempts').iterdir():
        if folder.is_dir():
            history.extend(str(p.relative_to(ROOT)) for p in folder.iterdir()
                           if p.is_file() and (p.suffix=='.json' or p.name.startswith('reason')))
    for path in sorted(set(history)):
        evidence[path]=sha(path)
    for path in ['docs/ASPECT_WHEN_RUNTIME.md','standalone/record_aspect_when_runtime.py']:
        bind(path,sha(path))
    output=dict(checkpoint_checks_passed=True,full_application_complete=False,
        full_application_gates_F01_F16='open',original_inputs=[],
        products={'TERMINAL.EXE':PARENT,'ASPECT.EXE':CHILD},sources=sources,
        local_evidence_sha256=evidence,reports=reports,preserved_history=sorted(set(history)),
        composed_receive_override_names=sorted(overrides['overrides']),
        raw_idle_policy={'resident_renderer':'native drain/match/display',
                         'active_patterns':'native drain/match',
                         'raw_without_renderer_or_patterns':'preserve explicit reads and ASIO return',
                         'native_flat_diagnostic':'unchanged native dispatcher'},
        limits=[
          'Partial66-slot trusted-source runtime; SET only WHENCASE; no arbitrary-bytecode safety.',
          'Immediate Escape and unavailable local keyboard/UI actions are maintained policies.',
          'Nine explicit composed receive expectations preserve isolated fixtures; RG0/RG1/GCLEFT/RGGLOB have direct native full-flow corroboration, not nine independent original probes.',
          'Carrier inputs and scheduled drops are models; actual product tests use emulated UART/BIOS.',
          'ENiGMA result requires explicit30ms modem buffering; no unqualified default-timing claim.',
          'No physical DCD/CTS, all-parser-stream stack bound or full application claim.',
        ])
    (ROOT/'docs/validation/aspect-when-runtime.json').write_text(json.dumps(output,indent=2)+'\n')
    print('WHEN checkpoint bound: runtime825/18298, product8/315, native rawWHEN5, legacy raw28, directory15, both scoped BBS workflows; F01-F16 open')


if __name__=='__main__':
    main()
