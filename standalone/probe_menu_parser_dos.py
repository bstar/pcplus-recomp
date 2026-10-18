#!/usr/bin/env python3
"""Actual DOS controlled split-CSI/menu-entry diagnostic with read-only guards.

This deliberately observes application words through the BIOS TSR. It is a
reproducer, not an original/native equivalence or uninstrumented BBS result.
"""
import argparse,hashlib,json,re,struct,subprocess,sys
from pathlib import Path
from test_connection_dos import run,ROOT,BINARY
sys.path.insert(0,str(ROOT/'lab/bbs'))
from menu_guard_probe import FIELDS

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);p.add_argument('--sha256',required=True);p.add_argument('--expect',choices=['refused','deferred'],default='refused');a=p.parse_args()
 assert a.label and all(c.isalnum() or c in '-_' for c in a.label)
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert digest==a.sha256
 out=ROOT/'build/menu-parser-probe'/a.label;out.mkdir(parents=True,exist_ok=False)
 manifest=json.loads((ROOT/'build/terminal/manifest.json').read_text());assert manifest['binary_sha256']==digest
 listing=(ROOT/'build/terminal/terminal.map').read_text()
 symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 near=manifest['memory_layout']['near_relative_segment'];offsets={n:s*16+o-near*16 for n in FIELDS for s,o in [symbols[n]]}
 assert all(0<=v<manifest['data_stack_bytes']-1 for v in offsets.values())
 include='%define GUARD_COUNT '+str(len(FIELDS))+'\n%define GUARD_OFFSETS dw '+','.join(str(offsets[n]) for n in FIELDS)+'\n'
 (out/'menu-guards.inc').write_text(include)
 source=ROOT/'standalone/menu_guard_watch.asm'
 subprocess.run(['nasm','-fbin','-I',str(out)+'/',str(source),'-o',str(out/'MGWATCH.COM')],check=True)
 name='parser-menu-'+a.label;folder=ROOT/'build/connection-dos'/name;assert not folder.exists()
 proof=run(name,'success','p2000 a-z p300 right p300 right p1500 escape p500 r e a d y p500 a-x',
  files={'MGWATCH.COM':(out/'MGWATCH.COM').read_bytes()},observer='MGWATCH',
  online_updates=[(.4,b'\x1b['),(2.1,b'31mPARTIAL\r\n\x1b[6n')])
 raw=(folder/'MGUARD.BIN').read_bytes();magic,version,size,n,count,overflow=struct.unpack_from('<6H',raw)
 assert magic==0x474d and version==1 and n==len(FIELDS) and size==16+n*2+8+240 and len(raw)==12+size*32 and not overflow
 records=[]
 for i in range(count):
  at=12+i*size;key,low,high,ip,cs,ds,ss,bp=struct.unpack_from('<8H',raw,at);assert ds==ss and cs+near==ds
  values=dict(zip(FIELDS,struct.unpack_from('<'+str(n)+'H',raw,at+16)));chars=at+16+n*2+8
  records.append(dict(key=key,ticks=high*65536+low,guards=values,title=raw[chars:chars+80].decode('cp437'),header=raw[chars+80:chars+160].decode('cp437')))
 wire=(folder/'serial.bin').read_bytes();altz=[r for r in records if r['key']==0x2c00]
 checks=dict(harness_passed=proof['passed'],actual_AltZ_during_parser=len(altz)==1 and altz[0]['guards']['terminal_parser_active']==1,
  actual_remote_CPR_after_split=b'\x1b[2;1R' in wire,ordinary_keyboard_resumed=b'ready' in wire)
 if a.expect=='refused':checks.update(menu_refused=bool(altz) and not any('Command Menu' in r['title'] for r in records),following_arrow_keys_reached_wire=wire.count(b'\x1b[C')==2)
 else:checks.update(menu_opened_after_parser=any(r['key']&255==27 and r['guards']['_command_menu_active']==1 and 'Command Menu' in r['title'] for r in records),
  queued_arrow_keys_not_sent=b'\x1b[C' not in wire)
 result=dict(reproduced=all(checks.values()),expected_behavior=a.expect,binary_sha256=digest,checks=checks,records=records,case=proof,offsets=offsets,
  sources={str(s.relative_to(ROOT)):hashlib.sha256(s.read_bytes()).hexdigest() for s in [Path(__file__),source,ROOT/'lab/bbs/menu_guard_probe.py',ROOT/'standalone/test_connection_dos.py']},
  scope='Controlled partial CSI delayed1.7s; actual production DOS/BIOS/UART. Map-bound read-only guard observation. Expected refusal or deferred entry is explicit. This tests the parser-busy refusal class, not the cause of an earlier unobserved BBS refusal.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert result['reproduced']

if __name__=='__main__':main()
