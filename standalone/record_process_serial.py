#!/usr/bin/env python3
"""Bind UART ownership evidence and the unchanged normal production build."""
import argparse,itertools,json,re
from pathlib import Path
from build_process_serial import ROOT,OUT,sha


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',required=True)
    parser.add_argument('--failed-label',help='optional retained initial DGROUP failure')
    args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    folder=OUT/'runs'/args.label
    report=json.loads((folder/'result.json').read_text());manifest=json.loads((OUT/'manifest.json').read_text())
    cpu=json.loads((OUT/'cpu.json').read_text());variants=json.loads((OUT/'variant-check/checks.json').read_text())
    assert report['passed'] and cpu['passed'] and variants['passed']
    assert cpu['case_count']==41 and len(cpu['cases'])==41 and all(c['passed'] for c in cpu['cases'])
    assert report['manifest_sha256']==sha(folder/'manifest.json')==sha(OUT/'manifest.json')
    assert report['binary_sha256']==cpu['binary_sha256']==variants['binary_sha256']==manifest['binary_sha256']==sha(OUT/'PSERIAL.EXE')
    assert report['checker_sha256']==sha(ROOT/'standalone/test_process_serial_dos.py')
    assert cpu['checker_sha256']==sha(ROOT/'standalone/check_process_serial.py')
    assert variants['checker_sha256']==sha(ROOT/'standalone/check_process_serial_variants.py')
    for p,h in cpu['reused_checkers'].items():assert sha(ROOT/p)==h,p
    for p,h in {**manifest['sources'],**manifest['process_sources']}.items():assert sha(ROOT/p)==sha(folder/'sources'/p)==h,p
    cases=report['cases'];assert {(c['port'],c['flow']) for c in cases}==set(itertools.product((1,2),'NSHB'))
    assert len(cases)==8 and sum(c['assertions'] for c in cases)==448
    for c in cases:
        assert c['passed'] and not c['timed_out'] and all(c['checks'].values())
        run=folder/f'com{c["port"]}-{c["flow"]}'
        for p,h in c['artifacts'].items():assert sha(run/p)==h,p
        assert sha(run/f'UART{c["port"]}.COM')==manifest['children'][f'UART{c["port"]}.COM']
    assert len(variants['cases'])==2 and all(c['rejected'] for c in variants['cases'])
    for c in variants['cases']:assert sha(OUT/'variant-check'/(c['case']+'.log'))==c['log_sha256']
    normal=ROOT/'build/aspect-serial/checks.json';regression=json.loads(normal.read_text())
    assert regression['passed'] and regression['inputs']==108
    assert regression['binary_sha256']==sha(ROOT/'build/aspect-serial/SERIAL.EXE')
    assert regression['manifest_sha256']==sha(ROOT/'build/aspect-serial/manifest.json')
    normal_aspect=ROOT/'build/aspect-runner/ASPECT.EXE'
    assert sha(normal_aspect)=='aef146fdf62846a2dfc5d73413f435a8bfe68ca4f68d639178083d4d21e559f5'
    normal_manifest=json.loads((normal_aspect.parent/'manifest.json').read_text())
    for p in ('src/aspect/serial.c','src/aspect/serial_backend.asm'):assert normal_manifest['sources'][p]==sha(ROOT/p)
    result=dict(passed=True,component_only=True,original_inputs=[],runtime_external_commands_enabled=False,
        whole_application_gates_closed=[],binary_sha256=manifest['binary_sha256'],
        sources=manifest['sources'],process_manifest_sha256=manifest['process_manifest_sha256'],
        CPU=dict(case_count=cpu['case_count'],cases=cpu['cases'],evidence_sha256=sha(OUT/'cpu.json')),
        DOS=dict(case_count=8,assertions=448,cases=[{k:c[k] for k in ('port','flow','assertions','checks','tx_hex','expected_tx_hex')} for c in cases],
            evidence={str(p.relative_to(ROOT)):sha(p) for p in (folder/'result.json',folder/'manifest.json')}),
        mixed_variants=variants['cases'],mixed_variant_evidence_sha256=sha(OUT/'variant-check/checks.json'),
        normal_serial_regression=dict(inputs=108,evidence_sha256=sha(normal)),
        normal_ASPECT=dict(binary_sha256=sha(normal_aspect),manifest_sha256=sha(normal_aspect.parent/'manifest.json'),
            byte_identical_to_previous_product=True),
        checkers={p:sha(ROOT/p) for p in ('standalone/check_process_serial.py','standalone/check_process_serial_variants.py',
            'standalone/test_process_serial_dos.py','standalone/record_process_serial.py')},
        limitations=['ASPECT_EXTERNAL_PROCESS component variant only; normal interpreter has no external runtime handlers.',
            'Actual DOS uses modeled nullmodem/serial hardware and cooperative peer; physical RS-232 Wi-Fi modem timing remains open.',
            'CGA/display/font/cursor/WAIT/NOCLEAR, full VM stream/lease/error integration and ASIOv4 renderer acceptance remain open.',
            'Unknown enabled FIFO rejects before handoff; a child-enabled FIFO is disabled with explicit LINE8 and no hardware pending-byte guarantee.',
            'Unrelated PIC bits are retained. Masked IRQ0 yields STATE4 with bounded port recovery; global timer recovery belongs to the full controller.'])
    if args.failed_label:
        assert re.fullmatch(r'[A-Za-z0-9_-]+',args.failed_label)
        old=OUT/'runs'/args.failed_label;failed=json.loads((old/'result.json').read_text())
        assert not failed['passed']
        old_manifest=json.loads((old/'manifest.json').read_text())
        for p,h in {**old_manifest['sources'],**old_manifest['process_sources']}.items():assert sha(old/'sources'/p)==h,p
        result['retained_failed_attempt']=dict(passed=False,reason='Missing DGROUP local-state fixups: phase changed but detached flag/data landed outside the C group.',
            evidence={str(p.relative_to(ROOT)):sha(p) for p in (old/'result.json',old/'manifest.json',old/'com1-N/CHECKS.TXT')})
    (ROOT/'docs/validation/process-serial.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Recorded41 modeled ownership cases,8 actual DOS cases/448 assertions,108 ordinary regressions and byte-identical production ASPECT.')


if __name__=='__main__':main()
