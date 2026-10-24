#!/usr/bin/env python3
"""Seal a matched stock immediate/buffered pair and checked-decoder DOS run."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def case(label):
    assert label and all(c.isalnum() or c in '-_' for c in label)
    wrapper = ROOT / 'build/bbs-lab/results/enigma' / (label + '-wrapper')
    report = load(wrapper / 'checks.json')
    for name, digest in report['inputs'].items():
        assert sha(ROOT / name) == digest, name
    for name, digest in report['artifacts'].items():
        assert sha(ROOT / name) == digest, name
    command = load(wrapper / 'command.json')
    normalized = command[:]
    for flag in ('--label', '--packet-delay-ms'):
        at = normalized.index(flag)
        del normalized[at:at + 2]
    return report, normalized, wrapper


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--immediate', required=True)
    p.add_argument('--buffered', required=True)
    p.add_argument('--framed', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    immediate, ic, iw = case(a.immediate)
    buffered, bc, bw = case(a.buffered)
    framed, fc, fw = case(a.framed)
    assert immediate['inputs'] == buffered['inputs'] and ic == bc
    def instance(report):
        names = [n for n in report['inputs'] if n.endswith('/peer-width-instance.json')]
        assert len(names) == 1
        return load(ROOT / names[0])
    stock_instance, framed_instance = instance(immediate), instance(framed)
    assert not stock_instance.get('decoder_inputs')
    assert set(framed_instance['decoder_inputs']) == {'core/client.js', 'core/key_stream.js'}
    assert framed_instance['decoder_report_sha256']
    assert stock_instance['revision'] == framed_instance['revision']
    assert immediate['binary_sha256'] == buffered['binary_sha256'] == framed['binary_sha256']
    assert immediate['modem_packet_delay_ms'] == framed['modem_packet_delay_ms'] == 0
    assert 0 < buffered['modem_packet_delay_ms'] <= 100
    assert not immediate['passed'] and not immediate['checks']['actual_server_CPR']
    assert immediate['checks']['harness'] and immediate['checks']['authenticated'] and immediate['checks']['immutable_inputs']
    assert buffered['passed'] and framed['passed']
    assert all(buffered['checks'].values()) and all(framed['checks'].values())
    for report in (buffered, framed):
        assert report['paints'] == [[132, 0], [132, 1], [132, 0], [80, 0], [132, 0]]
        assert report['cprs'] == [[2, 128], [2, 128], [2, 128], [2, 80], [2, 128]]
    custody = {}
    cohorts = {}
    for label, report, wrapper in [(a.immediate, immediate, iw), (a.buffered, buffered, bw), (a.framed, framed, fw)]:
        custody.update(report['artifacts'])
        custody[str((wrapper / 'checks.json').relative_to(ROOT))] = sha(wrapper / 'checks.json')
        cohorts[label] = {k: report[k] for k in ['passed', 'checks', 'binary_sha256', 'modem_packet_delay_ms',
                                               'paints', 'cprs', 'server_input_chunks', 'inputs', 'scope']}
    result = dict(passed=True, full_compatibility=False, accepted_for_deployment=False,
                  cohorts=cohorts, artifact_hashes=custody,
                  recorder_sha256=sha(Path(__file__)),
                  limitations=['The stock immediate path still fails; modem batching is an observed local workaround, not a guarantee of TCP receive boundaries.',
                               'The immediate decoder pass uses a separate explicitly patched server, never the stock or live board.',
                               'This synthetic authenticated menu is not stock artwork adaptation, active ASPECT/BBS composition, source compilation, wide file transfer or physical modem acceptance.',
                               'The broader application source proof and card release are separate gates.'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(f'Sealed three DOS ENiGMA runs and {len(custody)} artifacts; stock immediate failure retained')


if __name__ == '__main__':
    main()
