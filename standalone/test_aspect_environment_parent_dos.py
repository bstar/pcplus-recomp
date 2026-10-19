#!/usr/bin/env python3
"""Gate production login on inherited environment and independent owned values."""
import json
from pathlib import Path
import test_aspect_renderer_dos as renderer
import test_aspect_system_query_parent_dos as queries

ROOT = renderer.ROOT
OUT = ROOT / 'build/aspect-environment-parent-dos'


def definitions():
    case = queries.definitions()[0]
    source = case['source'].replace('integer version_len', 'string inherited,env_a,env_b\ninteger version_len')
    source = source.replace('if waitfor\n', '''if waitfor
getenv "loc_parent" inherited
strcmp inherited "MiXeD"
if failure
exit
endif
putenv "LOC_A=one"
if failure
exit
endif
putenv "LOC_B=two"
if failure
exit
endif
getenv "loc_a" env_a
getenv "loc_b" env_b
strcmp env_a "ONE"
if failure
exit
endif
strcmp env_b "TWO"
if failure
exit
endif
fopen 4 "ENV.LOG" "wb"
fputs 4 inherited
fputs 4 "|"
fputs 4 env_a
fputs 4 "|"
fputs 4 env_b
fputs 4 "|"
putenv "LOC_A="
getenv "LOC_A" env_a
strcmp env_a $NULL
if failure
exit
endif
fputs 4 env_a
fclose 4
putenv "LOC_B="
''', 1)
    return [dict(case, name='environment-login', source=source, environment={'LOC_PARENT': 'MiXeD'})]


def main():
    renderer.OUT = OUT
    renderer.definitions = definitions
    status = renderer.main()
    report = json.loads((renderer.OUT / 'checks.json').read_text())
    case = report['cases'][0]
    trace = renderer.OUT / case['case'] / 'ENV.LOG'
    case['checks']['environment_before_login'] = trace.is_file() and trace.read_bytes() == b'MiXeD|ONE|TWO|'
    report.update(passed=status == 0 and all(case['checks'].values()),
                  environment_trace_sha256=renderer.sha(trace) if trace.is_file() else None,
                  checker_sha256=renderer.sha(Path(__file__)),
                  reused_renderer_sha256=renderer.sha(Path(renderer.__file__)),
                  reused_query_parent_sha256=renderer.sha(Path(queries.__file__)),
                  scope='Actual terminal/ASPECT child: inherited mixed-case value, native assignment uppercase, two independently owned values, deletion and exact environment trace before query/timestamp/attribute/enumeration/file login gates. Parent keyboard/UART/hardware/JFT/owner restoration. Synthetic process environment and modeled modem; no physical/full application claim.')
    (renderer.OUT / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Environment parent', report['passed'])
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
