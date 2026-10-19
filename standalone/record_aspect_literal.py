#!/usr/bin/env python3
"""Reconcile DOS compiler, native CPU, maintained codec and clean-source proof."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus', type=Path, required=True)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    corpus, native = args.corpus.resolve(), args.native.resolve()
    for path in (corpus, native):
        assert path.is_relative_to(ROOT / 'analysis/aspect-compiler')
    oracle = read(corpus / 'report.json')
    replay = read(native / 'result.json')
    maintained = read(ROOT / 'build/aspect-literal/checks.json')
    build = read(ROOT / 'build/aspect-literal/manifest.json')
    source = read(ROOT / 'docs/validation/application-components-source-build.json')
    fixtures = read(ROOT / 'standalone/fixtures/aspect_literal_vectors.json')
    evidence_path = ROOT / 'analysis/aspect-compiler/rea-compiler-complete.json'
    evidence = read(evidence_path)
    assert oracle['compiler_sha256'] == replay['compiler_sha256'] == fixtures['compiler_sha256']
    assert replay['cases'] == len(replay['records']) == 725 and replay['pass1_cases'] == 52
    assert oracle['harness_sha256'] == sha(ROOT / 'standalone/aspect_compiler_probe.py')
    assert replay['passed'] and replay['comparison'] == 'maintained host C codec'
    assert replay['harness_sha256'] == sha(ROOT / 'standalone/check_aspect_literal_native.py')
    assert replay['fixture_sha256'] == sha(ROOT / 'standalone/fixtures/aspect_literal_vectors.json')
    assert replay['host_library_sha256'] == sha(ROOT / 'build/aspect-literal/literal.so')
    assert maintained['passed'] and source['passed']
    for name, digest in maintained['sources'].items():
        assert sha(ROOT / name) == digest, name
    assert build['binary_sha256'] == maintained['binary_sha256'] == sha(ROOT / 'build/aspect-literal/LITERAL.EXE')
    assert source['outputs']['aspect-literal/LITERAL.EXE']['sha256'] == build['binary_sha256']
    assert source['output_count'] == 65 and all(v['matches_workspace'] for v in source['outputs'].values())
    assert not any(source[k] for k in ['original_executable_present','original_install_present','REA_database_present','previous_build_outputs_present'])
    records = []
    by_name = {}
    for record in oracle['cases']:
        name = record['name'];by_name[name] = record
        assert record['source_sha256'] == sha(corpus / (name + '.ASP'))
        assert record['log_sha256'] == sha(corpus / (name + '.LOG'))
        assert record['success'] == (record['return_class'] == 'ZERO')
        if record['success']:
            assert sha(corpus / (name + '.ASX')) == record['asx_sha256']
        else:
            assert not (corpus / (name + '.ASX')).exists()
        records.append({k: v for k, v in record.items() if k not in ['diagnostic','hex']})
        code = re.search(r'Error (C\d+)', record['diagnostic'])
        if code:
            records[-1]['diagnostic_code'] = code[1]
    for vector in fixtures['vectors']:
        name = vector['case'];data = (corpus / (name + '.ASX')).read_bytes()
        text = bytes.fromhex(vector['text_hex']);position = vector['payload_offset']
        assert vector['source_sha256'] == by_name[name]['source_sha256']
        assert vector['asx_sha256'] == by_name[name]['asx_sha256']
        assert data[position-1] == 0xaa
        assert data[position:position+len(text)+2].hex() == vector['wire_hex']
        line = (corpus / (name + '.ASP')).read_bytes().split(b'\r\n')[vector['source_line']-1]
        assert b'"'+text+b'"' in line
    relevant = []
    for record in evidence['records']:
        assert record['subject']['digest']['sha256'] == oracle['compiler_sha256']
        if record['operation'] == 'inspect_native_load_image':
            assert record['normalized_result']['status'] == 'verified'
        relevant.append(dict(evidence_id=record['evidence_id'],operation=record['operation'],
            parameters=record['parameters'],target_sha256=record['subject']['digest']['sha256']))
    native_summary = {k: v for k, v in replay.items() if k != 'records'}
    inputs = [ROOT / name for name in ['Makefile','nix/flake.lock','src/aspect/literal.c',
        'src/aspect/literal.h','standalone/aspect_compiler_probe.py','standalone/build_aspect_literal.py',
        'standalone/check_aspect_literal.py','standalone/check_aspect_literal_native.py',
        'standalone/fixtures/aspect_literal_vectors.json','standalone/prove_source_build.py',
        'standalone/record_aspect_literal.py']]
    report = dict(passed=True,maintained_codec=maintained,native_cpu=native_summary,
        compiler_oracle=dict(compiler_sha256=oracle['compiler_sha256'],cases=len(records),
            accepted=sum(r['success'] for r in records),rejected=sum(not r['success'] for r in records),
            records=records,scope=oracle['scope']),
        source_only_build=dict(output_count=source['output_count'],snapshot_sha256=source['source_snapshot_sha256'],
            executable_sha256=build['binary_sha256'],terminal_sha256=source['outputs']['terminal/TERMINAL.EXE']['sha256']),
        rea_evidence=relevant,
        private_evidence={str(p.relative_to(ROOT)):sha(p) for p in [evidence_path,corpus/'report.json',native/'result.json',
            ROOT/'build/aspect-literal/checks.json',ROOT/'build/application-source-proof/result.json']},
        inputs={str(p.relative_to(ROOT)):sha(p) for p in inputs},
        historical_limitations=['corpus01 failed-case return files were truncated by conditional redirection; those return fields are not used as success evidence',
            'The earlier PROFILE.ASP fixture contains literal backslash-r/backslash-n text; its source layout is not equivalent to these CRLF scripts'],
        scope='Nonempty ASPECT1.01 literal payload codec, not a complete compiler, source parser, application VM or script execution feature. All whole-application gates remain open.')
    assert not args.output.exists(), 'Preserve previous ledgers'
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(args.output)


if __name__ == '__main__':
    main()
