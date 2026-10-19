#!/usr/bin/env python3
"""Checked native filename policy, including the maintained overflow guard."""
import ctypes,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/aspect-script-path'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 subprocess.run(['cc','-std=c89','-Wall','-Wextra','-Werror','-shared','-fPIC',
  str(ROOT/'src/aspect/script_path.c'),'-o',str(OUT/'script_path.so')],check=True)
 lib=ctypes.CDLL(str(OUT/'script_path.so'));fn=lib.aspect_script_path
 fn.argtypes=[ctypes.c_char_p,ctypes.c_void_p];fn.restype=ctypes.c_uint
 # Expected tuples transcribed from retained D4D0 rules, not from this resolver.
 cases=[(None,2,None),(b'',2,None),(b'login',0,b'LOGIN.ASX'),
  (b'login.asx',0,b'LOGIN.ASX'),(b'login.asp',1,b'LOGIN.ASP'),
  (b'C:\\BBS.V2\\LOGIN',0,b'C:\\BBS.V2\\LOGIN.ASX'),
  (b'C:LOGIN',0,b'C:LOGIN.ASX'),(b'12345678',0,b'12345678.ASX'),
  (b'123456789',3,None),(b'.ASX',3,None),(b'X.',3,None),
  (b'X.ASX.BAK',3,None),(b'X.ASP ',3,None),(b'X.exe',3,None),
  (b'X.ASPX',3,None),(b'C:\\',3,None),(b'C:',3,None),
  (b'LONGDIR/LOGIN',3,None),(b'A/B',0,b'A/B.ASX'),
  (b'game\\\x82a',0,b'GAME\\\x82A.ASX'),(b'A B',0,b'A B.ASX'),
  (b'foo:bar',0,b'FOO:BAR.ASX'),(b'X..ASX',3,None)]
 # The local82-byte bound allows77+4+NUL; native would overflow at78.
 for length in range(75,82):
  name=b'A'*(length-2)+b'\\X'
  cases.append((name,0 if length<=77 else 4,name+b'.ASX' if length<=77 else None))
 for length in range(77,82):
  name=b'A'*(length-6)+b'\\X.ASX'
  cases.append((name,0 if length<=80 else 4,name if length<=80 else None))
 checks=0
 for raw,status,expected in cases:
  for alias in (False,True):
   buf=ctypes.create_string_buffer(128);ctypes.memset(buf,0xA5,128)
   if alias and raw is not None:
    ctypes.memmove(buf,raw+b'\0',len(raw)+1);arg=ctypes.cast(buf,ctypes.c_char_p)
   else:arg=raw
   before=buf.raw;actual=fn(arg,buf);checks+=1
   assert actual==status,(raw,actual,status)
   if expected is None:assert buf.raw==before,raw
   else:
    assert buf.value==expected,(raw,buf.value,expected)
    assert buf.raw[len(expected)+1:]==before[len(expected)+1:],raw
   checks+=1
 assert fn(b'X',None)==3;checks+=1
 sources=['src/aspect/script_path.c','src/aspect/script_path.h','standalone/test_aspect_script_path.py']
 report=dict(cases=len(cases),checks=checks,passed=True,
  sources={p:sha(ROOT/p) for p in sources},
  scope='Host C filename normalization and bounds; retained D4D0 rules, not original runtime or DOS file resolution. Native unchecked extension overflow deliberately rejected.')
 (OUT/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
