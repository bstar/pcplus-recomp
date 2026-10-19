#!/usr/bin/env python3
"""Build the DOS expression/operand fragment diagnostic; no original input."""
import json,subprocess
from pathlib import Path
from build_aspect_compiler_lexer import ROOT,sha
OUT=ROOT/'build/aspect-compiler-expression'
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 names=['compiler_lexer.c','compiler_lexer.h','compiler_unit.c','compiler_unit.h','compiler_decimal.c','compiler_decimal.h','compiler_expr.c','compiler_expr.h','compiler_output.c','compiler_output.h','compiler_emit.c','compiler_emit.h','compiler_expression_dump.c','compiler_expression_dump.h','compiler_expression_probe.c']
 sources=[ROOT/'src/aspect'/name for name in names]
 subprocess.run(['wcl','-q','-bt=dos','-0','-ml','-fpc','-ecc','-s','-w4','-we','-k32768','-fm=ASPEXP.map','-fe=ASPEXP.EXE',*[str(p) for p in sources if p.suffix=='.c']],cwd=OUT,check=True)
 sources.extend([Path(__file__),ROOT/'standalone/build_aspect_compiler_lexer.py'])
 report=dict(binary_sha256=sha(OUT/'ASPEXP.EXE'),sources={str(p.relative_to(ROOT)):sha(p) for p in sources},original_inputs=[],platform='8086 DOS large-model C, software floating point,32768B stack',scope='Expression parsing, typed operands/assignment and short-circuit ASX fragments in a developer diagnostic. No statement/command compiler, full ASX program or runtime ASP compilation.')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('ASPEXP.EXE',report['binary_sha256'])
if __name__=='__main__':main()
