#!/usr/bin/env python3
"""Native integer conversions, optional exact original replay and actual8086 DOS."""
import argparse,hashlib,json,os,re,shutil,struct,subprocess
from pathlib import Path
from unicorn import UC_HOOK_INTR
from unicorn.x86_const import *
from dos_image import DosImage
from build_aspect_conversion_services import ROOT,OUT,SHA,UNITS
class DivideFault(Exception):pass
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def image(native=False):
 m=DosImage(OUT/'CONVERT.EXE',OUT/'conversion.map')
 if not native:return m
 b=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes();assert hashlib.sha256(b).hexdigest()==SHA
 old=m.data_base;data=bytes(m.uc.mem_read(old,65536));m.ds=0x4000;m.data_base=0x40000;m.uc.mem_write(m.data_base,data)
 for name,at in list(m.symbols.items()):
  if old<=at<old+65536:m.symbols[name]=m.data_base+at-old
 for name,start,end,digest in UNITS:
  raw=b[0x1200+start:0x1200+end];assert hashlib.sha256(raw).hexdigest()==digest and raw==(OUT/(name+'.bin')).read_bytes()
  m.uc.mem_write(m.base+start,raw);at=m.symbols['aspect_conversion_'+name]
  m.uc.mem_write(at,b'\xe9'+struct.pack('<H',(m.base+start-at-3)&65535))
 at=m.symbols['aspect_conversion_format_tail'];m.uc.mem_write(at,b'\xe9'+struct.pack('<H',(m.base+0xa5f4-at-3)&65535))
 return m

def parse(data):
 at=0
 while at<len(data) and data[at]in (9,32):at+=1
 negative=at<len(data) and data[at]==45
 if at<len(data) and data[at]in(43,45):at+=1
 value=0
 while at<len(data) and 48<=data[at]<=57:value=(value*10+data[at]-48)&0xffffffff;at+=1
 return (-value if negative else value)&0xffffffff

def formatted(value,radix,bits):
 value&=(1<<bits)-1;negative=radix==10 and bool(value&(1<<(bits-1)))
 if negative:value=(-value)&((1<<bits)-1)
 out=[]
 while True:
  value,remainder=divmod(value,radix);byte=(remainder+48)&255
  if byte>57:byte=(byte+39)&255
  out.append(byte)
  if not value:break
 return (b'-'if negative else b'')+bytes(reversed(out))

def cpu(native=False):
 m=image(native);groups=[];checksum=hashlib.sha256();total=0
 assert m.call('_conversions_dos_test',limit=30000000)==0
 cv=m.get('_vectors');ca=m.get('_assertions',4);assert not m.get('_failures')
 groups.append(dict(case='actual-C-independent-parse-format-span-oracles',vectors=cv,assertions=ca))
 source=m.offset('_source');reject=m.offset('_reject');buffer=m.offset('_buffer')
 def call(name,args):
  nonlocal total
  value=m.call('aspect_conversion_'+name,args,limit=200000)
  for reg,want in ((UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678),(UC_X86_REG_DS,m.ds),(UC_X86_REG_SS,m.ds)):assert m.uc.reg_read(reg)==want,(name,reg)
  assert not m.uc.reg_read(UC_X86_REG_EFLAGS)&0x400
  total+=1;return value
 start=total
 strings=[bytes([v])+b'123'for v in range(256)]
 strings += [b' \t'+sign+str(v).encode()+suffix for sign in (b'',b'+',b'-')for v in (0,1,32767,32768,65535,65536,2147483647,2147483648,4294967295,4294967296,18446744073709551615)for suffix in (b'',b'junk',b'.5')]
 for data in strings:
  m.uc.mem_write(m.data_base+source,data+b'\0');want=parse(data.split(b'\0')[0])
  for name in ('atoi','atol'):
   low=call(name,[source]);actual=(m.uc.reg_read(UC_X86_REG_DX)<<16)|low;assert actual==want,(name,data,actual,want);checksum.update(struct.pack('<I',actual))
 groups.append(dict(case='all256-leadingbytes-SP-TAB-only-sign-prefix-garbage-and32bit-wrap-boththunks',vectors=total-start))
 start=total
 values=list(range(256))+[32767,32768,65535,65536,0x7fffffff,0x80000000,0xffffffff]
 for bits,name in ((16,'itoa'),(32,'ltoa')):
  for value in values:
   for radix in (2,8,10,16,36):
    m.uc.mem_write(m.data_base+buffer,b'\xa5'*100);ptr=buffer+4
    args=[value&65535,ptr,radix]if bits==16 else [value&65535,value>>16,ptr,radix]
    assert call(name,args)==ptr;want=formatted(value,radix,bits)
    actual=bytes(m.uc.mem_read(m.data_base+buffer,100));assert actual==b'\xa5'*4+want+b'\0'+b'\xa5'*(95-len(want)),(name,value,radix,actual,want)
    checksum.update(want+b'\0')
 groups.append(dict(case='signed-decimal-unsigned-nondecimal-zero-extrema-and-buffer-canaries',vectors=total-start))
 start=total
 # Outside conventional2..36 support: characterize real byte-digit arithmetic
 # without claiming portable strings; some bases can emit embedded NUL bytes.
 for bits,name in ((16,'itoa'),(32,'ltoa')):
  for value in (0,36,127,208,255,256,65535,0xffffffff):
   for radix in (37,64,128,255,256,257,65535):
    ptr=buffer+4;m.uc.mem_write(m.data_base+buffer,b'\xa5'*100)
    args=[value&65535,ptr,radix]if bits==16 else[value&65535,value>>16,ptr,radix]
    assert call(name,args)==ptr;want=formatted(value,radix,bits)
    actual=bytes(m.uc.mem_read(m.data_base+buffer,100));assert actual==b'\xa5'*4+want+b'\0'+b'\xa5'*(95-len(want));checksum.update(want+b'\0')
 groups.append(dict(case='nonstandard-radix37-through65535-actual-byte-arithmetic-not-portable-contract',vectors=total-start))
 start=total
 full=bytes(range(1,256));m.uc.mem_write(m.data_base+source,full+b'\0')
 for value in range(1,256):
  m.uc.mem_write(m.data_base+reject,bytes([value,0]));actual=call('strcspn',[source,reject]);assert actual==value-1;checksum.update(struct.pack('<H',actual))
 m.uc.mem_write(m.data_base+reject,b'\0');assert call('strcspn',[source,reject])==255
 m.uc.mem_write(m.data_base+reject,full+b'\0');assert call('strcspn',[source,reject])==0
 groups.append(dict(case='strcspn-all255-bitmap-positions-empty-and-full-reject-set',vectors=total-start))
 invalid=[]
 for name,bits in (('itoa',16),('ltoa',32)):
  z=image(native);ptr=z.offset('_buffer')+4;z.uc.mem_write(z.data_base+z.offset('_buffer'),b'\xa5'*100)
  def interrupt(u,n,d):
   if n==0:raise DivideFault()
   raise AssertionError(('Unexpected interrupt',n))
  z.uc.hook_add(UC_HOOK_INTR,interrupt)
  args=[1,ptr,0]if bits==16 else[1,0,ptr,0]
  try:z.call('aspect_conversion_'+name,args,limit=2000)
  except DivideFault:pass
  else:raise AssertionError('Native radix0 unexpectedly avoids divide fault')
  z=image(native);ptr=z.offset('_buffer')+4;z.uc.mem_write(z.data_base+z.offset('_buffer'),b'\xa5'*100)
  args=[1,ptr,1]if bits==16 else[1,0,ptr,1]
  try:z.call('aspect_conversion_'+name,args,limit=200)
  except AssertionError:assert not z.returned
  else:raise AssertionError('Native radix1 nonzero unexpectedly returned')
  actual=bytes(z.uc.mem_read(z.data_base+z.offset('_buffer'),100));assert actual[:4]==b'\xa5'*4 and actual[40:]==b'\xa5'*60
  invalid.append(dict(service=name,radix0='CPU dividefault',radix1='nonreturn within200instructions; output stays inside-owned-buffer canaries; never DOS tested'))
 return dict(groups=groups,direct_vectors=total,c_selfcheck_vectors=cv,c_selfcheck_assertions=ca,semantic_sha256=checksum.hexdigest(),unsafe_radix_characterizations=invalid)

