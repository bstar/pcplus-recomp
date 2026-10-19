#!/usr/bin/env python3
"""Gate actual terminal login on native DOS queries and all earlier file probes."""
import json
from pathlib import Path
import re
import test_aspect_renderer_dos as renderer
import test_aspect_file_times_parent_dos as timestamps

ROOT = renderer.ROOT
OUT = ROOT / 'build/aspect-system-query-parent-dos'


def definitions():
    case = timestamps.definitions()[0]
    source = case['source'].replace('string attrs,date_value,time_value',
                                   'integer version_len\nstring workdir,version,query_number,attrs,date_value,time_value')
    source = source.replace('long size', 'long size,available')
    source = source.replace('if waitfor\n', r'''if waitfor
getdir 0 workdir
if failure
exit
endif
strcmp workdir "D:\"
if failure
exit
endif
dosver version
strlen version version_len
if version_len < 4
exit
endif
diskfree 0 available
if available <= 0L
exit
endif
fopen 4 "QUERY.LOG" "wb"
fputs 4 workdir
fputs 4 "|"
fputs 4 version
fputs 4 "|"
ltoa available query_number
fputs 4 query_number
fclose 4
''', 1)
    return [dict(case, name='system-query-login', source=source)]


def main():
    renderer.OUT = OUT
    renderer.definitions = definitions
    status = renderer.main()
    report = json.loads((renderer.OUT / 'checks.json').read_text())
    case = report['cases'][0]
    trace = renderer.OUT / case['case'] / 'QUERY.LOG'
    match = re.fullmatch(rb'D:\\\|[0-9]{1,3}\.[0-9]{2,3}\|([0-9]+)', trace.read_bytes()) if trace.is_file() else None
    case['checks']['system_queries_before_login'] = bool(match and int(match[1]) > 0)
    report.update(passed=status == 0 and all(case['checks'].values()),
                  query_trace_sha256=renderer.sha(trace) if trace.is_file() else None,
                  checker_sha256=renderer.sha(Path(__file__)),
                  reused_renderer_sha256=renderer.sha(Path(renderer.__file__)),
                  reused_timestamp_parent_sha256=renderer.sha(Path(timestamps.__file__)),
                  scope='Actual production terminal/ASPECT and DOS queries before earlier timestamp/attribute/enumeration/query/rename login gates. Real current-drive directory, DOSVER far-global writeback, positive disk free, exact trace grammar, normal parent keyboard/UART/owner/hardware restoration. Modeled modem, no physical claim.')
    (renderer.OUT / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print('System-query parent', report['passed'])
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
