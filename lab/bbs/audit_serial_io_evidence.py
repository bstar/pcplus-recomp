#!/usr/bin/env python3
"""Read-only frontend provenance/ownership audit; never waives gateway errors."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cohort', type=Path)
    out = parser.parse_args().cohort.resolve()
    n = json.loads((out/'node-result.json').read_text())
    r = json.loads((out/'result.json').read_text())
    attempts = (out/'serial-out.bin').read_bytes()
    rows = [json.loads(line) for line in (out/'serial-write-events.jsonl').read_text().splitlines()]
    checks = {}; at = 0; valid = True
    for row in rows:
        valid &= isinstance(row['offset'], int) and row['offset'] == at
        valid &= isinstance(row['length'], int) and row['length'] >= 0
        at += row['length']
        submitted = row['submittedAt'] is not None
        valid &= submitted != bool(row.get('skipped'))
        valid &= submitted or row['completedAt'] is None
        valid &= not row['error'] or row['completedAt'] is not None
        if submitted: valid &= row['submittedAt'] >= row['attemptedAt']
        if row['completedAt'] is not None: valid &= row['completedAt'] >= row['submittedAt']
    checks['complete_contiguous_attempt_manifest'] = bool(valid and at == len(attempts))
    select = lambda predicate: b''.join(attempts[v['offset']:v['offset']+v['length']] for v in rows if predicate(v))
    predicates = {'submitted':lambda v:v['submittedAt'] is not None,
                  'completed':lambda v:v['submittedAt'] is not None and v['completedAt'] is not None and not v['error'],
                  'skipped':lambda v:bool(v.get('skipped'))}
    for name, predicate in predicates.items():
        checks[name+'_artifact_matches_original_attempt_offsets'] = (out/f'serial-{name}.bin').read_bytes() == select(predicate)
    sums = {'attemptedBytes':len(attempts), 'submittedBytes':len(select(predicates['submitted'])),
            'completedBytes':len(select(predicates['completed'])), 'skippedBytes':len(select(predicates['skipped'])),
            'failedCallbackBytes':sum(v['length'] for v in rows if v['error']),
            'pendingBytes':sum(v['length'] for v in rows if v['submittedAt'] is not None and v['completedAt'] is None),
            'writeCalls':sum(v['submittedAt'] is not None for v in rows)}
    checks['all_final_counters_match_manifest'] = all(n['serialIo'][k] == v for k,v in sums.items())
    checks['all_submissions_have_final_callback'] = not any(v['submittedAt'] is not None and v['completedAt'] is None for v in rows)
    events = n['events']; errors = [e for e in events if e['type'] == 'error']
    closes = [e for e in events if e['type'] == 'serial-close']
    ends = [e for e in events if e['type'] == 'serial-end']
    shutdowns = [e for e in events if e['type'] == 'shutdown']
    checks['legacy_errors_preserved_in_structured_events'] = [e['message'] for e in errors] == n['errors']
    checks['one_observed_frontend_close_and_shutdown'] = len(closes) == len(shutdowns) == 1
    checks['observed_close_precedes_shutdown'] = len(closes) == len(shutdowns) == 1 and closes[0]['seconds'] <= shutdowns[0]['seconds']
    if len(closes) == 1:
        checks['no_write_submission_after_observed_close'] = all(v['submittedAt'] is None or v['submittedAt'] <= closes[0]['seconds'] for v in rows)
        checks['observed_frontend_input_matches_capture_size'] = closes[0]['endpoint']['bytesRead'] == (out/'serial-in.bin').stat().st_size
    checks['producer_capture_hashes'] = all(sha(out/name) == h for name,h in r['captures_sha256'].items())
    only_frontend_reset = bool(errors) and all(e['source']=='DOS-TCP' and e['code']=='ECONNRESET' and e['syscall']=='read' for e in errors)
    names = ['result.json','node-result.json','serial-write-events.jsonl','serial-out.bin',
             'serial-submitted.bin','serial-completed.bin','serial-skipped.bin','serial-in.bin']
    result = {'evidence_consistent':all(checks.values()), 'checks':checks, 'counters':sums,
              'error_events':errors, 'frontend_end_events':ends, 'frontend_close_events':closes,
              'shutdown_events':shutdowns, 'all_errors_are_frontend_read_reset':only_frontend_reset,
              'observed_reset_to_close_ms': [(closes[0]['seconds']-e['seconds'])*1000 for e in errors if e['source']=='DOS-TCP'] if len(closes)==1 else [],
              'expectedness':'Unproven. A captured source/phase does not establish why the peer reset or waive the error.',
              'capture_sha256':{name:sha(out/name) for name in names}, 'auditor_sha256':sha(Path(__file__)),
              'scope':'Independent reconstruction from original attempt offsets, actual submission/callback artifacts, socket events and retained errors. Local callback success is not peer consumption. Evidence consistency is not transport/application acceptance.'}
    (out/'serial-io-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2)); assert result['evidence_consistent']


if __name__ == '__main__': main()
