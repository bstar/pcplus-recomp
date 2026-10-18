#!/usr/bin/env python3
"""Maintained metadata codec: independent Python oracle, host fuzz, real8086 DOS.
No original executable/install, file IO callbacks, framing or protocol fixtures.
"""
import ctypes as C,hashlib,json,os,random,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/batch-header';SRC=ROOT/'src/transfer'
class Result(C.Structure):
 _fields_=[('name',C.c_char*13),('kind',C.c_ubyte),('flags',C.c_ushort),('size',C.c_uint32),('mtime',C.c_uint32),('mode',C.c_uint32),('serial',C.c_uint32),('extension_offset',C.c_ushort),('extension_length',C.c_ushort)]
def valid_name(name):
 try:text=name.decode('ascii')
 except UnicodeDecodeError:return False
 if not re.fullmatch(r"[A-Za-z0-9!#$%&'()\-@^_`{}~]{1,8}(?:\.[A-Za-z0-9!#$%&'()\-@^_`{}~]{1,3})?",text):return False
 stem=text.split('.')[0].upper()
 return stem not in {'CON','PRN','AUX','NUL','CLOCK$'} and not re.fullmatch(r'(COM|LPT)[1-9]',stem)
def oracle(raw):
 if len(raw) not in (128,1024):return 1,None
 try:n=raw.index(0)
 except ValueError:return 3,None
 if n==0:return (3,None) if any(raw) else (0,dict(name=b'',kind=2,flags=0,values=[0]*4,ext=(0,0)))
 if not valid_name(raw[:n]):return 2,None
 try:end=raw.index(0,n+1)
 except ValueError:return 3,None
 if any(raw[end+1:]):return 3,None
 meta=raw[n+1:end];tokens=meta.split(b' ') if meta else [];values=[0]*4;flags=0;ext=(0,0)
 for i,t in enumerate(tokens):
  if not t or any(c<33 or c>126 for c in t):return 3,None
  if i<4:
   if not re.fullmatch(b'[0-9]+' if i==0 else b'[0-7]+',t):return 3,None
   v=int(t,10 if i==0 else 8)
   if v>0xffffffff:return 4,None
   values[i]=v;flags|=1<<i
  elif i==4:
   pos=n+1+sum(len(t)+1 for t in tokens[:4]);ext=(pos,end-pos);flags|=16
 return 0,dict(name=raw[:n],kind=1,flags=flags,values=values,ext=ext)
def block(name=b'TEST.BIN',metadata=b'123',size=128):
 data=name+b'\0'+metadata+b'\0';assert len(data)<=size;return data.ljust(size,b'\0')
