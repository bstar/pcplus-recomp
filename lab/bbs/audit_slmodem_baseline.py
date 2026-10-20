#!/usr/bin/env python3
"""Audit the rebuilt baseline daemon's actual VM/DSP receive-trace cohort."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from synthmodem_vm_control import ROOT, records, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cohort', type=Path)
    args = parser.parse_args()
    cohort = args.cohort.resolve()
    result = json.loads((cohort / 'result.json').read_text())
    pcm = json.loads((cohort / 'PCM-analysis.json').read_text())
    offline = json.loads((cohort / 'offline-guest.json').read_text())
    build = json.loads((ROOT / 'docs/validation/synthmodem-slmodem-build.json').read_text())
    checks = {}

    def check(name, value):
        checks[name] = bool(value)
        assert value, name

    check('producer_passed_all_nine_checks', result['passed'] and result['producer_exit'] == 0
          and len(result['checks']) == 9 and all(result['checks'].values()))
    check('baseline_daemon_and_no_discard_transport', result['slmodem_variant'] == 'baseline'
          and result['dmodem_variant'] == 'candidate')
    for name, digest in result['frozen_inputs'].items():
        check('frozen:' + name, sha(ROOT / name) == digest)
    for name, digest in result['runtime_inputs'].items():
        check('runtime:' + name, sha(Path(name)) == digest)
    for name, digest in result['tested_inputs'].items():
        check('tested:' + name, sha(Path(name)) == digest)
    for name, digest in result['captures_sha256'].items():
        check('capture:' + name, sha(cohort / name) == digest)
    for name, digest in pcm['frozen_inputs'].items():
        check('PCM:' + name, sha(cohort / name) == digest)
    check('independent_analyzer_identity', sha(ROOT / 'lab/bbs/analyze_receive_trace.py') == pcm['analyzer_sha256'])
    check('independent_decoder_identity', sha(ROOT / 'lab/bbs/diagnose_receive_pcm.js') == offline['checker_sha256'])
    check('independent_decoder_capture', sha(cohort / 'modem_rx_8k.raw') == offline['capture_sha256'])
    decoder = cohort / 'runtime/source/src/dsp/protocols/V22Demodulator.js'
    check('independent_native_decoder_source', sha(decoder) == offline['decoder_sha256'])
    check('no_upstream_edits', pcm['upstream_changes'] == [])
    check('all_captured_RTP_before_teardown_matches', pcm['common_RTP_prefix_exact'])
    alignment = pcm['sample_alignment']
    check('486400_guest_samples_exact_at_fixed_delay',
          alignment['compared_samples'] >= 486400 and alignment['differing_samples'] == 0
          and alignment['guest_PCM_equals_delayed_RTP_prefix']
          and len(alignment['offset_histogram']) == 1)
    check('independent_guest_decoder_recovers_34_authored_bytes',
          offline['equals_authored_upstream'] and offline['decoded_bytes'] == 34)
    check('authored_input_lengths', len((cohort / 'expected-upstream.bin').read_bytes()) == 34
          and len((cohort / 'expected-downstream.bin').read_bytes()) == 6000)
    image = cohort / 'runtime/candidate.cpio.gz'
    entries = records(gzip.decompress(image.read_bytes()))
    actual = [body for name, _, body in entries if name == 'usr/local/bin/slmodemd']
    check('VM_boot_archive_contains_exact_rebuilt_daemon', len(actual) == 1
          and hashlib.sha256(actual[0]).hexdigest() == build['builds']['baseline']['sha256'])
    executable = Path(result['slmodem_build'][0]['outputs']['out']) / 'bin/slmodemd'
    check('Nix_executable_matches_archive', actual[0] == executable.read_bytes())
    check('ELF32_i386', actual[0][:5] == b'\x7fELF\x01' and actual[0][18:20] == b'\x03\x00')
    receipt = {'passed': all(checks.values()), 'checks': checks,
               'cohort': str(cohort.relative_to(ROOT)), 'daemon_sha256': sha(executable),
               'producer_result_sha256': sha(cohort / 'result.json'),
               'PCM_analysis_sha256': sha(cohort / 'PCM-analysis.json'),
               'offline_decoder_result_sha256': sha(cohort / 'offline-guest.json'),
               'audit_sha256': sha(Path(__file__)), 'alignment': alignment,
               'upstream_bytes': 34, 'downstream_bytes': 6000,
               'scope': 'Rebuilt baseline slmodemd, unchanged upstream DSP object, actual software V.22/1200 VM/caller. Capture stops before external RTP teardown tail; only the common captured prefix is compared. No carrier-channel candidate, DOS/BBS workflow, analog modem or ATA.'}
    (cohort / 'baseline-audit.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__': main()
