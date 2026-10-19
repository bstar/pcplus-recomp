#!/usr/bin/env python3
"""Actual DOS streaming lexer against the full maintained source corpus."""
import hashlib,json,os,re,shutil,struct,subprocess,sys
from pathlib import Path
from build_aspect_compiler_lexer import ROOT,OUT,sha,main as build
sys.path.insert(0,str(ROOT/'src/aspect'))
import compiler
HARNESS=r'''
#include <stdio.h>
#include <string.h>
#include <process.h>
#include <io.h>
#include <fcntl.h>
#include <sys/stat.h>
#include "compiler_lexer.h"
#include "compiler_lex_dump.h"
static unsigned failed,checks,cases;
static void ck(unsigned ok){++checks;if(!ok)++failed;}
static void cli(const char *input,const char *name,unsigned expected){
 int fd,save,result;fflush(stdout);
 fd=open(name,O_CREAT|O_TRUNC|O_WRONLY|O_BINARY,S_IREAD|S_IWRITE);ck(fd>=0);
 save=dup(1);ck(save>=0);ck(dup2(fd,1)==0);close(fd);
 if(input)result=spawnl(P_WAIT,"ASPLEX.EXE","ASPLEX",input,(char *)0);
 else result=spawnl(P_WAIT,"ASPLEX.EXE","ASPLEX",(char *)0);
 fflush(stdout);ck(dup2(save,1)==0);close(save);ck(result==expected);
 printf("CLI %s exit%d expected%u\n",name,result,expected);
}
static void contracts(void){
 FILE *file;aspect_compiler_reader reader;aspect_compiler_line line;
 unsigned char text[256],before[256];unsigned long position;unsigned saved;
 file=fopen("API.ASP","wb");ck(file!=0);if(!file)return;
 fwrite("ABC=\"A\0B\"\r\n",1,11,file);ck(fclose(file)==0);
 file=fopen("API.ASP","rb");ck(file!=0);if(!file)return;
 ck(aspect_compiler_reader_init(&reader,file)==0);
 ck(aspect_compiler_next_line(&reader,&line)==1);ck(line.number==1 && line.offset==0 && line.count==3);
 memset(text,0xa5,sizeof(text));memcpy(before,text,sizeof(text));
 ck(aspect_compiler_token_copy(&line,0,text,3)==-1);ck(!memcmp(text,before,sizeof(text)));
 ck(aspect_compiler_token_copy(&line,3,text,sizeof(text))==-1);ck(!memcmp(text,before,sizeof(text)));
 ck(aspect_compiler_token_copy(&line,0,text,4)==3);ck(!memcmp(text,"abc\0",4));
 ck(aspect_compiler_token_copy(&line,2,text,sizeof(text))==5);ck(!memcmp(text,"\"A\0B\"\0",6));
 saved=line.tokens[0].start;line.tokens[0].start=254;
 memcpy(before,text,sizeof(text));ck(aspect_compiler_token_copy(&line,0,text,sizeof(text))==-1);
 ck(!memcmp(text,before,sizeof(text)));line.tokens[0].start=saved;
 ck(aspect_compiler_next_line(&reader,&line)==0);position=reader.offset;
 ck(position==11);ck(aspect_compiler_next_line(&reader,&line)==0 && reader.offset==position);
 ck(fclose(file)==0);
 file=fopen("BAD.ASP","wb");ck(file!=0);if(!file)return;fputs("@ trailing",file);ck(fclose(file)==0);
 file=fopen("BAD.ASP","rb");ck(file!=0);if(!file)return;
 ck(aspect_compiler_reader_init(&reader,file)==0);ck(aspect_compiler_next_line(&reader,&line)==-1);
 ck(reader.status==ASPECT_LEX_CHARACTER && reader.error_line==1 && reader.error_offset==0);
 position=(unsigned long)ftell(file);ck(aspect_compiler_next_line(&reader,&line)==-1);
 ck((unsigned long)ftell(file)==position);ck(fclose(file)==0);
 file=fopen("API.ASP","rb");ck(file!=0);if(!file)return;
 ck(aspect_compiler_reader_init(&reader,file)==0);reader.offset=0xffffffffUL;
 ck(aspect_compiler_next_line(&reader,&line)==-1 && reader.status==ASPECT_LEX_POSITION);
 ck(reader.error_offset==0xffffffffUL);ck(fclose(file)==0);
 file=fopen("API.ASP","wb");ck(file!=0);if(!file)return;
 ck(aspect_compiler_reader_init(&reader,file)==0);
 ck(aspect_compiler_next_line(&reader,&line)==-1 && reader.status==ASPECT_LEX_IO);
 ck(fclose(file)==0);
}
int main(void){
 FILE *list,*output,*input;char path[13];unsigned expected;int result;
 list=fopen("CASES.LST","rt");output=fopen("TOKENS.DAT","wb");if(!list||!output)return 99;
 while(fscanf(list,"%12s %u",path,&expected)==2){
  input=fopen(path,"rb");if(!input)return 98;
  result=aspect_compiler_lex_dump(input,output);ck(result==expected);ck(fclose(input)==0);++cases;
 }
 ck(!ferror(list));ck(fclose(list)==0);ck(fclose(output)==0);
 contracts();
'''
EDGE={
 'empty':b'', 'unterminated-last-line':b'PROC MAIN\nENDPROC',
 'mixed-boundaries':b'; first\rPROC MAIN\r\n\n\x0b\x0c\x1c\x1d\x1eENDPROC',
 'CP437-and-comment':b'MeSsAgE "\x82\xff;^M" ; ignored \x01\x00\xfe\n',
 'unicode-space-equivalence':b'\xff\tPROC\x1fMAIN\xff; comment\n',
 'embedded-NUL-literal':b'message "A\0B"\n', 'embedded-NUL-invalid':b'proc\0main\n',
 'SUB-is-not-implicit-EOF':b'proc main\n\x1a\nendproc\n',
 'numeric-prefixes':b'0x 0XfL 0x1E+2 1e+ 1e-2L 1.25E+03 1.2l 123L 00001\n',
 'operator-boundaries':b'++= --= += -= *= /= %= == != <= >= && || () , = + - * / % < >\n',
 'bad-ampersand':b'foo & bar', 'bad-period':b'1.\n', 'unterminated-quote':b'  message "abc',
 'line253':b';'+b'A'*252, 'line254':b';'+b'A'*253,
 'maximum-token-count':b'('*253, 'long-identifier':b'A'*253,
 'line-size-before-comment':b'\n;'+b'A'*253+b'\n',
 'all-CP437-in-quoted-fields':b''.join(b'message "'+bytes([c])+b'"\r\n' for c in range(256) if c not in [10,11,12,13,28,29,30,34]),
 'source-offset-and-line-over64K':b';\n'*65536+b'proc main\r\nmessage "TAIL"\r\nendproc',
}
def word(n):return struct.pack('<H',n)
def dword(n):return struct.pack('<I',n)
def expected(raw):
 output=bytearray(b'ALX1');position=0;lines=tokens=0
 def error(code,number,offset,column):
  output.extend(bytes([255,code])+dword(number)+dword(offset)+word(column))
  return bytes(output),1,lines,tokens
 for number,fragment in enumerate(raw.decode('cp437').splitlines(keepends=True),1):
  text=fragment[:-2] if fragment.endswith('\r\n') else fragment[:-1] if fragment[-1:] in '\r\n\v\f\x1c\x1d\x1e' else fragment
  data=text.encode('cp437')
  if len(data)>253:return error(2,number,position+253,253)
  parsed=[];pos=0
  while pos<len(text):
   rest=text[pos:]
   if not rest.strip() or rest.lstrip().startswith(';'):break
   match=compiler.TOKEN.match(text,pos)
   if not match:
    column=pos
    while column<len(text) and text[column].isspace():column+=1
    return error(3,number,position+column,column)
   token=match.group(1);kind=3 if token.startswith('"') else 2 if token[0].isdigit() else 1 if re.match(r'[A-Za-z_$]',token) else 4
   normalized=(token if kind==3 else token.lower()).encode('cp437')
   parsed.append(bytes([kind])+word(match.start(1))+word(len(normalized))+normalized);pos=match.end()
  output.extend(bytes([1])+dword(number)+dword(position)+word(len(data))+word(len(parsed))+data+b''.join(parsed))
  position+=len(fragment.encode('cp437'));lines+=1;tokens+=len(parsed)
 output.extend(bytes([0])+dword(lines+1)+dword(len(raw)))
 return bytes(output),0,lines,tokens

