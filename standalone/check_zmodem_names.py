#!/usr/bin/env python3
"""Independent alias oracle and actual engine identity/collision regressions."""
import ctypes as C
import hashlib
import json
from pathlib import Path
import random
import subprocess
import zlib
from check_batch_header import Result,valid_name
from check_zmodem import Fixture,h,offer,payload
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/zmodem-names'
def alias(name):
 if valid_name(name):return name
 stem,dot,ext=name.rpartition(b'.')
 allowed=b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!#$%&'()-@^_`{}~"
 ext=ext.upper() if stem and dot and 1<=len(ext)<=3 and all(c in allowed for c in ext.upper()) else b'DAT'
 return f'{zlib.crc32(name.upper()):08X}'.encode()+b'.'+ext
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 sources=[ROOT/'src/transfer'/p for p in ('zmodem.c','zmodem_wire.c','zmodem_name.c','batch_header.c')]
 subprocess.run(['gcc','-std=c89','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-shared','-fPIC',*[str(p) for p in sources],'-o',str(OUT/'names.so')],check=True)
 lib=C.CDLL(str(OUT/'names.so'));lib.zm_name_decode.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p];lib.zm_run.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint]
 cases=[]
 def check(name,condition):assert condition,name;cases.append(name)
 def decode(raw,status=0,want=None):
  source=C.create_string_buffer(raw,len(raw));scratch=C.create_string_buffer(b'\xa5'*1024,1024);result=Result();C.memset(C.byref(result),0x77,C.sizeof(result));before=bytes(result)
  got=lib.zm_name_decode(source,len(raw),scratch,C.byref(result));assert got==status,(raw[:40],got,status)
  assert source.raw==raw
  if status:assert bytes(result)==before
  elif want is not None:assert result.name==want,(result.name,want)
  return result
 names=[b'TEST.BIN',b'mIx-1234.ZiP',b'PCPLUS PROBE 01 (1991).ZIP',b'long.name.with.many.parts.zip',b'a b.zip',b'CON.TXT',b'LPT9',b'CLOCK$',b'.hidden',b'.hidden.NFO',b'a'*255,b'a'*250+b'.zip',b'name.abcdef',b'name.?',b'game\xff\xfe.zip']
 rng=random.Random(0x5a4d);names += [bytes(rng.choice(b'ABCDEabcde01234 ._-') for _ in range(n)) for n in (13,31,63,127,255) for _ in range(30)]
 for name in names:
  if name in (b'.',b'..'):continue
  raw=name+b'\0'+b'1301 0 100644 0 opaque=yes\0'
  result=decode(raw,want=alias(name));check('name-'+name.hex(),result.size==1301 and result.flags==31 and result.extension_offset==raw.index(b'opaque=yes'))
 for c in range(1,256):
  name=b'long wire '+bytes([c])+b'.ZIP';raw=name+b'\0' + b'3\0'
  bad=c<32 or c==127 or c in b'/\\:'
  decode(raw,2 if bad else 0,None if bad else alias(name));check('byte-'+str(c),True)
 for raw,status in [(b'',1),(b'A'*256+b'\0' + b'1\0',2),(b'\0' + b'1\0',2),(b'.\0' + b'1\0',2),(b'..\0' + b'1\0',2),(b'../X\0' + b'1\0',2),(b'C:X\0' + b'1\0',2),(b'A\\B\0' + b'1\0',2),(b'TEST.BIN',3),(b'TEST.BIN\0' + b'123',3),(b'long file.zip\0' + b'123',3),(b'long file.zip\0' + b'1\0X',3),(b'long file.zip\0' + b'-1\0',3),(b'long file.zip\0' + b'4294967296\0',4)]:
  if raw:decode(raw,status)
  else:
   source=C.create_string_buffer(1);scratch=C.create_string_buffer(1024);r=Result();assert lib.zm_name_decode(source,0,scratch,C.byref(r))==1
  check('malformed-'+raw.hex(),True)
 for count in (128,1024):
  raw=b'Long Game Title.ZIP\0' + b'42\0';decode(raw.ljust(count,b'\0'),want=alias(b'Long Game Title.ZIP'));check('padded-'+str(count),True)
 # Output/source/scratch overlap is rejected before touching any data.
 buffer=C.create_string_buffer(b'\x77'*2048,2048);r=Result();before=buffer.raw
 check('overlap-block-scratch',lib.zm_name_decode(buffer,128,buffer,C.byref(r))==1 and buffer.raw==before)
 check('overlap-result-scratch',lib.zm_name_decode(buffer,128,C.byref(buffer,128),C.byref(buffer,256))==1 and buffer.raw==before)
 check('overlap-result-source',lib.zm_name_decode(buffer,128,C.byref(buffer,1024),buffer)==1 and buffer.raw==before)
 for fmt in (65,67):
  name='PCPLUS PROBE 01 (1991).ZIP';local=alias(name.encode()).decode();body=bytes(range(256))*5
  rx=offer(name,len(body),fmt)+payload(body[:1024],0,fmt)+offer(name,len(body),fmt)+payload(body[1024:],1024,fmt)+h(11,len(body),fmt)+h(8)+b'OO'
  f=Fixture(lib,rx);check('long-retry-'+str(fmt),f.run()==0 and f.received=={local:body} and sum(e[0]=='open' for e in f.events)==1)
  f=Fixture(lib,offer(name,3,fmt)+payload(b'ABC',0,fmt)+h(11,3,fmt)+offer(name,3,fmt)+h(8)+b'OO')
  check('repeat-existing-skips-'+str(fmt),f.run()==0 and f.session.files==1 and f.session.skipped==1 and f.received=={local:b'ABC'})
 # A real CRC32 alias collision must never merge active wire identities or
 # overwrite a committed target. The checked existing-target skip is explicit.
 a='Game 9P4Ppbwljq4gg3.ZIP';b='Game o6dYr6fHK42eTT.ZIP';local='4F09E7D3.ZIP'
 check('known-collision-oracle',alias(a.encode())==alias(b.encode())==local.encode())
 f=Fixture(lib,offer(a,6)+payload(b'ABC')+offer(b,6))
 check('active-collision-rejects-changed-wire',f.run()==6 and not f.received and sum(e[0]=='open' for e in f.events)==1 and any(e[0]=='abort' for e in f.events))
 f=Fixture(lib,offer(a,3)+payload(b'ABC')+h(11,3)+offer(b,3)+h(8)+b'OO')
 check('committed-collision-skips-without-overwrite',f.run()==0 and f.received=={local:b'ABC'} and f.session.files==1 and f.session.skipped==1)
 report=dict(passed=True,cases=len(cases),case_names=cases,collision=dict(first=a,second=b,alias=local,policy='Active identity mismatch aborts; existing target is explicitly skipped without overwrite'),checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources+[ROOT/'src/transfer/zmodem_name.h',ROOT/'src/transfer/zmodem.h']},scope='Independent Python CRC32/local-name oracle, actual C bounded metadata codec and actual ZMODEM engine with recording transport/storage callbacks. Full wire identity, CRC16/32 retry and collision/skip policy. No DOS filesystem or BBS completion claim from host callbacks.')
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print('ZMODEM names',len(cases),'cases PASS')
if __name__=='__main__':main()
