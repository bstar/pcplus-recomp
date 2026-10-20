#!/usr/bin/env python3
"""Rebuild normal, experimental and fault-diagnostic DOS products from source."""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import uuid
from build_aspect_process import ROOT, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', default='source-' + uuid.uuid4().hex)
    parser.add_argument('--mouse', action='store_true')
    args = parser.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)
    folder = ROOT / ('build/aspect-unwind-mouse/source-proofs' if args.mouse else 'build/aspect-unwind/source-proofs') / args.label
    folder.mkdir(parents=True, exist_ok=False)
    source = folder / 'source'
    sources = {}
    names = ['terminal-process', 'aspect-process-parent', 'aspect-fault',
             'aspect-process', 'aspect-compiler-dos', 'aspect-runner']
    if args.mouse:names += ['terminal-mouse', 'terminal-mouse-process']
    for name in names:
        manifest = json.loads((ROOT / 'build' / name / 'manifest.json').read_text())
        for path, digest in manifest['sources'].items():
            assert path not in sources or sources[path] == digest, path
            sources[path] = digest
    for name, digest in sources.items():
        path = Path(name)
        assert not path.is_absolute() and '..' not in path.parts
        assert path.parts[0] not in ('analysis', 'build')
        assert sha(ROOT / path) == digest, name
        target = source / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, target)
    assert not (source / 'build').exists() and not (source / 'analysis').exists()
    code = '''import sys,subprocess
from pathlib import Path
sys.path.insert(0,'standalone')
import build_aspect_compiler_dos as compiler
import build_aspect_process as process
import build_aspect_runner as runner
root=Path.cwd()
compiler.main()
process.main(parent_render=True)
process.main(root/'standalone/aspect_fault_driver.c',parent_render=True,output=root/'build/aspect-fault')
process.main(root/'standalone/aspect_process_diagnostic.c')
runner.main()
subprocess.run([sys.executable,'standalone/build_terminal.py','--external-render'],check=True)
subprocess.run([sys.executable,'standalone/build_terminal.py'],check=True)
'''
    if args.mouse:
        code += "subprocess.run([sys.executable,'standalone/build_terminal.py','--mouse'],check=True)\nsubprocess.run([sys.executable,'standalone/build_terminal.py','--mouse','--external-render'],check=True)\n"
    with (folder / 'build.log').open('w') as log:
        result = subprocess.run([sys.executable, '-c', code], cwd=source,
                                stdout=log, stderr=log, timeout=300)
    products = ['aspect-process-parent/ASPECT.EXE', 'aspect-fault/ASPECT.EXE',
                'aspect-process/ASPECT.EXE', 'aspect-runner/ASPECT.EXE',
                'aspect-compiler-dos/ASPCOMP.EXE', 'terminal-process/TERMINAL.EXE',
                'terminal/TERMINAL.EXE', 'native-program/PROGRAM.EXE',
                'native-program/OWN1.COM', 'native-program/OWN2.COM',
                'native-display/DISPLAY.EXE', 'native-display/VIDEO.COM',
                'process-serial/PSERIAL.EXE', 'process-serial/UART1.COM',
                'process-serial/UART2.COM', 'native-process/NATIVE.EXE',
                'native-process/NAMES.EXE']
    products += ['native-process/' + name for name in json.loads(
        (ROOT / 'build/native-process/manifest.json').read_text())['children']]
    if args.mouse:products += ['terminal-mouse/TERMINAL.EXE', 'terminal-mouse-process/TERMINAL.EXE']
    compared = {name: dict(expected=sha(ROOT / 'build' / name),
                           actual=sha(source / 'build' / name))
                for name in products} if not result.returncode else {}
    report = dict(passed=not result.returncode and len(compared) == (29 if args.mouse else 27) and
                  all(p['expected'] == p['actual'] for p in compared.values()),
                  original_inputs=[], experimental_mouse=args.mouse, source_files=len(sources), sources=sources,
                  products=compared, exit_code=result.returncode,
                  checker_sha256=sha(Path(__file__)), log_sha256=sha(folder / 'build.log'),
                  scope='Fresh declared-source tree: normal products, compiler, capability7 parent/child, raw diagnostic, fault diagnostic and20 process components. No originals, previous objects or REA databases.')
    (folder / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Fresh unwind source:', len(compared), 'products',
          'PASS' if report['passed'] else 'FAIL', folder)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
