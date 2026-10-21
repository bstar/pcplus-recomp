#!/usr/bin/env python3
"""Check the isolated EOF-position patch and compile its exact source function.

The function probe uses declared fixture layout and logging/purge callbacks;
it does not establish the full upstream struct ABI or a real transfer.
"""
import argparse,ctypes as C,json,subprocess
from pathlib import Path
from synthmodem_vm_control import ROOT,sha


class State(C.Structure):
 _fields_=[('rxd_header_pos',C.c_uint32),('current_file_size',C.c_uint64),('ack_file_pos',C.c_uint32),('current_file_pos',C.c_uint64)]


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline-helper',type=Path,required=True);p.add_argument('--candidate-helper',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 before=a.baseline_helper.resolve();after=a.candidate_helper.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 base=before.parent.parent/'share/sexyz-source';candidate=after.parent.parent/'share/sexyz-source'
 manifest=json.loads((candidate/'eof-position-manifest.json').read_text())
 assert manifest['upstream_commit']=='e7a825704ef5329c7ef8408749671291a85ef7f2'
 assert sha(base/'zmodem.c')==manifest['before_sha256'] and sha(candidate/'zmodem.c')==manifest['after_sha256']
 assert sha(ROOT/'tools/patch-sexyz-eof-position.py')==manifest['patcher_sha256']
 assert sha(candidate/'send-credit-manifest.json')==manifest['credit_manifest_sha256']
 assert (base/'send-credit-manifest.json').read_bytes()==(candidate/'send-credit-manifest.json').read_bytes()
 assert (base/'source-manifest.json').read_bytes()==(candidate/'source-manifest.json').read_bytes()
 names={q.name for q in base.iterdir() if q.suffix in ('.c','.h')}
 assert names=={q.name for q in candidate.iterdir() if q.suffix in ('.c','.h')}
 assert [n for n in sorted(names) if (base/n).read_bytes()!=(candidate/n).read_bytes()]==['zmodem.c']
 original=(base/'zmodem.c').read_text();changed=(candidate/'zmodem.c').read_text()
 head='\nBOOL zmodem_handle_zrpos(';tail='\nBOOL zmodem_handle_zack('
 assert original[:original.index(head)]==changed[:changed.index(head)]
 assert original[original.index(tail):]==changed[changed.index(tail):]
 def function(text):return text[text.index(head)+1:text.index(tail)]
 support='''#include <stdint.h>
#include <inttypes.h>
typedef int BOOL;
typedef unsigned long ulong;
#define TRUE 1
#define FALSE 0
#define LOG_INFO 1
#define LOG_WARNING 2
typedef struct {
 uint32_t rxd_header_pos; uint64_t current_file_size;
 uint32_t ack_file_pos; uint64_t current_file_pos;
} zmodem_t;
unsigned logs, purges, timeout;
void lprintf(zmodem_t* z,int level,const char* text,...)
{ (void)z; (void)level; (void)text; ++logs; }
void zmodem_recv_purge(zmodem_t* z,unsigned t)
{ (void)z; ++purges; timeout=t; }
'''
 code=out/'guard.c';code.write_text(support+function(original).replace('zmodem_handle_zrpos','baseline')+function(changed).replace('zmodem_handle_zrpos','candidate'))
 library=out/'guard.so';subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-shared','-fPIC',str(code),'-o',str(library)],check=True)
 lib=C.CDLL(str(library));rows=[]
 for size in (0,1,2,65535,65536,65797,0xffffffff,0x100000000):
  for request in sorted({0,1,max(0,size-1),size,size+1}):
   if request>0xffffffff:continue
   for initial in sorted({0,request,size+11}):
    for purge in (0,3):
     results=[]
     for name in ('baseline','candidate'):
      fn=getattr(lib,name);fn.argtypes=[C.POINTER(State),C.POINTER(C.c_uint64),C.c_uint]
      for field,value in [('logs',0),('purges',0),('timeout',0x7777)]:C.c_uint.in_dll(lib,field).value=value
      state=State(request,size,0xa5a5,19);position=C.c_uint64(initial);result=fn(C.byref(state),C.byref(position),purge)
      valid=request<size if name=='baseline' else request<=size
      assert result==int(valid)
      assert position.value==(request if valid else initial)
      assert state.ack_file_pos==(request if valid and initial!=request else 0xa5a5)
      assert state.rxd_header_pos==request and state.current_file_size==size and state.current_file_pos==19
      assert C.c_uint.in_dll(lib,'purges').value==int(valid)
      assert C.c_uint.in_dll(lib,'timeout').value==(purge if valid else 0x7777)
      assert C.c_uint.in_dll(lib,'logs').value==(int(initial!=request) if valid else 1)
      results.append(result)
     assert (results[0]!=results[1])==(request==size)
     rows.append(dict(size=size,requested=request,initial=initial,purge_timeout=purge,baseline_accepted=bool(results[0]),candidate_accepted=bool(results[1]),passed=True))
 result=dict(passed=True,case_count=len(rows),cases=rows,only_handle_zrpos_changed_from_credit_candidate=True,
  baseline_helper_sha256=sha(before),candidate_helper_sha256=sha(after),patch_manifest=manifest,
  source_files={n:sha(candidate/n) for n in sorted(names)},
  inputs={str(q.relative_to(ROOT)):sha(q) for q in [Path(__file__).resolve(),ROOT/'tools/patch-sexyz-eof-position.py',ROOT/'nix/sexyz-send-credit-eof.nix',ROOT/'tools/build-sexyz-send-credit-eof']},
  generated_probe_sha256=sha(code),library_sha256=sha(library),scope=__doc__)
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,case_count=len(rows))))


if __name__=='__main__':main()
