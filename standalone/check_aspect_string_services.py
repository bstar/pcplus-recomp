#!/usr/bin/env python3
"""CPU and actual8086 DOS service checks; --original adds separate native replay."""
import argparse,hashlib,json,os,re,shutil,struct,subprocess
from pathlib import Path
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import *
from dos_image import DosImage
from build_aspect_string_services import ROOT,OUT,SHA,UNITS,REUSED
SYMBOLS=['aspect_string_'+u[0]for u in UNITS]+[u[0]for u in REUSED]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def image(native=False):
 m=DosImage(OUT/'SERVICES.EXE',OUT/'services.map')
 if not native:return m
 p=ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE';b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==SHA
 old=m.data_base;data=bytes(m.uc.mem_read(old,65536));m.ds=0x4000;m.data_base=m.ds*16;m.uc.mem_write(m.data_base,data)
 for name,at in list(m.symbols.items()):
  if old<=at<old+65536:m.symbols[name]=m.data_base+at-old
 for i,(name,start,end,base,digest) in enumerate(UNITS):
  raw=b[base+start:base+end];assert hashlib.sha256(raw).hexdigest()==digest
  m.uc.mem_write(m.base+start,raw)
  at=m.symbols[SYMBOLS[i]];m.uc.mem_write(at,b'\xe9'+struct.pack('<H',(m.base+start-at-3)&65535))
 for name,path,start,end,_ in REUSED:
  raw=b[0x1200+start:0x1200+end];assert raw==(OUT/(name+'.bin')).read_bytes(),('Reused helper bytes',name);m.uc.mem_write(m.base+start,raw)
  at=m.symbols[name];m.uc.mem_write(at,b'\xe9'+struct.pack('<H',(m.base+start-at-3)&65535))
 for native_at,name in [(0xdd68,'aspect_string_bounded_integer'),(0xde4d,'aspect_expr_integer_address')]:
  at=m.base+native_at;target=m.symbols[name];m.uc.mem_write(at,b'\xe9'+struct.pack('<H',(target-at-3)&65535))
 def alias(u,at,size,_):
  if at in (m.base+0xda0c,m.base+0xda28):u.mem_write(m.data_base+0xd124,struct.pack('<H',m.get('_comparison')))
 m.uc.hook_add(UC_HOOK_CODE,alias);return m

def cpu(native=False):
 m=image(native);groups=[];digest=hashlib.sha256();n=0
 assert m.call('_services_dos_test',limit=15000000)==0
 vectors=m.get('_vectors');assertions=m.get('_assertions',4);assert not m.get('_failures')
 groups.append(dict(case='actual-C-291-vector-CRT-and-wrapper-selfcheck',vectors=vectors,assertions=assertions))
 a=m.offset('_fixture_left');b=m.offset('_fixture_right');buffer=m.offset('_fixture_buffer')
 def direct(index,args,expected=None):
  nonlocal n
  m.uc.reg_write(UC_X86_REG_ES,0xb800)
  value=m.call(SYMBOLS[index],args)
  for reg,want in [(UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds)]:assert m.uc.reg_read(reg)==want,(SYMBOLS[index],reg)
  assert not m.uc.reg_read(UC_X86_REG_EFLAGS)&0x400,'DF must remain clear'
  if expected is not None:assert value==expected,(SYMBOLS[index],args,value,expected)
  n+=1;digest.update(struct.pack('<H',value));return value
 start=n
 for left in range(256):
  for right in (0,1,65,127,128,254,255):
   m.uc.mem_write(m.data_base+a,bytes([left,0,0xcc]));m.uc.mem_write(m.data_base+b,bytes([right,0,0xdd]))
   direct(0,[a,b],65535 if left<right else int(left>right))
 groups.append(dict(case='unsigned-strcmp-all256-versus-seven-boundaries-with-NUL-early-stop-ABI',vectors=n-start))
 start=n
 for alignment in (0,1):
  for count in (0,1,2,3,7,8,31,32,79,80):
   for value in range(256):
    m.uc.mem_write(m.data_base+buffer,b'\xa5'*100);ptr=buffer+8+alignment
    direct(2,[ptr,value,count],ptr)
    actual=bytes(m.uc.mem_read(m.data_base+buffer,100));want=b'\xa5'*(8+alignment)+bytes([value])*count+b'\xa5'*(100-8-alignment-count)
    assert actual==want;digest.update(actual)
 groups.append(dict(case='raw-fill-all256-values-even-odd-counts-zero-and-canaries-ABI',vectors=n-start))
 start=n
 for index,convert in ((1,lambda x:x+32 if 65<=x<=90 else x),(11,lambda x:x-32 if 97<=x<=122 else x)):
  data=bytes(range(1,256))+b'\0\xde\xad';m.uc.mem_write(m.data_base+buffer,data)
  direct(index,[buffer],buffer);out=bytes(m.uc.mem_read(m.data_base+buffer,len(data)))
  assert out==bytes(map(convert,range(1,256)))+b'\0\xde\xad';digest.update(out)
 groups.append(dict(case='ASCII-only-lower-and-reused-upper-highbytes-tail-canaries-ABI',vectors=n-start))
 # Actual bounded wrapper instructions must preserve BP/SI/DI while forwarding
 # min/max and modeled service return, including out-of-range fixture returns.
 start=n
 for index,maximum in ((3,255),(4,79)):
  for value in (0,1,79,80,255,256,65535):
   m.put('_model_return',value);m.put('_bounded_calls',0)
   direct(index,[],value);assert m.get('_bounded_calls')==1 and m.get('_seen_min')==0 and m.get('_seen_max')==maximum
 groups.append(dict(case='byte-index-minmax-and-exact-return-forwarding-to-explicit-fixture',vectors=n-start))
 start=n
 for value in (0,1,2,0x7fff,0x8000,0xffff):
  m.put('_comparison',value);direct(6,[],value);direct(7,[],int(value==0))
 groups.append(dict(case='status21-and-success27-all-representative-word-signs',vectors=n-start))
 return dict(groups=groups,direct_vectors=n,c_selfcheck_vectors=vectors,c_selfcheck_assertions=assertions,semantic_sha256=digest.hexdigest())

