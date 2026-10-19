#!/usr/bin/env python3
"""Reconcile and freeze string-command recovery and composed DOS evidence."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    local, sources, modules = {}, {}, {}

    def retain(path):
        data = (ROOT / path).read_bytes()
        local[path] = digest(data)
        return json.loads(data)

    def bind(path, expected):
        assert digest((ROOT / path).read_bytes()) == expected, path
        assert path not in sources or sources[path] == expected, path
        sources[path] = expected

    for name in ['string-services', 'string-commands', 'runtime']:
        base = f'build/aspect-{name}/'
        manifest = retain(base + 'manifest.json')
        normal = retain(base + 'checks.json')
        native = retain(base + 'checks-native.json')
        assert normal['passed'] and native['passed']
        assert normal['original_inputs'] == manifest['original_inputs'] == []
        assert normal['binary_sha256'] == native['binary_sha256'] == manifest['binary_sha256']
        for path, value in manifest['sources'].items():
            bind(path, value)
        checker_key = 'checker_sha256' if name == 'string-services' else 'check_sha256'
        assert normal[checker_key] == native[checker_key]
        bind('standalone/check_aspect_' + name.replace('-', '_') + '.py', normal[checker_key])
        if name != 'string-commands':
            assert normal['manifest_sha256'] == native['manifest_sha256'] == local[base + 'manifest.json']
        if name == 'string-services':
            assert native['original_inputs'][0]['sha256'] == ORIGINAL
            assert normal['cpu'] == native['cpu'] == native['native']
            assert normal['native'] is None
            assert normal['manifest'] == native['manifest'] == manifest
        else:
            assert native['optional_original']['original_sha256'] == ORIGINAL
        modules[name] = dict(manifest=manifest, source_only_checks=normal,
                             optional_native=native.get('optional_original', native.get('native')))

    services, commands, runtime = [modules[k] for k in ['string-services', 'string-commands', 'runtime']]
    assert services['manifest']['exact_new_bytes'] == 173
    assert services['manifest']['reused_bytes'] == 168
    service_checks = services['source_only_checks']
    assert service_checks['cpu']['direct_vectors'] == 6940
    assert service_checks['cpu']['c_selfcheck_vectors'] == 291
    assert service_checks['dos']['passed'] and service_checks['dos']['original_inputs'] == []
    assert service_checks['dos']['vectors'] == 291 and service_checks['dos']['assertions'] == 76091
    cmd = commands['source_only_checks']
    assert cmd['cpu_scenarios'] == commands['optional_native']['paired_cpu_scenarios'] == 2058
    assert cmd['visited_instructions'] == 196
    assert cmd['DOS_summary'] == 'ASPECT_STRING_COMMANDS 27819 checks 0 failures'
    assert commands['optional_native']['exact_command_bytes'] == 401
    assert commands['optional_native']['all_component_ranges'] == 37
    bind('standalone/check_aspect_strings.py', cmd['inherited_checker_sha256'])

    corpus = retain('standalone/fixtures/aspect_string_command_vectors.json')
    bind('standalone/aspect_string_command_probe.py', corpus['probe_sha256'])
    bind('standalone/freeze_aspect_string_commands.py', corpus['freezer_sha256'])
    report = retain(corpus['private_report'])
    assert local[corpus['private_report']] == corpus['private_report_sha256']
    assert len(report['cases']) == 65 and sum(c['success'] for c in report['cases']) == 52
    assert len(corpus['vectors']) == 52 and len(corpus['rejected']) == 13
    assert corpus['source_encoding'] == 'cp437'
    accepted = {c['name']: c for c in report['cases'] if c['success']}
    for vector in corpus['vectors']:
        assert vector['source_encoding'] == 'cp437' and not vector['dos_excluded']
        assert digest(vector['source'].encode('cp437')) == vector['source_sha256']
        assert digest(bytes.fromhex(vector['hex'])) == vector['asx_sha256']
        for key in ['source_sha256', 'asx_sha256']:
            assert vector[key] == accepted[vector['name']][key]
    assert sum('error' not in v['expected'] for v in corpus['vectors']) == 46

    result_path = 'build/aspect-runtime/RESULT.TXT'
    data = (ROOT / result_path).read_bytes()
    local[result_path] = digest(data)
    text = data.decode('ascii')
    run = runtime['source_only_checks']
    assert run['result_sha256'] == read_native_result_hash(ROOT) == local[result_path]
    assert run['DOS_summary'] == 'ASPECT_RUNTIME 361 cases 5371 checks 0 failures'
    assert run['fixture_count'] == 184
    rows = []
    fields = ['file', 'error', 'steps', 'peak', 'cleanup', 'close', 'integer0', 'long0']
    pattern = r'CASE (\S+) error=(\d+) steps=(\d+) peak=(\d+) cleanup=(\d+) close=(\d+) int0=(\d+) long0=(\d+)'
    for name, *values in re.findall(pattern, text):
        rows.append(dict(zip(fields, [name, *map(int, values)])))
    assert len(rows) == runtime['manifest']['diagnostic_case_count'] == 361
    slots = {int(k, 16) for k in runtime['manifest']['supported_slots']}
    unsupported = [r for r in rows if re.fullmatch(r'U[0-9A-F]{3}\.ASX', r['file'])]
    assert len(slots) == 50 and len(unsupported) == run['unsupported_slot_cases'] == 165
    assert {int(r['file'][1:4], 16) for r in unsupported} == set(range(215)) - slots
    for row in unsupported:
        assert row['error'] == 3 and row['steps'] == 1 and row['cleanup'] == row['close'] == 1
    values = {(name, key): int(value) for name, key, value in
              re.findall(r'VALUE (\S+) (integer\d+|long\d+)=(\d+)', text)}
    strings = {(name, key): bytes.fromhex(value) for name, key, value in
               re.findall(r'STRING (\S+) (string\d+)=([0-9A-F]*)', text)}
    native_errors = {name: int(code) for name, code in re.findall(r'NATIVE (\S+) code=(\d+)', text)}
    errors = {'divide_zero': 11, 'native_int0': 12, 'float': 4, 'budget': 6,
              'stack': 9, 'unsupported': 3, 'operand': 7}
    for name, fixture in runtime['manifest']['fixture_expectations'].items():
        file = name + '.ASX'
        row = next(r for r in rows if r['file'] == file)
        expected = fixture['expected']
        assert row['error'] == errors.get(expected.get('error'), 0), (name, row)
        assert row['cleanup'] == row['close'] == 1, name
        for key, value in expected.items():
            if re.fullmatch(r'(integer|long)\d+', key):
                assert values[(file, key)] == value, (name, key)
            if re.fullmatch(r'string\d+', key):
                assert strings[(file, key)] == value.encode('cp437'), (name, key)
        if 'native_error' in expected:
            assert native_errors[file] == expected['native_error'], name
    assert len(native_errors) == 6
    assert set(runtime['optional_native']['comparison_builtins']) == {'21', '27'}

    evidence = []
    for i in range(1, 5):
        bundle = retain(f'analysis/aspect-expression/rea-string-helpers-0{i}.json')
        evidence += [dict(id=r['evidence_id'], operation=r['operation'], parameters=r['parameters'],
                          subject_sha256=r['subject']['digest']['sha256']) for r in bundle['records']]
    assert len(evidence) == 12
    sources['standalone/record_aspect_string_commands.py'] = digest(Path(__file__).read_bytes())
    result = dict(passed=True, sources=sources, local_evidence=local, modules=modules,
                  compiler=dict(cases=65, accepted=52, rejected=13, completions=46,
                                operand_stops=6, encoding='cp437', findings=corpus['findings']),
                  runtime_cases=[r for r in rows if r not in unsupported], unsupported_count=165,
                  native_operand_errors=native_errors, static_evidence=evidence,
                  limitations=[
                      'Only50of215 opcode slots are wired;165 abort explicitly.',
                      'Original compiler is an optional oracle; a source compiler remains required.',
                      'Component callback fixtures do not prove complete parser or builtin behavior.',
                      'Native unchecked pointer/frame/span behavior remains; fixed authored fixtures are not arbitrary-input safety.',
                      'Float, recorder, full application bindings and terminal integration remain unfinished; all F01-F16 gates remain open.'])
    out = ROOT / 'docs/validation/aspect-string-commands.json'
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(out.relative_to(ROOT))


def read_native_result_hash(root):
    return json.loads((root / 'build/aspect-runtime/checks-native.json').read_text())['result_sha256']


if __name__ == '__main__':
    main()
