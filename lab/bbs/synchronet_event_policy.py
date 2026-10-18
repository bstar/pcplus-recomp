#!/usr/bin/env python3
"""Disable scheduled events in the owned loopback lab, preserving stock flags.

NO_EVENTS stops execution but pinned Synchronet data.cpp:getnextevent() still
considers forced events unless EVENT_DISABLED(1<<3) is set in each event config.
No account time limits, editor implementation or external BBS is modified.
Restart the owned loopback listener afterwards; this helper does not kill it.
"""
import argparse,hashlib,json,re,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/'build/bbs-lab/synchronet/runtime/ctrl/xtrn.ini'
def sha(data):return hashlib.sha256(data).hexdigest()
def disable(text):
 section='';changed=[];out=[]
 for line in text.splitlines(keepends=True):
  match=re.match(r'\[([^]]+)\]',line)
  if match:section=match.group(1)
  match=re.match(r'(\s*settings\s*=\s*)(0x[0-9a-fA-F]+|\d+)(\s*)$',line)
  if section.lower().startswith('event:') and match:
   before=int(match.group(2),0);after=before|8
   if before!=after:changed.append(dict(section=section,before=before,after=after));line=match.group(1)+hex(after)+match.group(3)
  out.append(line)
 return ''.join(out),changed
def self_check():
 before='[event:A]\n settings=0x44003\n cmd=unchanged\n[other]\n settings=2\n[event:B]\n settings=8\n[event:C]\n settings=0\n'
 expected='[event:A]\n settings=0x4400b\n cmd=unchanged\n[other]\n settings=2\n[event:B]\n settings=8\n[event:C]\n settings=0x8\n'
 after,changes=disable(before)
 assert after==expected
 assert all(c['before'] ^ c['after']==0x8 for c in changes)
 assert [c['section'] for c in changes]==['event:A','event:C']
 assert disable(after)==(after,[])
 assert disable('[other]\n settings=0x44003\n')==('[other]\n settings=0x44003\n',[])
 print('Source-only event policy self-check PASS: mask0x8(bit3), all other flags/non-event text preserved, already-disabled unchanged, idempotent; no configuration read or changed')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');p.add_argument('--self-check',action='store_true');a=p.parse_args()
 if a.self_check:self_check();return
 before=CONFIG.read_bytes();after,changes=disable(before.decode());after=after.encode();report=dict(config=str(CONFIG.relative_to(ROOT)),before_sha256=sha(before),after_sha256=sha(after),changed=changes,applied=False,scope='Owned loopback lab event policy only; EVENT_DISABLED mask0x8 (bit3) added while all other event flags, account quotas and editor code remain unchanged.',native_server_source='build/bbs-lab/synchronet/source/src/sbbs3/data.cpp getnextevent skips EVENT_DISABLED; sbbsdefs.h EVENT_DISABLED=1<<3')
 if a.apply and changes:
  out=ROOT/'build/bbs-lab/synchronet/event-policy'/str(time.time_ns());out.mkdir(parents=True,exist_ok=False);(out/'xtrn.ini.before').write_bytes(before);CONFIG.write_bytes(after);(out/'xtrn.ini.after').write_bytes(after);report['applied']=True;report['artifact_directory']=str(out.relative_to(ROOT));(out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
