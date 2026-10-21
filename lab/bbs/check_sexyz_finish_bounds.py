#!/usr/bin/env python3
"""Real receiver closing owner with modeled byte/clock/cancel boundaries."""
import argparse,ctypes as C,hashlib,json,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'standalone'))
from check_zmodem import h

PROBE=r'''
#include "genwrap.h"
#include "dirwrap.h"
#include "zmodem.h"
#include "receive_finish.h"
#include <string.h>
typedef struct { unsigned status,used,polls,cancelled; uint64_t elapsed; } result;
static const unsigned char *wire;
static unsigned length,used,polls,step,flags;
static uint64_t now;
uint64_t xp_timer64(void) {
 if (flags&1) return UINT64_MAX;
 if ((flags&2) && used) return 999999;
 return now;
}
static BOOL connected(void *ctx) { (void)ctx;return !((flags&4) && used>=2); }
static BOOL canceled(void *ctx) { (void)ctx;return !!((flags&8) && used>=2); }
static int input(void *ctx,unsigned seconds) {
 (void)ctx;
 if (seconds!=1) return 256;
 ++polls;
 if (used==length) { now+=1000; return -1; }
 now+=step;
 return wire[used++];
}
void probe(const unsigned char *bytes,unsigned n,unsigned timeout,unsigned pace,unsigned fault,result *out) {
 zmodem_t zm;memset(&zm,0,sizeof(zm));memset(out,0,sizeof(*out));
 wire=bytes;length=n;used=polls=0;step=pace;flags=fault;now=1000000;
 zm.recv_timeout=timeout;zm.recv_byte=input;zm.is_connected=connected;zm.is_cancelled=canceled;
 zm.local_abort=!!(flags&16);
 out->status=loc_receive_finish(&zm);out->used=used;out->polls=polls;
 out->cancelled=zm.cancelled;out->elapsed=now-1000000;
}
'''

class Result(C.Structure):
 _fields_=[(n,C.c_uint) for n in ('status','used','polls','cancelled')]+[('elapsed',C.c_uint64)]


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();source=a.source.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 module=ROOT/'lab/bbs/patches/sexyz-receive-finish';(out/'probe.c').write_text(PROBE)
 includes=[source] if (source/'zmodem.h').is_file() else [source/d for d in ('src/sbbs3','src/xpdev','src/hash')]
 command=['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-shared','-fPIC',
  *['-I'+str(d) for d in includes],'-I'+str(module),'-I'+str(ROOT/'src/transfer'),
  str(out/'probe.c'),str(module/'receive_finish.c'),str(ROOT/'src/transfer/zmodem_wire.c'),'-o',str(out/'probe.so')]
 subprocess.run(command,check=True)
 lib=C.CDLL(str(out/'probe.so'));lib.probe.argtypes=[C.c_void_p,*[C.c_uint]*4,C.POINTER(Result)]
 bad=bytearray(h(8));bad[-3]=ord('0') if bad[-3]!=ord('0') else ord('1')
 cases=[('literal-OO-retains-app',b'OOAPP',True,10,0,0),
  ('flow-between-Os',b'O\x11\x93OAPP',True,10,0,0),
  ('queued-hex-FIN-and-ABORT',h(8)+h(7)+b'OOAPP',True,10,0,0),
  ('queued-binary-closing',h(8,0,65)+h(7,0,67)+b'OOAPP',True,10,0,0),
  ('nine-closing-headers',h(8)*9+b'OOAPP',True,10,0,0),
  ('ten-closing-headers-bounded',h(8)*10+b'OOAPP',False,10,0,0),
  ('bad-CRC-not-OO',bytes(bad)+b'OOAPP',False,10,0,0),
  ('nonzero-position-rejected',h(8,1)+b'OOAPP',False,10,0,0),
  ('unrelated-header-rejected',h(4)+b'OOAPP',False,10,0,0),
  ('noise-containing-OO-rejected',b'NOISEOOAPP',False,10,0,0),
  ('wrong-second-O-rejected',b'OXOOAPP',False,10,0,0),
  ('raw-five-CAN-cancels',b'\x18'*5,False,10,0,0),
  ('missing-OO-timeout',b'',False,10,0,0),
  ('single-O-timeout',b'O',False,10,0,0),
  ('byte-ceiling-for-endless-flow',b'\x11'*1000,False,10,0,0),
  ('trickle-does-not-reset-deadline',b'\x11'*200+b'OO',False,10,100,0),
  ('OO-at-deadline-rejected',b'OO',False,1,500,0),
  ('zero-timeout-clamped',b'',False,0,0,0),
  ('huge-timeout-clamped',b'',False,0xffffffff,0,0),
  ('clock-error-rejected',b'OO',False,10,0,1),
  ('backward-clock-rejected',b'OO',False,10,0,2),
  ('disconnect-during-second-O',b'OO',False,10,0,4),
  ('cancel-during-second-O',b'OO',False,10,0,8),
  ('local-abort-before-input',b'OO',False,10,0,16)]
 rows=[]
 for name,wire,wanted,timeout,pace,flags in cases:
  result=Result();buffer=C.create_string_buffer(wire);lib.probe(buffer,len(wire),timeout,pace,flags,C.byref(result))
  assert bool(result.status)==wanted,(name,result.status)
  assert result.used<=512 and result.elapsed<=61000,(name,result.used,result.elapsed)
  if wanted:assert wire[result.used:]==b'APP',name
  if 'cancels' in name or 'cancel-during' in name or 'local-abort' in name:assert result.cancelled,name
  if name=='missing-OO-timeout':assert result.elapsed==10000
  if name=='huge-timeout-clamped':assert result.elapsed==60000
  if name=='trickle-does-not-reset-deadline':assert result.elapsed==10000 and result.used==100
  rows.append({'case':name,'passed':True,'status':result.status,'consumed':result.used,'polls':result.polls,'modeled_elapsed_ms':result.elapsed,'cancelled':bool(result.cancelled)})
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 report={'passed':True,'cases':rows,'checker_sha256':sha(Path(__file__)),
  'upstream_header_sha256':{name:sha(next(d/name for d in includes if (d/name).is_file())) for name in ['genwrap.h','dirwrap.h','zmodem.h']},
  'module_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [module/'receive_finish.c',module/'receive_finish.h',ROOT/'src/transfer/zmodem_wire.c',ROOT/'src/transfer/zmodem_wire.h']},
  'scope':'Actual candidate receive-finish C owner and maintained codec, real pinned upstream zmodem_t ABI. Only byte input, monotonic clock and cancellation/disconnect callbacks modeled. Independent Python CRC/header vectors, exact APP suffix, bounded retries/flow/noise/timeout and fail-closed clocks. Not actual helper subprocess, DOS, audio, BBS or physical acceptance.'}
 (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print('Passed',len(rows),'receiver closing bound cases')


if __name__=='__main__':main()
