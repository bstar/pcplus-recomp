#!/usr/bin/env python3
"""Bind live script login/terminal resume and retained diagnostic attempts."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    assert args.label and all(c.isalnum() or c in '-_' for c in args.label)
    local, sources = {}, {}

    def sha(path):
        return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

    def read(path):
        local[path] = sha(path)
        return json.loads((ROOT / path).read_text())

    def bind(path, digest):
        assert sha(path) == digest, path
        assert path not in sources or sources[path] == digest, path
        sources[path] = digest

    terminal = read('build/terminal/manifest.json')
    runner = read('build/aspect-runner/manifest.json')
    assert terminal['kind'] == 'source-only-interactive-dos-terminal'
    assert terminal['data_stack_bytes'] == 65408 and runner['original_inputs'] == []
    for folder, leaf, manifest in [('terminal', 'TERMINAL.EXE', terminal), ('aspect-runner', 'ASPECT.EXE', runner)]:
        assert manifest['binary_sha256'] == sha('build/' + folder + '/' + leaf)
        for path, digest in manifest['sources'].items():
            bind(path, digest)
    linked = read('build/terminal/script-launch-live-checks.json')
    assert linked['passed'] and linked['binary_sha256'] == terminal['binary_sha256']
    assert len(linked['cases']) == 17 and linked['inputs'] == 65
    assert linked['manifest_sha256'] == local['build/terminal/manifest.json']
    bind('standalone/check_script_launch_live.py', linked['checker_sha256'])
    for path, digest in linked['sources'].items():
        bind(path, digest)
    parent = read('build/script-launch-dos/checks.json')
    assert parent['passed'] and len(parent['cases']) == 7 and parent['case_filter'] is None
    assert parent['terminal_sha256'] == terminal['binary_sha256'] and parent['runner_sha256'] == runner['binary_sha256']
    bind('standalone/test_script_launch_dos.py', parent['source_sha256'])
    assert all(c['passed'] and all(c['checks'].values()) for c in parent['cases'])

    stage = 'build/bbs-lab/script-login/' + args.label + '/'
    result = read(stage + 'checks.json')
    assert result['passed'] and all(result['checks'].values()) and len(result['checks']) == 11
    assert result['terminal_sha256'] == terminal['binary_sha256']
    assert result['runner_sha256'] == runner['binary_sha256']
    assert result['editor']['passed'] and len(result['editor']['checks']) == 12
    assert all(result['editor']['checks'].values()) and all(result['editor']['observed_key_wire'].values())
    assert result['run']['serial']['com'] == 2 and result['run']['serial']['flow'] == 'HARD'
    assert result['run']['modem_packet_delay_ms'] == 0
    for path, digest in result['sources'].items():
        bind(path, digest)
    for leaf, digest in result['staged'].items():
        assert sha(stage + leaf) == digest, leaf
        local[stage + leaf] = digest
    assert sha(stage + 'predictions.json') == result['predictions_sha256']
    for path, digest in result['artifacts'].items():
        assert sha(path) == digest, path
        local[path] = digest
    regressions = {}
    for leaf in ['config-far-checks.json', 'program-actions-live-checks.json', 'command-menu-checks.json']:
        path = 'build/terminal/' + leaf
        check = read(path)
        assert check['passed'] and check['binary_sha256'] == terminal['binary_sha256']
        regressions[path] = check
    proof = read('docs/validation/application-components-source-build.json')
    assert proof['passed'] and proof['output_count'] == 90
    assert not proof['original_executable_present'] and not proof['REA_database_present']
    for path, entry in proof['outputs'].items():
        assert entry['matches_workspace'] and sha('build/' + path) == entry['sha256'], path
    package = read('build/dos-package/manifest.json')
    assert package['original_inputs'] == []
    assert package['files']['TERMINAL.EXE'] == terminal['binary_sha256']
    assert package['files']['ASPECT.EXE'] == runner['binary_sha256']
    for leaf, digest in package['files'].items():
        assert sha('build/dos-package/' + leaf) == digest
    for path, digest in package['sources'].items():
        bind(path, digest)

    failures = {}
    for label, archive, reason in [
        ('script-login-input-policy-de47', 'checker-before-observer.py',
         'Initial live login attempt sent no credentials. Prefix checker also incorrectly included Telnet negotiation bytes.'),
        ('script-login-input-policy-de47-observed', 'checker-before-screen.py',
         'Observer confirmed launch-error prompt; diagnostic installed observer before baseline and collected before final hardware sample, invalidating its vector comparison.'),
        ('script-login-input-policy-de47-screen', 'checker-before-port-fix.py',
         'Corrected passive screen capture confirms ASPECT serial3 before opcode execution: COM2 session incorrectly passed native active slot0 as COM1.'),
        ('script-login-selected-port-e806', 'checker-before-auto-resume.py',
         'Port fix sends credentials and authenticates; child success and return prompt observed, but terminal exits abnormally during welcome stream before scheduled acknowledgement. Exact terminal errorlevel was not recorded.'),
    ]:
        folder = 'build/bbs-lab/script-login/' + label + '/'
        old = read(folder + 'checks.json')
        assert not old['passed']
        bind_old = folder + archive
        assert sha(bind_old) == old['sources']['lab/bbs/script_login_dos_probe.py']
        assert sha(folder + 'TERMINAL.EXE') == old['terminal_sha256']
        local[bind_old] = sha(bind_old)
        failures[label] = dict(reason=reason, terminal_sha256=old['terminal_sha256'],
                               runner_sha256=old['runner_sha256'], checks=old['checks'],
                               observer_bits=old.get('observer_bits'),
                               checker_archive=bind_old, report_sha256=local[folder + 'checks.json'])
    previous = read('docs/validation/aspect-input-policy.json')
    assert previous['passed'] and previous['modules']['aspect-runner']['manifest']['binary_sha256'] == runner['binary_sha256']
    bind('standalone/record_script_session.py', sha('standalone/record_script_session.py'))
    output = dict(passed=True, normal_build_original_inputs=[], sources=sources,
                  local_evidence_sha256=local, terminal=terminal, runner=runner,
                  linked=linked, parent_DOS=parent, actual_script_login=result,
                  regressions=regressions, package=package, retained_failures=failures,
                  source_rebuild_outputs=90,
                  limitations=['All F01-F16 whole-application gates remain open.',
                               'Actual script login/editor workflow covers owned loopback Synchronet, COM2/19200/8N1/HARD only.',
                               'COM1 through4 selection is also checked at the linked prepare boundary; physical UART/modem remains unverified.',
                               'Current child ABI supports standard bases and IRQs only; parent rejects incompatible custom mappings before EXEC.',
                               'Bounded buffers and hardware flow still require peer cooperation; immediate connected-script return removes the imposed acknowledgement pause.',
                               'Full ASPECT compiler/VM/recorder, script terminal rendering and WHEN scheduling remain incomplete.',
                               'Separate ENiGMA editor failure and buffering evidence is tied to its own recorded executable, not this script-login run.'])
    (ROOT / 'docs/validation/aspect-script-session.json').write_text(json.dumps(output, indent=2) + '\n')
    print('Live script session reconciled:COM2 login,12 editor checks,65 linked inputs,7 DOS workflows,90 source-only outputs')


if __name__ == '__main__':
    main()
