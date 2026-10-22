#!/usr/bin/env python3
"""Bind staged normal/mouse packages to actual DOS compiler/runner receipts."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert args.label and all(c.isalnum() or c in '-_' for c in args.label)
    output=args.output.resolve();assert output.is_relative_to(ROOT/'docs/validation') and not output.exists()
    rows={}
    for mouse in (False,True):
        package=ROOT/('build/dos-package-mouse' if mouse else 'build/dos-package')
        folder=ROOT/('build/package-mouse-tests' if mouse else 'build/package-tests')/args.label
        report=read(folder/'result.json');manifest=read(package/'manifest.json')
        assert report['passed'] and all(report['checks'].values()) and len(report['checks'])==6
        assert report['checker_sha256']==sha(ROOT/'standalone/test_package_mouse.py')
        assert report['sampler_sha256']==sha(ROOT/'standalone/test_terminal.py')
        assert report['package_manifest_sha256']==sha(package/'manifest.json')
        assert report['files']==manifest['files'] and manifest['original_inputs']==[]
        assert manifest['experimental_mouse']==mouse and len(manifest['files'])==10
        assert {p.name for p in package.iterdir()}==set(manifest['files'])|{'manifest.json'}
        for name,digest in manifest['files'].items():assert sha(package/name)==sha(folder/name)==digest
        for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest
        for name,digest in report['artifacts'].items():assert sha(folder/name)==digest
        for leaf,info in manifest['input_manifests'].items():
            path=ROOT/info['manifest'];assert sha(path)==info['sha256']
            product=read(path);assert product['binary_sha256']==sha(package/leaf)
            for name,digest in product['sources'].items():
                source=Path(name);assert not source.is_absolute() and '..' not in source.parts and source.parts[0] not in ('analysis','build')
                assert sha(ROOT/source)==digest
        assert 'cputype=8086' in (folder/'dosbox.conf').read_text()
        assert (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists()
        assert (folder/'REBUILD.ASX').read_bytes()==(package/'HELLO.ASX').read_bytes()
        assert b'/I:0..32767' in (package/'README.TXT').read_bytes()
        key='mouse' if mouse else 'normal'
        rows[key]=dict(directory=str(package.relative_to(ROOT)),report=str((folder/'result.json').relative_to(ROOT)),report_sha256=sha(folder/'result.json'),manifest_sha256=sha(package/'manifest.json'),files=manifest['files'],checks=report['checks'],input_manifests=manifest['input_manifests'],captures_sha256=report['artifacts'])
    result=dict(passed=True,packages=rows,auditor_sha256=sha(Path(__file__)),scope='Two current source-built DOS package inventories and actual 8086 DOS compilation, bytecode execution and source compile/run of the authored example. Package terminal/mouse interaction, complete distribution and physical hardware require separate evidence.')
    with output.open('x') as stream:stream.write(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,packages=len(rows),DOS_checks=sum(len(r['checks']) for r in rows.values()))))
if __name__=='__main__':main()
