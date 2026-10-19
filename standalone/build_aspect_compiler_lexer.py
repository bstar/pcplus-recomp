#!/usr/bin/env python3
"""Build the DOS compiler lexer diagnostic without originals or fixtures."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-compiler-lexer'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 names=['compiler_lexer.c','compiler_lexer.h','compiler_lex_dump.c','compiler_lex_dump.h','compiler_lex_probe.c']
 sources=[ROOT/'src/aspect'/name for name in names]
 subprocess.run(['wcl','-q','-bt=dos','-0','-ml','-ecc','-s','-w4','-we','-k8192','-fm=ASPLEX.map','-fe=ASPLEX.EXE',*[str(p) for p in sources if p.suffix=='.c']],cwd=OUT,check=True)
 sources.append(Path(__file__))
 report=dict(binary_sha256=sha(OUT/'ASPLEX.EXE'),sources={str(p.relative_to(ROOT)):sha(p) for p in sources},original_inputs=[],platform='8086DOS large-model C,8192B stack, borrowed binary FILE streams',scope='Streaming compiler lexer diagnostic; no declarations, grammar, procedure pass, ASX emission or runtime source compilation yet.')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('ASPLEX.EXE',report['binary_sha256'])
if __name__=='__main__':main()
