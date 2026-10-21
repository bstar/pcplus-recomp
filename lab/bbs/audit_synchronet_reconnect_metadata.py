#!/usr/bin/env python3
"""Read official FileBase state after an interrupted call and completed retry."""
import argparse
import binascii
import hashlib
import json
import re
import subprocess
from pathlib import Path
from audio_synchronet import ROOT, RUNTIME, sha, snapshot
from audio_synchronet_download import source
from synchronet import ENV, Peer
from modem import Telnet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cohort', type=Path)
    out = parser.parse_args().cohort.resolve()
    assert out.is_relative_to(ROOT / 'build') and not (out / 'reconnect-metadata-audit.json').exists()
    run = json.loads((out / 'result.json').read_text())
    assert not run['diagnostic'] and snapshot() == run['server']
    assert all(run['checks'][key] for key in ('normal_DOS_exit','exact_retry','complete_retry_observed','two_BBS_connections','inputs_preserved'))
    script = out / 'reconnect-metadata.js'
    script.write_text("var f=new FileBase('pcplab');if(!f.open())throw Error(f.last_error);print('PCPLAB_JSON:'+JSON.stringify(f.get('PCXTEST.BIN')));f.close();\n")
    result = subprocess.run([str(RUNTIME / 'exec/jsexec'), '-n', str(script)],
                            env=ENV(), capture_output=True, text=True, check=True)
    (out / 'reconnect-metadata.stdout').write_text(result.stdout)
    (out / 'reconnect-metadata.stderr').write_text(result.stderr)
    metadata = json.loads(result.stdout.split('PCPLAB_JSON:', 1)[1].splitlines()[0])
    data = source().read_bytes()
    counts = []
    for index in (1, 2):
        display, _ = Telnet().feed((out / f'bbs-{index}/output.bin').read_bytes())
        values = re.findall(r'Times D/Led\s*:\s*(\d+)', Peer.cleaned(display))
        assert len(values) == 1, (index, values)
        counts.append(int(values[0]))
    checks = dict(
        official_name_and_size=metadata['name'] == 'PCXTEST.BIN' and metadata['size'] == len(data) == 11521,
        official_payload_hashes=(metadata['crc16'] == binascii.crc_hqx(data, 0)
            and metadata['crc32'] == binascii.crc32(data) & 0xffffffff
            and metadata['sha1'] == hashlib.sha1(data).hexdigest()
            and metadata['md5'] == hashlib.md5(data).hexdigest()),
        interrupted_call_did_not_advance_count=counts[0] == counts[1],
        completed_retry_advanced_count_once=metadata['times_downloaded'] == counts[1] + 1,
        one_authoritative_success_log=len(re.findall(rb'D- downloaded PCXTEST\.BIN \(11521 bytes\) from Main PCPlus Lab', (out / 'server-session.log').read_bytes())) == 1,
        source_still_exact=sha(source()) == run['source_sha256'],
        server_inputs_preserved=snapshot() == run['server'])
    names = ['reconnect-metadata.js', 'reconnect-metadata.stdout', 'reconnect-metadata.stderr',
             'result.json', 'bbs-1/output.bin', 'bbs-2/output.bin', 'server-session.log']
    result = dict(passed=all(checks.values()), producer_passed=run['passed'], compatibility_accepted=False, checks=checks, metadata=metadata,
                  displayed_download_counts=counts,
                  inputs={str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__).resolve(), ROOT / 'lab/bbs/audio_synchronet.py', ROOT / 'lab/bbs/audio_synchronet_download.py', ROOT / 'lab/bbs/synchronet.py', ROOT / 'lab/bbs/modem.py']},
                  capture_sha256={name: sha(out / name) for name in names},
                  scope='Read-only official FileBase.get after producer exit. Exact source hashes and displayed pre-transfer counts on both calls must agree; the interrupted attempt must not advance the count, and the completed retry must advance it once with one success log. No server/account/configuration mutation.')
    (out / 'reconnect-metadata-audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    assert result['passed']


if __name__ == '__main__':
    main()
