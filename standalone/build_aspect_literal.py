#!/usr/bin/env python3
"""Build an8086 DOS ASPECT literal diagnostic from maintained sources/vectors."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/aspect-literal'
VECTORS = ROOT / 'standalone/fixtures/aspect_literal_vectors.json'

DOS = r'''
#include "literal.h"
#include <stdio.h>
#include <string.h>
#include "vectors.h"
static unsigned checks,failures;
static unsigned char plain[100],wire[100],saved[100];
static aspect_literal_result result,before;
static void ck(unsigned condition){++checks;if(!condition){++failures;printf("FAIL %u\n",checks);}}
int main(void){
 unsigned i,j,n;FILE *f;
 ck(sizeof(aspect_u32)==4 && sizeof(result)==6);
 for(i=0;i<sizeof(vectors)/sizeof(vectors[0]);++i){
  n=vectors[i].length;
  ck(aspect_literal_encode(vectors[i].plain,n,vectors[i].position,vectors[i].line,wire,100,&result)==0);
  ck(result.text_length==n && result.wire_length==n+2 && !memcmp(wire,vectors[i].wire,n+2));
  memset(plain,0xcc,100);
  ck(aspect_literal_decode(wire,n+2,vectors[i].position,plain,100,&result)==0);
  ck(result.text_length==n && !memcmp(plain,vectors[i].plain,n) && plain[n]==0xcc);
  for(j=0;j<n+2;++j){
   memset(plain,0xcc,100);memcpy(saved,plain,100);memset(&result,0x77,sizeof(result));before=result;
   ck(aspect_literal_decode(wire,j,vectors[i].position,plain,100,&result)==ASPECT_LITERAL_TRUNCATED);
   ck(!memcmp(plain,saved,100) && !memcmp(&result,&before,sizeof(result)));
  }
 }
 ck(aspect_literal_encode((unsigned char *)0xfff0,32,4,2,wire,100,&result)==ASPECT_LITERAL_ARGUMENT);
 ck(aspect_literal_encode((unsigned char *)"A",1,4,2,(unsigned char *)0xffff,3,&result)==ASPECT_LITERAL_ARGUMENT);
 ck(aspect_literal_encode((unsigned char *)"A",1,4,2,wire,100,(aspect_literal_result *)0xfffd)==ASPECT_LITERAL_ARGUMENT);
 ck(aspect_literal_decode((unsigned char *)0xfffe,3,4,plain,100,&result)==ASPECT_LITERAL_ARGUMENT);
 ck(aspect_literal_encode((unsigned char *)"AB",2,4,2,wire,100,&result)==0);
 ck(aspect_literal_decode(wire,4,4,(unsigned char *)0xffff,100,&result)==ASPECT_LITERAL_ARGUMENT);
 ck(aspect_literal_encode(plain,1,4,2,plain,100,&result)==ASPECT_LITERAL_ARGUMENT);
 ck(aspect_literal_encode(0,1,4,2,wire,100,&result)==ASPECT_LITERAL_ARGUMENT);
 ck(aspect_literal_encode(plain,0,4,2,wire,100,&result)==ASPECT_LITERAL_RANGE);
 ck(aspect_literal_encode(plain,81,4,2,wire,100,&result)==ASPECT_LITERAL_RANGE);
 ck(aspect_literal_encode((unsigned char *)"A",1,4,2,wire,2,&result)==ASPECT_LITERAL_TRUNCATED);
 ck(aspect_literal_encode((unsigned char *)"A",1,0xffffffffUL,2,wire,100,&result)==0 && wire[1]==0x83 && wire[2]==0x36);
 f=fopen("DONE.TXT","w");if(!f)return 2;fprintf(f,"ASPECT_LITERAL %u checks %u failures\n",checks,failures);fclose(f);
 printf("ASPECT_LITERAL %u checks %u failures\n",checks,failures);return failures?1:0;
}
'''


def byte_array(data):
    return '{' + ','.join(str(x) for x in data) + '}'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    vectors = json.loads(VECTORS.read_text())['vectors']
    rows = []
    for v in vectors:
        plain, wire = bytes.fromhex(v['text_hex']), bytes.fromhex(v['wire_hex'])
        rows.append('{%d,%dUL,%dUL,%s,%s}' % (len(plain), v['payload_offset'], v['source_line'], byte_array(plain), byte_array(wire)))
    (OUT / 'vectors.h').write_text('static const struct { unsigned length; aspect_u32 position,line; unsigned char plain[80],wire[82]; } vectors[]={\n' + ',\n'.join(rows) + '\n};\n')
    (OUT / 'diagnostic.c').write_text(DOS)
    subprocess.run(['wcl', '-q', '-bt=dos', '-0', '-ms', '-s', '-w4', '-we', '-k8192',
        '-i=' + str(ROOT / 'src/aspect'), '-fm=LITERAL.map', '-fe=LITERAL.EXE',
        str(ROOT / 'src/aspect/literal.c'), str(OUT / 'diagnostic.c')], cwd=OUT, check=True)
    sources = [ROOT / 'src/aspect/literal.c', ROOT / 'src/aspect/literal.h', VECTORS, Path(__file__).resolve()]
    manifest = dict(binary_sha256=hashlib.sha256((OUT / 'LITERAL.EXE').read_bytes()).hexdigest(),
        sources={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        original_inputs=[], scope='Source-only8086 literal codec diagnostic; frozen source-owned compiler-oracle vectors, no original executable/install input')
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Built LITERAL.EXE', manifest['binary_sha256'])


if __name__ == '__main__':
    main()
