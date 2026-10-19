#!/usr/bin/env python3
"""Exercise path commands in the real terminal's ASPECT login child."""
import json
from pathlib import Path
import test_aspect_renderer_dos as renderer

ROOT = renderer.ROOT
OUT = ROOT / 'build/aspect-paths-parent-dos'


def definitions():
    source = 'proc main\nwaitfor "LOGIN:" 5\nif waitfor\n'
    for action in ('mkdir "PATHBOX"', 'chdir "PATHBOX"', 'mkdir "SUB"',
                   'chdir ".."', 'rmdir "PATHBOX\\SUB"', 'rmdir "PATHBOX"'):
        source += action + '\n'
        # CHDIR deliberately preserves the preceding native comparison result.
        if not action.startswith('chdir'):
            source += 'if failure\nexit\nendif\n'
    source += 'transmit $D_PWORD\ntransmit "^M"\npause 1\nendif\nendproc\n'
    return [dict(name='path-login', source=source,
                 banner=renderer.ESC + b'[2J' + renderer.ESC + b'[HFIRST BYTE SAFE'
                        + renderer.QUERY + renderer.DA + b'LOGIN:',
                 success=True, post=renderer.QUERY,
                 post_reply=renderer.ESC + b'[1;22R', screen=[(0, 0, 'FIRST BYTE SAFE')])]


def main():
    renderer.OUT = OUT
    renderer.definitions = definitions
    result = renderer.main()
    folder = renderer.OUT
    report = json.loads((folder / 'checks.json').read_text())
    for case in report['cases']:
        stage = folder / case['case']
        case['checks']['relative_path_hierarchy_removed'] = all(
            not (stage / name).exists() for name in ('PATHBOX', 'SUB'))
        case['passed'] = all(case['checks'].values())
        (stage / 'result.json').write_text(json.dumps(case, indent=2) + '\n')
    report.update(passed=result == 0 and all(c['passed'] for c in report['cases']),
                  checker_sha256=renderer.sha(Path(__file__)),
                  reused_renderer_checker_sha256=renderer.sha(Path(renderer.__file__)),
                  scope='Actual terminal ASPECT login child with native DOS mkdir/chdir/rmdir. '
                        'Password transmitted only after the relative hierarchy is removed; '
                        'real parent keys, renderer query, JFT/sink/history/serial ownership and '
                        'normal DOS exit checked by the reused passive observer. Owned test drives '
                        'and modeled modem; no physical modem or complete language claim.')
    (folder / 'checks.json').write_text(json.dumps(report, indent=2) + '\n')
    print('ASPECT path login:', report['passed'])
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
