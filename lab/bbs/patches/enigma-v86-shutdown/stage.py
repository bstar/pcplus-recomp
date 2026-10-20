#!/usr/bin/env python3
"""Stage controlled-error image transfer and awaited atomic disk persistence."""
import argparse
import json
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from enigma_key_stream_fixture import owned, pid, sha


def replace(text, changes):
    for old, new in changes:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    return text


def stage(candidate):
    candidate = owned(candidate)
    assert not pid(candidate)
    marker = candidate / 'v86-door-instance.json'
    meta = json.loads(marker.read_text())
    assert meta['input_bridge'] and 'input_trace' not in meta and 'input_shutdown' not in meta
    worker_name, door_name = 'core/v86_door/v86_worker.js', 'core/v86_door/v86_door.js'
    worker, door = candidate / worker_name, candidate / door_name
    original = {name: sha(candidate / name) for name in (worker_name, door_name)}
    assert original[worker_name] == meta['fixture_inputs'][worker_name] == meta['input_bridge']['staged_worker_sha256']
    assert original[door_name] == meta['fixture_inputs'][door_name] == meta['source_inputs'][door_name]
    worker_text = replace(worker.read_text(), [
        ("""onError: error => {
        parentPort.postMessage({type: 'error', message: error.message});
        shutdown();
    },""", "onError: error => shutdown(error),"),
        ("""} catch (error) {
                parentPort.postMessage({type: 'error', message: error.message});
                shutdown();
            }""", """} catch (error) {
                shutdown(error);
            }"""),
        ('function shutdown() {', 'function shutdown(error) {'),
        ('shutdownStarted = true;', 'shutdownStarted = true;\n    const failure = error && error.message;'),
        ("parentPort.postMessage({ type: 'stopped', elapsed });", "parentPort.postMessage({ type: 'stopped', elapsed, ...(failure ? { error: failure } : {}) });"),
    ])
    door_text = replace(door.read_text(), [
        ("const { existsSync, readFileSync, writeFileSync } = require('fs');", "const { existsSync, readFileSync } = require('fs');"),
        ("const { Worker } = require('worker_threads');", "const { Worker } = require('worker_threads');\nconst { flushImage } = require('./image_flush');"),
        ("""    if (!entry) {
        return;
    }
    entry.flushQueue = entry.flushQueue.then(() => {
        writeFileSync(imagePath, Buffer.from(entry.sab));
    });""", "    return flushImage(entry, imagePath);"),
        ("""                        flushSabToDisk(self.config.image);
                        trackDoorRunEnd(doorTracking);
                        self._decrementInstances();
                        callback(err);""", """                        const complete = failure => {
                            trackDoorRunEnd(doorTracking);
                            self._decrementInstances();
                            callback(failure);
                        };
                        flushSabToDisk(self.config.image).then(() => complete(err), flushError => {
                            self.client.log.warn({ name: doorName, error: flushError.message,
                                imageCommitted: !!flushError.imageCommitted }, 'v86 image flush failed');
                            complete(err || flushError);
                        });"""),
        ("""                                return finish(null);
                            }

                            case 'error':""", """                                if (msg.error) {
                                    self.client.log.warn({ name: doorName, error: msg.error }, 'v86 worker stopped with error');
                                }
                                return finish(msg.error ? new Error(msg.error) : null);
                            }

                            case 'error':"""),
    ])
    helper = candidate / 'core/v86_door/image_flush.js'
    assert not helper.exists()
    shutil.copyfile(HERE / 'image_flush.js', helper)
    worker.write_text(worker_text)
    door.write_text(door_text)
    staged = {name: sha(candidate / name) for name in (worker_name, door_name, 'core/v86_door/image_flush.js')}
    meta['fixture_inputs'].update(staged)
    meta['input_shutdown'] = dict(original=original, staged=staged, stager_sha256=sha(Path(__file__)),
        scope='Controlled serial-input failure travels with stopped/image transfer; menu completion awaits atomic image flush, failed attempts remain retryable. No process-crash or live deployment claim.')
    marker.write_text(json.dumps(meta, indent=2) + '\n')
    (candidate / 'v86-input-shutdown.json').write_text(json.dumps(meta['input_shutdown'], indent=2) + '\n')
    print('Staged controlled-error transfer and awaited atomic disk flush')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    stage(parser.parse_args().candidate)
