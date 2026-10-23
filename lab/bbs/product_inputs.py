"""Resolve explicit source-built products for owned BBS integration probes."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def select_product(path, leaf):
    binary = path.resolve()
    assert binary.is_relative_to(ROOT / 'build') and binary.name == leaf
    manifest_path = binary.parent / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    assert not manifest.get('original_inputs')
    assert sha(binary) == manifest['binary_sha256']
    sources = [manifest_path, Path(__file__)]
    for name, digest in manifest['sources'].items():
        relative = Path(name)
        assert not relative.is_absolute() and '..' not in relative.parts
        assert relative.parts[0] not in ('build', 'original', 'originals', 'install', 'analysis')
        assert sha(ROOT / relative) == digest, name
        sources.append(ROOT / relative)
    return binary, sources
