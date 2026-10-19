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
               *[ROOT / 'src/aspect' / name for name in ['runner.c', 'runtime.c', 'runtime.h', 'file_io.c', 'file_io.h',
                   'serial_runtime.c','serial_runtime.h','receive_runtime.c','receive_runtime.h','directory_runtime.c','directory_runtime.h','serial.c','serial.h','serial_handoff.h','resident_render.c','resident_render.h']],
               ROOT/'reconstruction/translation/receive.asm', ROOT / 'reconstruction/uart/encodings.inc',ROOT/'reconstruction/uart/layout.inc',
               ROOT/'src/config/resource_path.c',ROOT/'src/config/resource_path.h',
               ROOT/'reconstruction/directory_accounting/patch.asm']
    serial_asm=[('uart','reconstruction/uart/core.asm','UART_OMF'),('uart_api','src/uart/api.asm',None),
                ('serial_backend','src/aspect/serial_backend.asm',None),
                ('resident_client','src/aspect/resident_render_client.asm',None)]
    for name, relative, define in ASM+serial_asm:
        source, obj = ROOT / relative, OUT / (name + '.obj')
        sources.append(source)
        subprocess.run(['nasm', '-f', 'obj', include] + (['-D' + define] if define else []) +
                       (['-DASPECT_RUNTIME_SERIAL'] if name=='bridge' else []) +
                       [str(source), '-o', str(obj)], check=True)
        objects.append(str(obj))
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-ecc', '-s', '-w4', '-we', '-k8192','-dASPECT_RUNTIME_SERIAL',
                    '-i=' + str(ROOT / 'src/aspect'), '-fm=ASPECT.map', '-fe=ASPECT.EXE',
                    str(ROOT / 'src/aspect/runner.c'), str(ROOT / 'src/aspect/runtime.c'),
                    str(ROOT / 'src/aspect/file_io.c'),str(ROOT/'src/aspect/serial_runtime.c'),str(ROOT/'src/aspect/receive_runtime.c'),
                    str(ROOT/'src/aspect/serial.c'),str(ROOT/'src/aspect/directory_runtime.c'),str(ROOT/'src/aspect/resident_render.c'),str(ROOT/'src/config/resource_path.c'), *objects], cwd=OUT, check=True)
    result = dict(binary_sha256=sha(OUT / 'ASPECT.EXE'), original_inputs=[],
                  sources={str(p.relative_to(ROOT)): sha(p) for p in sources},
                  platform='8086 DOS, small model, near DS=SS, cdecl, 8192-byte stack',
                  diagnostic_build=False,
                  scope='DOS CLI for trusted source-compiled ASX; partial63-slot runtime. Optional owned UART with validated parent ASIO handback; native TRANSMIT/WAITFOR with raw receive backend. No complete script/UI scheduling or arbitrary-bytecode safety.')
    (OUT / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print('ASPECT.EXE', result['binary_sha256'])


if __name__ == '__main__':
    main()
