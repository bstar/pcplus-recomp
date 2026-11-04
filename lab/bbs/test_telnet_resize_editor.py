#!/usr/bin/env python3
"""Compare fixed and resized unsaved drafts on the owned loopback ENiGMA."""
import argparse, fcntl, hashlib, json, re, sqlite3, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--codec', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    codec, out = a.codec.resolve(), a.output.resolve()
    assert codec.is_relative_to(ROOT / 'build') and out.is_relative_to(ROOT / 'build')
    out.mkdir(parents=True, exist_ok=False)
    lab = ROOT / 'build/bbs-lab/enigma'
    source = lab / 'source'
    probe = ROOT / 'lab/bbs/telnet_resize_editor_probe.js'
    identities = {str(x.relative_to(ROOT)): sha(x) for x in [codec, probe, Path(__file__).resolve(),
        source / 'core/fse.js', source / 'core/multi_line_edit_text_view.js',
        source / 'core/servers/login/telnet.js', source / 'core/client_term.js']}
    def messages():
        with sqlite3.connect(f'file:{source}/db/message.sqlite3?mode=ro', uri=True) as db:
            return db.execute('SELECT count(*) FROM message').fetchone()[0]
    with (lab / '.dos-integration.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before = messages()
        results = {}
        for mode in ['control', 'resize']:
            target = out / mode
            target.mkdir()
            with (target / 'stdout').open('w') as stdout, (target / 'stderr').open('w') as stderr:
                r = subprocess.run(['node', str(probe), str(codec), str(source / 'logs/enigma-bbs.log'),
                    str(target), mode], stdout=stdout, stderr=stderr, timeout=60)
            assert r.returncode == 0, (target / 'stderr').read_text()
            results[mode] = json.loads((target / 'node-result.json').read_text())
        assert messages() == before, 'Message table count changed'
    assert results['control']['sizes'] == [[80,24]]
    assert results['resize']['sizes'] == [[80,24],[80,25],[80,24]]
    compared = ['seed', 'after-grow-marker', 'after-grow-pageup', 'after-grow-pagedown',
        'after-shrink-marker', 'after-shrink-pageup', 'after-shrink-pagedown', 'editor-menu', 'discard-select', 'discard']
    observations = {}
    for name in compared:
        c, r = (out / 'control' / (name + '.bin')).read_bytes(), (out / 'resize' / (name + '.bin')).read_bytes()
        observations[name] = dict(equal=c == r, control_sha256=hashlib.sha256(c).hexdigest(),
            resize_sha256=hashlib.sha256(r).hexdigest(), control_bytes=len(c), resize_bytes=len(r))
        if name == 'discard':
            # Only the returned menu's clock is dynamic. No editor bytes are
            # normalized. Keep raw equality and both exact clock values visible.
            clock = rb'(\x1b\[23;72H\x1b\[0;1;37;40m\x1b\[0;1;37;40m)([0-9]{1,2}:[0-9]{2} [ap]m)'
            a, b = re.findall(clock, c), re.findall(clock, r)
            assert len(a) == len(b) == 1
            stable = re.sub(clock, rb'\1<CLOCK>', c) == re.sub(clock, rb'\1<CLOCK>', r)
            observations[name].update(clock_only_equal=stable,
                control_clock=a[0][1].decode(), resize_clock=b[0][1].decode())
            assert stable, 'Returned menu differs beyond its declared clock field'
        else:
            assert c and c == r, f'Actual editor output differs: {name}'
    expected_positions = {'after-grow-marker': [31,2], 'after-grow-pageup': [17,2],
        'after-grow-pagedown': [31,2], 'after-shrink-marker': [31,3],
        'after-shrink-pageup': [17,3], 'after-shrink-pagedown': [31,3]}
    for mode, result in results.items():
        steps = {s['name']: s for s in result['steps']}
        assert steps['seed']['positions'][-1] == ['INS',31,1]
        for name, position in expected_positions.items():
            assert steps[name]['menu'] == 'messageBaseNewPost'
            assert steps[name]['positions'] == [['INS', *position]], (mode, name)
        for name in ['resize-25', 'resize-24']:
            assert steps[name]['menu'] == 'messageBaseNewPost' and steps[name]['received'] == 0
            expected = dict(changed=True, advertised=True) if mode == 'resize' else None
            assert steps[name]['result'] == expected
        for name, marker in [('after-grow-pagedown', b'G '), ('after-shrink-pagedown', b'GS ')]:
            raw = (out / mode / (name + '.bin')).read_bytes()
            plain = re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]', b'', raw)
            assert all(f'L{i:02}:ABCD'.encode() in plain for i in range(18,31))
            assert marker in plain, 'Draft tail did not survive paging'
        assert steps['discard']['menu'] == 'messageBaseMainMenu'
    for x in identities:
        assert sha(ROOT / x) == identities[x], 'Input changed during the probe'
    record = dict(passed=True, sources=identities, messages_before_and_after=before,
        results={m: dict(path=str((out / m / 'node-result.json').relative_to(ROOT)),
            sha256=sha(out / m / 'node-result.json')) for m in results}, comparisons=observations,
        observed_positions=expected_positions, resize_only_output_bytes=0,
        finding='For this art-backed active editor, both NAWS updates are logged but emit no redraw in the500ms observation windows. Subsequent edit/page/discard bytes are identical to fixed24; paging remains14 document lines. This proves scoped draft/focus continuity, not dynamic editor reflow or DOS viewport coherence.',
        scope='Actual staged Telnet codec and owned loopback ENiGMA unsaved multiline editor. Independent fixed24 control versus24->25->24 updates during draft. Captures compare actual editing/paging/discard output and independent server NAWS events; no PCPlus/DOS renderer, full-route binary transfer, live bridge change, SIP or physical acceptance.')
    (out / 'result.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Completed owned ENiGMA editor resize comparison:', json.dumps({k:v['equal'] for k,v in observations.items()}))


if __name__ == '__main__':
    main()
