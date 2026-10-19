#!/usr/bin/env python3
"""Build the maintained DOS compiler without original or host compiler inputs."""
import json,subprocess
from pathlib import Path
from build_aspect_compiler_lexer import ROOT,sha
OUT=ROOT/'build/aspect-compiler-dos'
MODULES=['compiler_lexer','compiler_unit','compiler_decimal','compiler_expr','compiler_output','compiler_emit','compiler_commands','compiler_program']
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 sources=[ROOT/'src/aspect'/(name+suffix) for name in MODULES for suffix in ('.c','.h') if (ROOT/'src/aspect'/(name+suffix)).exists()]
 sources.extend([ROOT/'src/aspect/compiler_program_internal.h',ROOT/'src/aspect/compiler_main.c'])
 subprocess.run(['wcl','-q','-bt=dos','-0','-ml','-fpc','-ecc','-s','-w4','-we','-k32768','-fm=ASPCOMP.map','-fe=ASPCOMP.EXE',*[str(p) for p in sources if p.suffix=='.c']],cwd=OUT,check=True)
 sources.extend([Path(__file__),ROOT/'standalone/build_aspect_compiler_lexer.py'])
 report=dict(binary_sha256=sha(OUT/'ASPCOMP.EXE'),sources={str(p.relative_to(ROOT)):sha(p) for p in sources},original_inputs=[],platform='8086 DOS large-model C, integer-only decimal conversion,32768B stack',scope='Maintained host grammar port producing complete ASX programs with staged CLI publication. Runtime ASP integration and original compiler families beyond the maintained host remain unfinished.')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('ASPCOMP.EXE',report['binary_sha256'])
if __name__=='__main__':main()
