#!/usr/bin/env python3
"""Freeze native conversions, independent compiler cases and composed DOS proof."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    sources, local, modules = {}, {}, {}

    def retain(path):
        data = (ROOT / path).read_bytes()
        local[path] = sha(data)
        return json.loads(data)

    def bind(path, expected):
        assert sha((ROOT / path).read_bytes()) == expected, path
        assert path not in sources or sources[path] == expected, path
        sources[path] = expected

    for name in ['conversions', 'conversion-services', 'runtime']:
        base = f'build/aspect-{name}/'
        manifest = retain(base + 'manifest.json')
        normal = retain(base + 'checks.json')
        native = retain(base + 'checks-native.json')
        assert normal['passed'] and native['passed']
        assert manifest['original_inputs'] == normal['original_inputs'] == []
        assert normal['binary_sha256'] == native['binary_sha256'] == manifest['binary_sha256']
        for path, value in manifest['sources'].items():
            bind(path, value)
        check_key = 'checker_sha256' if name == 'conversion-services' else 'check_sha256'
        assert normal[check_key] == native[check_key]
        bind('standalone/check_aspect_' + name.replace('-', '_') + '.py', normal[check_key])
        if name != 'conversions':
            assert normal['manifest_sha256'] == native['manifest_sha256'] == local[base + 'manifest.json']
        if name == 'conversion-services':
            assert native['original_inputs'][0]['sha256'] == ORIGINAL
            assert native['native'] == native['cpu'] == normal['cpu']
            assert native['manifest'] == normal['manifest'] == manifest
            optional = native['native']
        else:
            optional = native['optional_original']
            assert optional['original_sha256'] == ORIGINAL
        modules[name] = dict(manifest=manifest, source_only_checks=normal, optional_native=optional)

    commands, services, runtime = [modules[n] for n in ['conversions', 'conversion-services', 'runtime']]
    assert commands['optional_native']['exact_conversion_bytes'] == 218
    assert commands['optional_native']['all_component_ranges'] == 46
    assert commands['source_only_checks']['cpu_scenarios'] == commands['optional_native']['paired_cpu_scenarios'] == 1711
    assert commands['source_only_checks']['visited_instructions'] == 104
    assert commands['source_only_checks']['DOS_summary'] == 'ASPECT_CONVERSIONS 8282 checks 0 failures'
    for name, value in commands['source_only_checks']['inherited_checker_sha256'].items():
        bind('standalone/' + name, value)
    assert services['manifest']['exact_bytes'] == 312
    assert services['source_only_checks']['cpu']['direct_vectors'] == 3709
    assert services['source_only_checks']['cpu']['c_selfcheck_vectors'] == 1234
    assert services['source_only_checks']['dos']['assertions'] == 6694
    assert services['source_only_checks']['dos']['passed']
    assert services['source_only_checks']['dos']['original_inputs'] == []

    corpora = {}
    for group, probe, freezer, accepted, rejected in [
        ('conversion', 'aspect_conversion_probe.py', 'freeze_aspect_conversions.py', 38, 4),
        ('compiler_validation', 'aspect_compiler_validation_probe.py', 'freeze_aspect_compiler_validation.py', 15, 0),
    ]:
        corpus = retain(f'standalone/fixtures/aspect_{group}_vectors.json')
        bind('standalone/' + probe, corpus['probe_sha256'])
        bind('standalone/' + freezer, corpus['freezer_sha256'])
        report = retain(corpus['private_report'])
        assert local[corpus['private_report']] == corpus['private_report_sha256']
        assert len(corpus['vectors']) == accepted and len(corpus['rejected']) == rejected
        assert sum(c['success'] for c in report['cases']) == accepted
        assert len(report['cases']) == accepted + rejected
        originals = {c['name']: c for c in report['cases'] if c['success']}
        for vector in corpus['vectors']:
            assert vector['source_encoding'] == 'cp437'
            assert sha(vector['source'].encode('cp437')) == vector['source_sha256']
            assert sha(bytes.fromhex(vector['hex'])) == vector['asx_sha256']
            for key in ['source_sha256', 'asx_sha256']:
                assert vector[key] == originals[vector['name']][key]
        corpora[group] = dict(accepted=accepted, rejected=rejected, findings=corpus.get('expectation_model'))

    path = 'build/aspect-runtime/RESULT.TXT'
    data = (ROOT / path).read_bytes()
    local[path] = sha(data)
    text = data.decode('ascii')
    run = runtime['source_only_checks']
    native = retain('build/aspect-runtime/checks-native.json')
    assert run['result_sha256'] == native['result_sha256'] == local[path]
    assert run['DOS_summary'] == 'ASPECT_RUNTIME 410 cases 6090 checks 0 failures'
    assert run['fixture_count'] == 237
    fields = ['file', 'error', 'steps', 'peak', 'cleanup', 'close', 'integer0', 'long0']
    rows = [dict(zip(fields, [name, *map(int, values)])) for name, *values in re.findall(
        r'CASE (\S+) error=(\d+) steps=(\d+) peak=(\d+) cleanup=(\d+) close=(\d+) int0=(\d+) long0=(\d+)', text)]
    assert len(rows) == runtime['manifest']['diagnostic_case_count'] == 410
    slots = {int(k, 16) for k in runtime['manifest']['supported_slots']}
    unsupported = [r for r in rows if re.fullmatch(r'U[0-9A-F]{3}\.ASX', r['file'])]
    assert len(slots) == 54 and len(unsupported) == run['unsupported_slot_cases'] == 161
    assert {int(r['file'][1:4], 16) for r in unsupported} == set(range(215)) - slots
    for row in unsupported:
        assert row['error'] == 3 and row['steps'] == 1 and row['cleanup'] == row['close'] == 1
    values = {(name, key): int(value) for name, key, value in
              re.findall(r'VALUE (\S+) (integer\d+|long\d+)=(\d+)', text)}
    strings = {(name, key): bytes.fromhex(value) for name, key, value in
               re.findall(r'STRING (\S+) (string\d+)=([0-9A-F]*)', text)}
    errors = {'divide_zero': 11, 'native_int0': 12, 'float': 4, 'budget': 6,
              'stack': 9, 'unsupported': 3, 'operand': 7}
    for name, fixture in runtime['manifest']['fixture_expectations'].items():
        file, expected = name + '.ASX', fixture['expected']
        row = next(r for r in rows if r['file'] == file)
        assert row['error'] == errors.get(expected.get('error'), 0), name
        assert row['cleanup'] == row['close'] == 1
        for key, value in expected.items():
            if re.fullmatch(r'(integer|long)\d+', key):
                assert values[(file, key)] == value, (name, key)
            if re.fullmatch(r'string\d+', key):
                assert strings[(file, key)] == value.encode('cp437'), (name, key)
    evidence = retain('analysis/aspect-expression/rea-conversions-03.json')
    records = [dict(id=r['evidence_id'], operation=r['operation'], parameters=r['parameters'],
                    subject_sha256=r['subject']['digest']['sha256']) for r in evidence['records']]
    assert len(records) == 20
    compiler = retain('build/aspect-compiler/checks.json')
    assert compiler['success'] and compiler['original_inputs'] == []
    assert compiler['test_methods'] == 9
    assert compiler['frozen_vectors_checked'] == compiler['presentation_variants_checked'] == 237
    bind('src/aspect/compiler.py', compiler['compiler_sha256'])
    bind('standalone/test_aspect_compiler.py', compiler['checker_sha256'])
    for group, value in compiler['fixture_sha256'].items():
        bind(f'standalone/fixtures/aspect_{group}_vectors.json', value)
    proof = retain('docs/validation/application-components-source-build.json')
    assert proof['passed'] and proof['output_count'] == 82
    assert not proof['original_executable_present'] and not proof['REA_database_present']
    assert 'standalone/test_aspect_compiler.py' in proof['build_scripts']
    for relative, output in proof['outputs'].items():
        assert output['matches_workspace']
        assert sha((ROOT / 'build' / relative).read_bytes()) == output['sha256'], relative
    sources['standalone/record_aspect_conversions.py'] = sha(Path(__file__).read_bytes())
    result = dict(passed=True, sources=sources, local_evidence=local, modules=modules,
                  corpora=corpora, compiler=compiler, static_evidence=records,
                  source_rebuild=dict(output_count=82, snapshot_sha256=proof['source_snapshot_sha256'],
                                      compiler_regressions_in_fresh_tree=True),
                  runtime_cases=[r for r in rows if r not in unsupported],
                  limitations=['54of215 slots;161 explicitly abort.',
                               'Maintained host compiler covers tested grammar, not full ASPECT or DOS-hosted compilation.',
                               'Native unchecked buffers/indices remain; fixed diagnostic suite is not arbitrary-input safety.',
                               'Float/formatting/recorder/full application bindings/terminal integration and all F01-F16 gates remain open.'])
    out = ROOT / 'docs/validation/aspect-conversions.json'
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(out.relative_to(ROOT))


if __name__ == '__main__':
    main()