DOS=r'''
#include "batch_header.h"
#include <stdio.h>
#include <string.h>
static unsigned char b[1024],before[1024];static batch_header_result r,old;
static unsigned checks,failures;
static void ck(unsigned good,const char *label){++checks;if(!good)++failures;if(!good || checks<17)printf("%s %s\n",good?"PASS":"FAIL",label);}
int main(void){
 unsigned i,s;FILE *f;
 ck(sizeof(r)==36,"fixed36 byte nearC ABI");
 ck(batch_header_encode("aBc-1234.Bin",13,0xffffffffUL,b,128)==0 && !memcmp(b,"aBc-1234.Bin\0004294967295\000",23),"maxDWORD decimal casepreserved encoder");
 ck(batch_header_decode(b,128,&r)==0 && r.kind==BH_FILE && r.flags==BH_LENGTH && r.size==0xffffffffUL,"DWORD decode");
 memset(b,0,1024);memcpy(b,"TEST.BIN",8);strcpy((char *)b+9,"6347 3314742513 100644 17 extra=a future");
 ck(batch_header_decode(b,1024,&r)==0 && r.flags==31 && r.size==6347 && r.mtime==03314742513UL && r.mode==0100644 && r.serial==017 && r.extension_length==14,"knownoctal plusopaquefuture1024");
 memset(b,0,128);memcpy(b,"TEST.BIN",8);ck(batch_header_decode(b,128,&r)==0 && !r.flags && !r.size,"absent size distinctzero");
 ck(batch_header_encode("X",2,0,b,128)==0 && batch_header_decode(b,128,&r)==0 && r.flags==1 && !r.size,"explicitzero known");
 ck(batch_header_end(b,128)==0 && batch_header_decode(b,128,&r)==0 && r.kind==BH_END && !r.flags,"allzero end batch");
 memset(&r,0x77,sizeof(r));old=r;b[127]=1;ck(batch_header_decode(b,128,&r)==BH_FORMAT && !memcmp(&r,&old,sizeof(r)),"invalid endtail atomic");
 memset(b,0xa5,1024);memcpy(before,b,1024);ck(batch_header_encode("CON.txt",8,1,b,128)==BH_NAME && !memcmp(b,before,1024),"reserveddevice rejected atomically");
 ck(batch_header_encode("X",2,1,(unsigned char *)0xff90,128)==BH_ARGUMENT,"near outputwrap");
 ck(batch_header_decode((unsigned char *)0xfe00,1024,&r)==BH_ARGUMENT,"near inputwrap");
 ck(batch_header_decode(b,128,(batch_header_result *)0xfff0)==BH_ARGUMENT,"near resultwrap");
 ck(batch_header_decode(b,128,(batch_header_result *)b)==BH_ARGUMENT,"decode overlap");
 ck(batch_header_encode((char *)b,13,1,b,128)==BH_ARGUMENT,"encode overlap");
 ck(batch_header_decode(0,128,&r)==BH_ARGUMENT && batch_header_end(0,128)==BH_ARGUMENT,"null guarded");
 ck(batch_header_end(b,1024)==BH_ARGUMENT,"encoder restricted128");
 ck(batch_header_encode((const char *)0xfff8,13,1,b,128)==BH_ARGUMENT,"near namewrap");
 ck(batch_header_encode("X",0,1,b,128)==BH_ARGUMENT && batch_header_encode("X",65,1,b,128)==BH_ARGUMENT,"name capacity bounds");
 memset(b,0xa5,1024);memcpy(before,b,1024);ck(batch_header_encode("ABCDEFGHIJKLM",13,1,b,128)==BH_NAME && !memcmp(b,before,1024),"unterminated boundedname atomic");
 ck(batch_header_decode(b,127,&r)==BH_ARGUMENT && batch_header_decode(b,129,&r)==BH_ARGUMENT,"decoder exact block extents");
 f=fopen("VECTORS.BIN","rb");if(!f)return 2;i=0;
 while(fread(b,1,130,f)==130){s=b[128]|((unsigned)b[129]<<8);memset(&r,0x77,sizeof(r));old=r;ck(batch_header_decode(b,128,&r)==s && (!s || !memcmp(&r,&old,sizeof(r))),"independent oracle vector status/atomicity");++i;}
 fclose(f);ck(i>20,"independent oracle corpus executed");
 printf("BATCHHEADER %u checks %u failures\n",checks,failures);return failures?1:0;
}
'''
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 subprocess.run(['gcc','-std=c89','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-fPIC','-shared',str(SRC/'batch_header.c'),'-o',str(OUT/'header.so')],cwd=ROOT,check=True)
 lib=C.CDLL(str(OUT/'header.so'));lib.batch_header_encode.argtypes=[C.c_void_p,C.c_uint,C.c_uint32,C.c_void_p,C.c_uint];lib.batch_header_decode.argtypes=[C.c_void_p,C.c_uint,C.c_void_p];lib.batch_header_end.argtypes=[C.c_void_p,C.c_uint]
 assert C.sizeof(Result)==36 and Result.size.offset==16
 vectors=[bytes(128),block(metadata=b''),block(metadata=b'0'),block(metadata=b'4294967295'),block(metadata=b'6347 3314742513 100644'),block(metadata=b'1 0 0 17'),block(metadata=b'1 0 0 17 opaque=alpha next'),block(b'mIx.Bin',b'0001'),block(metadata=b'1 37777777777 37777777777 37777777777')]
 for name in [b'',b'CON',b'con.txt',b'LPT9.bin',b'COM1',b'CLOCK$',b'..',b'/X',b'C:X',b'A\\B',b'LONGER123.BIN',b'A.ABCD',b'X.',b'a b',b'\xff']:
  vectors.append(block(name,b'1'))
 for meta in [b'-1',b'+1',b'4294967296',b'18446744073709551616',b'1 8',b'1 40000000000',b'1 1 1 8',b' 1',b'1 ',b'1  0',b'1\t0',b'1 0 0 0 future\x1f',b'0000000000000000000000000000001']:
  vectors.append(block(metadata=meta))
 vectors += [block(metadata=b'1 0'),block(metadata=b'1 0 0 0 '+b'X'*(128-9-8-1)),block(metadata=b'1 0 0 0 '+b'X'*(1024-9-8-1),size=1024),b'X'*128, b'X\0'+b'1'*126,block()+b'\0',bytes(127),block()[:-1]+b'X',block(size=1024,metadata=b'1 0 0 0 '+b'x'*900)]
 rng=random.Random(1988)
 for _ in range(1500):
  r=bytearray(rng.choice(vectors[:40]));r[rng.randrange(len(r))]=rng.randrange(256);vectors.append(bytes(r))
 checks=0;dos_vectors=[]
 for raw in vectors:
  expected,info=oracle(raw);buf=C.create_string_buffer(raw);r=Result();C.memset(C.addressof(r),0x77,36);prior=bytes(r)
  got=lib.batch_header_decode(buf,len(raw),C.byref(r));assert got==expected,(raw,got,expected)
  if got:assert bytes(r)==prior
  else:
   assert bytes(r.name)==info['name'] and r.kind==info['kind'] and r.flags==info['flags']
   assert [r.size,r.mtime,r.mode,r.serial]==info['values'] and (r.extension_offset,r.extension_length)==info['ext']
  checks+=1
  if len(raw)==128 and len(dos_vectors)<200:dos_vectors.append(raw+expected.to_bytes(2,'little'))
 for name in [b'X',b'abcdefgh.xyz',b'MiXeD.Bin',b'CON.txt',b'',b'bad/path',b'ABC.DEF.G']:
  for size in [0,1,127,65535,65536,2147483648,4294967295]:
   b=C.create_string_buffer(b'\xa5'*128,128);before=bytes(b);n=C.create_string_buffer(name);s=lib.batch_header_encode(n,len(name)+1,size,b,128)
   assert s==(0 if valid_name(name) else 2)
   assert bytes(b)==(block(name,str(size).encode()) if not s else before);checks+=1
 # Guard declarations and disjointness through actual linked C.
 b=C.create_string_buffer(1024);r=Result();assert lib.batch_header_decode(b,128,b)==1
 assert lib.batch_header_encode(b,13,1,b,128)==1
 assert lib.batch_header_decode(None,128,C.byref(r))==1
 assert lib.batch_header_end(b,1024)==1
 checks+=4
 for cap in [0,65]:
  before=bytes(b);assert lib.batch_header_encode(C.create_string_buffer(b'X'),cap,1,b,128)==1 and bytes(b)==before;checks+=1
 for cap in [0,127,129,1023]:
  before=bytes(r);assert lib.batch_header_decode(b,cap,C.byref(r))==1 and bytes(r)==before;checks+=1
 for name in [b'A'*12,b'A'*64]:
  before=bytes(b);n=C.create_string_buffer(name,len(name));assert lib.batch_header_encode(n,len(name),1,b,128)==2 and bytes(b)==before;checks+=1
 for cap in [0,127,129,1024]:
  before=bytes(b);assert lib.batch_header_end(b,cap)==1 and bytes(b)==before;checks+=1
 (OUT/'VECTORS.BIN').write_bytes(b''.join(dos_vectors))
 subprocess.run(['python3',str(ROOT/'standalone/build_batch_header.py')],cwd=ROOT,check=True)
 for name in ['PASS.TXT','FAIL.TXT','RESULT.TXT']:(OUT/name).unlink(missing_ok=True)
 conf=f'''[sdl]\noutput=surface\n[cpu]\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nHEADER >RESULT.TXT\nif errorlevel 1 goto fail\necho PASS>PASS.TXT\ngoto done\n:fail\necho FAIL>FAIL.TXT\n:done\nexit\n'''
 (OUT/'dosbox.conf').write_text(conf)
 with (OUT/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=30)
 text=(OUT/'RESULT.TXT').read_text();print(text);assert (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),text
 result=dict(passed=True,host_oracle_checks=checks,DOS_oracle_vectors=len(dos_vectors),DOS_summary=text.splitlines()[-1],binary_sha256=hashlib.sha256((OUT/'HEADER.EXE').read_bytes()).hexdigest(),sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [SRC/'batch_header.c',SRC/'batch_header.h',Path(__file__).resolve()]},scope='Maintained metadata codec only. Independent Python oracle, linked host C, source-built8086 DOS and near span/overlap diagnostics. No transfer engine, framing, filesystem timestamps/modes or original executable inputs.')
 (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