def dos():
 run=OUT/'dos';run.mkdir(exist_ok=True);shutil.copy2(OUT/'CONVERT.EXE',run/'CONVERT.EXE')
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
CONVERT > RESULT.TXT
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
 text=(run/'RESULT.TXT').read_text();match=re.search(r'CONVERSION PASS vectors=(\d+) assertions=(\d+) failures=0',text)
 assert code==0 and match and(run/'PASS.OK').exists()and not(run/'FAIL.TXT').exists(),text
 return dict(passed=True,vectors=int(match[1]),assertions=int(match[2]),stdout=text,original_inputs=[],scope='Source-built CONVERT.EXE in actual8086 DOSBox-X; only conventional validradix2..36, no original executable run')

def main():
 p=argparse.ArgumentParser();p.add_argument('--original',action='store_true');args=p.parse_args()
 manifest=json.loads((OUT/'manifest.json').read_text());assert sha(OUT/'CONVERT.EXE')==manifest['binary_sha256']
 for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,('Rebuild source',name)
 linked=cpu();native=cpu(True)if args.original else None
 if native is not None:assert linked==native,'Original/source semantics differ'
 actual_dos=dos();assert actual_dos['vectors']==linked['c_selfcheck_vectors']and actual_dos['assertions']==linked['c_selfcheck_assertions']
 result=dict(passed=True,binary_sha256=manifest['binary_sha256'],manifest_sha256=sha(OUT/'manifest.json'),checker_sha256=sha(Path(__file__)),manifest=manifest,cpu=linked,native=native,dos=actual_dos,original_inputs=[dict(path='analysis/pcplus-originals/PCPLUS-main-2.01.EXE',sha256=SHA,usage='Read-only exact7unit/nativeinstructioncomparison; neverDOSexecuted')]if args.original else[],limitations=['No bounds/error guard is added to native CRT: callers own valid terminated buffers and formatting capacity.','Only conventional2..36 radix supported as live contract; native0dividefault/1nonreturn are bounded CPU characterizations and never run in DOS.','Nonstandardradices are characterized as raw-byte arithmetic, potentially embeddedNUL, not portable Cstring conversions.','Original replay uses exact native bodies and relocated entry bridges; no product callback or floatingpoint approximation is substituted.'])
 path=OUT/('checks-native.json'if args.original else'checks.json');path.write_text(json.dumps(result,indent=2)+'\n');print('PASS',linked['direct_vectors'],'direct CPU,',actual_dos['vectors'],'DOS vectors/',actual_dos['assertions'],'assertions',path)
if __name__=='__main__':main()