def dos():
 run=OUT/'dos';run.mkdir(exist_ok=True);shutil.copy2(OUT/'SERVICES.EXE',run/'SERVICES.EXE')
 for name in ('PASS.OK','FAIL.TXT','RESULT.TXT'):(run/name).unlink(missing_ok=True)
 conf='''[sdl]
output=surface
[dosbox]
memsize=8
[cpu]
core=normal
cputype=8086
cycles=max
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "'''+str(run)+'''"
c:
SERVICES > RESULT.TXT
if errorlevel 1 goto fail
echo PASS>PASS.OK
goto done
:fail
echo FAIL>FAIL.TXT
:done
exit
'''
 (OUT/'dosbox.conf').write_text(conf)
 with (OUT/'dosbox.log').open('w')as log:code=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],cwd=OUT,stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),timeout=90).returncode
 text=(run/'RESULT.TXT').read_text();match=re.search(r'SERVICES PASS vectors=(\d+) assertions=(\d+) failures=0',text)
 assert code==0 and match and (run/'PASS.OK').exists() and not(run/'FAIL.TXT').exists(),text
 return dict(passed=True,vectors=int(match[1]),assertions=int(match[2]),stdout=text,original_inputs=[],scope='Source-built SERVICES.EXE actual8086 DOSBox-X selfcheck, modeled bound/address callbacks; no original executable run')

def main():
 p=argparse.ArgumentParser();p.add_argument('--original',action='store_true');args=p.parse_args()
 manifest=json.loads((OUT/'manifest.json').read_text());assert sha(OUT/'SERVICES.EXE')==manifest['binary_sha256']
 for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,('Rebuild changed source',name)
 linked=cpu();native=cpu(True)if args.original else None
 if native is not None:assert linked==native,'Native/source semantic mismatch'
 actual_dos=dos();assert actual_dos['vectors']==linked['c_selfcheck_vectors'] and actual_dos['assertions']==linked['c_selfcheck_assertions']
 result=dict(passed=True,binary_sha256=manifest['binary_sha256'],manifest_sha256=sha(OUT/'manifest.json'),checker_sha256=sha(Path(__file__)),manifest=manifest,cpu=linked,native=native,dos=actual_dos,original_inputs=[dict(path='analysis/pcplus-originals/PCPLUS-main-2.01.EXE',sha256=SHA,usage='Read-only exact-unit/native-instruction comparison; never DOS-executed')]if args.original else [],limitations=['Only numeric-range and integer-address services are explicit callback fixtures; native parser/error semantics are not thereby recovered.','Inputs own bounded valid near buffers with terminating NUL; undefined scans, overlapping strings and near-wrap not exercised.','Native replay uses exact verified bodies plus callback relocation bridges and mirrored synthetic DS:D124 comparison state.','Reused strncat count0 is tested at normal nonzero-owned addresses; null/DS0 pointers are excluded.'])
 path=OUT/('checks-native.json'if args.original else 'checks.json');path.write_text(json.dumps(result,indent=2)+'\n');print('PASS',linked['direct_vectors'],'direct CPU,',linked['c_selfcheck_vectors'],'C vectors,',actual_dos['assertions'],'DOS assertions;',path)
if __name__=='__main__':main()