def source_corpus():
 cases={};fixture_hashes={}
 def add(raw,reference):
  key=hashlib.sha256(raw).hexdigest()
  if key not in cases:cases[key]=dict(raw=raw,references=[])
  cases[key]['references'].append(reference)
 def visit(value,path):
  if isinstance(value,dict):
   if isinstance(value.get('source'),str):add(value['source'].encode('cp437'),path)
   for child in value.values():visit(child,path)
  elif isinstance(value,list):
   for child in value:visit(child,path)
 for path in sorted((ROOT/'standalone/fixtures').glob('aspect*.json')):
  fixture_hashes[str(path.relative_to(ROOT))]=sha(path);visit(json.loads(path.read_text()),str(path.relative_to(ROOT)))
 for name,data in EDGE.items():add(data,'authored:'+name)
 return list(cases.values()),fixture_hashes

def main():
 build();cases,fixture_hashes=source_corpus();folder=OUT/'tests';folder.mkdir(exist_ok=True)
 shutil.copyfile(OUT/'ASPLEX.EXE',folder/'ASPLEX.EXE')
 program=HARNESS;listing='';expected_stream=bytearray();selected={};summaries=[]
 for index,case in enumerate(cases):
  name=f'F{index:05}.ASP';(folder/name).write_bytes(case['raw'])
  data,status,lines,tokens=expected(case['raw']);listing+=f'{name} {status}\n';expected_stream.extend(data)
  summaries.append(dict(name=name,source_sha256=hashlib.sha256(case['raw']).hexdigest(),references=case['references'],status=status,lines=lines,tokens=tokens,output_sha256=hashlib.sha256(data).hexdigest(),output_bytes=len(data)))
  if status not in selected:selected[status]=(name,data)
 (folder/'CASES.LST').write_text(listing)
 for status,(name,data) in selected.items():
  program+=f' cli("{name}","CLI{status}.ALX",{status});\n'
 program+=' cli("NOFILE.ASP","MISSING.ALX",1);cli(0,"USAGE.ALX",64);\n'
 program+=' printf("LEXER %u cases %u checks %u failures\\n",cases,checks,failed);return failed?1:0;}\n'
 (folder/'harness.c').write_text(program)
 subprocess.run(['wcl','-q','-bt=dos','-0','-ml','-ecc','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/aspect'),'-fm=LEXTEST.map','-fe=LEXTEST.EXE',str(folder/'harness.c'),str(ROOT/'src/aspect/compiler_lexer.c'),str(ROOT/'src/aspect/compiler_lex_dump.c')],cwd=folder,check=True)
 for name in ['PASS.TXT','FAIL.TXT','RUN.TXT','TOKENS.DAT']:(folder/name).unlink(missing_ok=True)
 config=f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{folder}"\nc:\nLEXTEST >RUN.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n'
 (folder/'dosbox.conf').write_text(config)
 with (folder/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=180)
 run=(folder/'RUN.TXT').read_text();print(run)
 actual=(folder/'TOKENS.DAT').read_bytes()
 if actual!=expected_stream:
  offset=next((i for i,(a,b) in enumerate(zip(actual,expected_stream)) if a!=b),min(len(actual),len(expected_stream)))
  end=0
  for case in summaries:
   end+=case['output_bytes']
   if offset<end:break
  (OUT/'mismatch.json').write_text(json.dumps(dict(offset=offset,case=case,actual=actual[max(0,offset-8):offset+24].hex(),expected=expected_stream[max(0,offset-8):offset+24].hex()),indent=2)+'\n')
  raise AssertionError((offset,case))
 assert (folder/'PASS.TXT').exists() and not (folder/'FAIL.TXT').exists(),run
 for status,(name,data) in selected.items():assert (folder/f'CLI{status}.ALX').read_bytes()==data
 assert (folder/'MISSING.ALX').read_bytes()==(folder/'USAGE.ALX').read_bytes()==b''
 (OUT/'cases.json').write_text(json.dumps(summaries,indent=2)+'\n')
 report=dict(passed=True,binary_sha256=sha(OUT/'ASPLEX.EXE'),manifest_sha256=sha(OUT/'manifest.json'),checker_sha256=sha(Path(__file__)),host_compiler_sha256=sha(ROOT/'src/aspect/compiler.py'),fixture_sources=fixture_hashes,case_count=len(cases),accepted_lexically=sum(c['status']==0 for c in summaries),rejected_lexically=sum(c['status']==1 for c in summaries),line_count=sum(c['lines'] for c in summaries),token_count=sum(c['tokens'] for c in summaries),DOS_summary=run.strip().splitlines()[-1],tokens_sha256=sha(folder/'TOKENS.DAT'),tokens_bytes=len(actual),case_manifest_sha256=sha(OUT/'cases.json'),authored_edges=list(EDGE),original_inputs=[],scope='Actual DOS8086 large-model C lexer over real binary FILE streams, complete maintained source corpus plus boundary/CP437/error/over64KiB cases. Exact token bytes, offsets and physical lines compared with existing host regex. Parser, symbol/procedure passes, ASX emission and runtime source compilation remain unimplemented.')
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if isinstance(v,(str,int,bool))},indent=2))
if __name__=='__main__':main()
