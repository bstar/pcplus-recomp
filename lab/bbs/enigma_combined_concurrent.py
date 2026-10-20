#!/usr/bin/env python3
"""Reuse the actual two-peer route while preserving earlier cumulative uploads."""
import argparse
import json
from pathlib import Path

import enigma_concurrent_upload as base
from enigma_key_stream_fixture import ROOT, owned, sha


def files(root):
    result = {}
    for path in root.iterdir():
        assert path.is_file()
        value = path.stat()
        result[path.name] = dict(inode=value.st_ino, bytes=value.st_size,
            mtime_ns=value.st_mtime_ns, ctime_ns=value.st_ctime_ns, sha256=sha(path))
    return result


def run(args):
    candidate = owned(args.candidate)
    assert (candidate / 'combined-instance.json').is_file()
    before = sha(Path(__file__))
    installed = candidate / 'file_base/pcplus_upload'
    inventory = files(installed)
    assert inventory and not (set(inventory) & {'CONCA.BIN', 'CONCB.BIN'})
    catalog = base.metadata(candidate, sorted(inventory))
    original = base.Lab
    class PreservingLab(original):
        def __init__(self, *values):
            super().__init__(*values)
            (self.output / 'existing-upload-baseline.json').write_text(json.dumps(
                dict(files=inventory, catalog=catalog, adapter_sha256=before), indent=2) + '\n')
            self.main_interrupts = []

        def go(self, peer, data, menu):
            if self.menu(peer) == 'mainMenu':
                acknowledged = 0
                def ready():
                    nonlocal acknowledged
                    visible = base.Peer.cleaned(peer.history)
                    pause = '>> smash your keyboard <<'
                    if visible.rfind('...cmd:') > visible.rfind(pause):
                        return True
                    count = visible.count(pause)
                    if count > acknowledged:
                        assert 'ACHIEVEMENT' in visible
                        acknowledged = count
                        peer.application(b'\r', 'acknowledge queued Main achievement')
                        self.main_interrupts.append(dict(peer=peer.name, pause=count))
                    return False
                self.wait(ready, 'actual Main prompt after queued achievements')
            return super().go(peer, data, menu)

        def snapshot(self, label):
            temporary = super().snapshot(label)
            row = self.snapshots[-1]
            current = files(installed)
            preserved = {name: current[name] for name in inventory if name in current}
            old_catalog = base.metadata(candidate, sorted(inventory))
            row.update(installed_all=row['installed'], preserved_files=preserved, preserved_catalog=old_catalog)
            # The inherited route's installed assertions concern its NEW files.
            # Preserve the complete observation alongside that explicit delta.
            row['installed'] = sorted(set(row['installed_all']) - set(inventory))
            self.check('earlier_uploads_preserved_at_' + str(len(self.snapshots)), preserved == inventory and old_catalog == catalog)
            return temporary
    base.Lab = PreservingLab
    try:
        base.run(args)
    finally:
        base.Lab = original
    out = ROOT / 'build/bbs-lab/results/enigma' / args.label
    report_path = out / 'concurrent-checks.json'
    report = json.loads(report_path.read_text())
    report['composition_adapter'] = dict(sha256=before, unchanged=before == sha(Path(__file__)),
        earlier_uploads=sorted(inventory), baseline_sha256=sha(out / 'existing-upload-baseline.json'))
    report['passed'] = report['passed'] and report['composition_adapter']['unchanged']
    report['scope'] += ' Explicit nonempty-directory adapter retains full installed observations and verifies prior file identity/content/catalog at all four snapshots.'
    report_path.write_text(json.dumps(report, indent=2) + '\n')
    assert report['passed']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--label', required=True)
    parser.set_defaults(setup=False)
    run(parser.parse_args())
