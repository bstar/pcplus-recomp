#!/usr/bin/env python3
"""Record a live ENiGMA check separately from isolated decoder evidence."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live-label', required=True)
    parser.add_argument('--replay-dir', type=Path, required=True)
    parser.add_argument('--details-dir', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.live_label)
    live_dir = ROOT / 'build/bbs-lab/results/enigma-owned' / args.live_label
    live_path = live_dir / 'owned-server-checks.json'
    live = json.loads(live_path.read_text())
    assert live['mode'] == 'files'
    assert all(value for key, value in live['checks'].items() if key != 'nfo_scrolled')
    assert live['passed'] == all(live['checks'].values())
    assert live['message_count_before'] == live['message_count_after']
    assert all(sha(Path(path)) == digest for path, digest in live['input_hashes'].items())
    assert live['binary_sha256'] == sha(ROOT / 'build/terminal/TERMINAL.EXE')
    replay = json.loads((args.replay_dir / 'report.json').read_text())
    assert replay['passed']
    server = Path(live['server_root'])
    assert all(sha(server / path) == digest for path, digest in replay['source_hashes'].items())
    evidence = [live_path, args.replay_dir / 'report.json']
    results = {}
    for name in ('framer', 'decoder-stock', 'decoder-candidate'):
        path = args.replay_dir / (name + '.log')
        result = json.loads(path.read_text().strip().splitlines()[-1])
        assert result == replay['results'][name] and result['passed']
        results[name] = result
        evidence.append(path)
    for name, source in [('details-stock', server), ('details-candidate', args.candidate)]:
        path = args.details_dir / (name + '.log')
        result = json.loads(path.read_text().strip().splitlines()[-1])
        assert result['passed']
        assert result['checker_sha256'] == sha(ROOT / 'lab/bbs/patches/enigma-key-stream/check_game_details.js')
        for key, rel in [('client_sha256', 'core/client.js'),
                         ('module_sha256', 'mods/loc_game_details/loc_game_details.js'),
                         ('helper_sha256', 'mods/black_flag_files/helpers.js')]:
            assert result[key] == sha(source / rel)
        results[name] = result
        evidence.append(path)
    candidate = results['details-candidate']
    assert candidate['fixed'] and candidate['timed_checks'] == 42
    assert candidate['fragmented_differences'] == candidate['unexpected_leaves'] == 0
    for rel in ('mods/loc_game_details/loc_game_details.js', 'mods/black_flag_files/helpers.js'):
        assert sha(server / rel) == sha(args.candidate / rel)
    display = (live_dir / 'display.bin').read_bytes()
    wire = (live_dir / 'bbs-sent.bin').read_bytes()
    evidence += [live_dir / name for name in ('display.bin', 'bbs-sent.bin', 'server-session.jsonl')]
    report = dict(date=date.today().isoformat(), compatibility_complete=False,
                  live_server_modified=False, physical_modem_validated=False,
                  server_root='~/projects/black-flag-bbs', server_revision=live['server_revision'],
                  terminal_sha256=live['binary_sha256'],
                  live_file_navigation=dict(passed=live['passed'], checks=live['checks'],
                      page_headers=[list(map(int, p)) for p in re.findall(rb'NFO \| lines (\d+)-(\d+)/(\d+)', display)],
                      navigation_keys_emitted=dict(down=b'\x1b[B' in wire, page_down=b'\x1b[6~' in wire)),
                  source_hashes=replay['source_hashes'],
                  decoder_replay={name: {k: v for k, v in result.items()
                                        if k not in ('stock_baselines', 'unfragmented')}
                                  for name, result in results.items()},
                  evidence=[dict(path=str(p.resolve().relative_to(ROOT)), sha256=sha(p)) for p in evidence],
                  recorder_sha256=sha(Path(__file__)),
                  limitations=['The candidate is separate from the running server.',
                               'Elapsed-time module checks use a deterministic clock, not measured network timing.',
                               'Physical modem, complete live editor/transfer/door acceptance remain open.'])
    # Public output contains only scoped results and hashes, never credentials,
    # endpoint addresses, configuration contents or captured text.
    with args.output.open('x') as output:
        output.write(json.dumps(report, indent=2) + '\n')
    print(args.output)


if __name__ == '__main__':
    main()
