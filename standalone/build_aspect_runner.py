#!/usr/bin/env python3
"""Build the maintained DOS ASPECT CLI without original or fixture inputs."""
import json
from pathlib import Path
import subprocess
from build_aspect_runtime import ROOT, ASM, sha

OUT = ROOT / 'build/aspect-runner'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    include = '-I' + str(ROOT / 'reconstruction/uart') + '/'
    objects = []
    sources = [Path(__file__).resolve(), ROOT / 'standalone/build_aspect_runtime.py',
               *[ROOT / 'src/aspect' / name for name in ['runner.c', 'runtime.c', 'runtime.h', 'file_io.c', 'file_io.h']],
               ROOT / 'reconstruction/uart/encodings.inc']
    for name, relative, define in ASM:
        source, obj = ROOT / relative, OUT / (name + '.obj')
        sources.append(source)
        subprocess.run(['nasm', '-f', 'obj', include] + (['-D' + define] if define else []) +
                       [str(source), '-o', str(obj)], check=True)
        objects.append(str(obj))
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-w4', '-we', '-k8192',
                    '-i=' + str(ROOT / 'src/aspect'), '-fm=ASPECT.map', '-fe=ASPECT.EXE',
                    str(ROOT / 'src/aspect/runner.c'), str(ROOT / 'src/aspect/runtime.c'),
                    str(ROOT / 'src/aspect/file_io.c'), *objects], cwd=OUT, check=True)
    result = dict(binary_sha256=sha(OUT / 'ASPECT.EXE'), original_inputs=[],
                  sources={str(p.relative_to(ROOT)): sha(p) for p in sources},
                  platform='8086 DOS, small model, near DS=SS, cdecl, 8192-byte stack',
                  diagnostic_build=False,
                  scope='DOS CLI for trusted source-compiled ASX; partial57-slot runtime. MESSAGE raw DOS stdout and BIOS Escape cancellation, PAUSE uses native BIOS clock. No terminal serial bindings or arbitrary-bytecode safety.')
    (OUT / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print('ASPECT.EXE', result['binary_sha256'])


if __name__ == '__main__':
    main()
