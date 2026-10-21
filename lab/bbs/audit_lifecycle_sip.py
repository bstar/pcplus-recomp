#!/usr/bin/env python3
"""Audit real guest REGISTER refresh ownership on the captured tunnel stream."""
import argparse,collections,gzip,json,re,struct
from pathlib import Path
from synthmodem_vm_control import ROOT,sha,records
from synthmodem_lifecycle_runtime import validate
from synthmodem_carrier_runtime import validate as validate_carrier

def sip_frames(path):
 raw=path.read_bytes();at=0;result=[];count=0
 while at<len(raw):
  assert at+7<=len(raw);size=struct.unpack_from('<H',raw,at)[0];assert 5<=size<=8197 and at+size+2<=len(raw)
  channel=raw[at+2];payload=raw[at+7:at+size+2];at+=size+2;count+=1
  if channel!=0:continue
  lines=payload.decode('ascii').replace('\r','').split('\n');headers={}
  for line in lines[1:]:
   if not line:break
   k,v=line.split(':',1);headers[k.lower()]=v.strip()
  result.append({'frame':count,'first':lines[0],'headers':headers})
 return result,count

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--carrier',action='store_true');a=p.parse_args();out=a.cohort.resolve();baseline=a.baseline.resolve()
 r=json.loads((out/'result.json').read_text());base=json.loads((baseline/'result.json').read_text());checks={}
 def runtime_root(receipt):return next(Path(n).parent for n in receipt if Path(n).name=='candidate.cpio.gz')
 inputs=(validate_carrier if a.carrier else validate)(runtime_root(r['runtime_inputs']))
 checks['validated_carrier_runtime' if a.carrier else 'validated_lifecycle_runtime']=inputs==r['runtime_inputs'] and r.get('carrier' if a.carrier else 'lifecycle',False) and r['passed']
 checks['capture_hashes']=all(sha(out/n)==h for n,h in r['captures_sha256'].items())
 checks['baseline_qemu_hash']=sha(baseline/'qemu-0.log')==base['captures_sha256']['qemu-0.log']
 incoming,rx_count=sip_frames(out/'internal-from-guest.bin');outgoing,tx_count=sip_frames(out/'internal-to-guest.bin')
 regs=[v for v in incoming if v['first'].startswith('REGISTER ') and v['headers'].get('expires')!='0' and not re.search(r'expires=0(?:\D|$)',v['headers'].get('contact',''))]
 acks=[v['frame'] for v in outgoing if v['first'].startswith('ACK ')];byes=[v['frame'] for v in outgoing if v['first'].startswith('BYE ')]
 checks['actual_dialog_boundaries']=bool(acks) and bool(byes) and min(acks)<max(byes)
 checks['actual_guest_refresh_observed']=bool(regs)
 requests=collections.Counter((v['headers']['call-id'],v['headers']['cseq']) for v in regs);summaries=[];qemu=(out/'qemu-0.log').read_text()
 for (call,cseq),count in requests.items():
  replies=[v for v in outgoing if v['first'].startswith('SIP/2.0 ') and v['headers'].get('call-id')==call and v['headers'].get('cseq')==cseq]
  codes=[int(v['first'].split()[1]) for v in replies];seq=cseq.split()[0]
  summaries.append({'CSeq':cseq,'request_frames':count,'response_codes':codes,'reply_in_active_dialog':all(min(acks)<v['frame']<max(byes) for v in replies) if acks and byes else False,
   'guest_received_200':bool(re.search(r'RX .*Response msg 200/REGISTER/cseq='+re.escape(seq)+r'\b',qemu))})
 checks['one_successful_owner_per_request']=bool(summaries) and all(v['response_codes']==[200]*v['request_frames'] for v in summaries)
 checks['refresh_during_active_dialog']=bool(summaries) and all(v['reply_in_active_dialog'] for v in summaries)
 checks['guest_received_refresh_success']=bool(summaries) and all(v['guest_received_200'] for v in summaries)
 checks['no_duplicate_UAC_reply']='unexpected incoming REGISTER' not in (out/'node.log').read_text() and not re.search(r'Response msg 405/REGISTER',qemu)
 old=collections.defaultdict(list)
 for code,cseq in re.findall(r'RX .*Response msg (\d+)/REGISTER/cseq=(\d+)\b',(baseline/'qemu-0.log').read_text()):old[cseq].append(int(code))
 checks['real_baseline_duplicate_preserved']=any(200 in v and 405 in v for v in old.values())
 # Runtime roots are external staging directories; compare their relative files.
 old_root=runtime_root(base['runtime_inputs']);new_root=runtime_root(r['runtime_inputs'])
 old_files={str(Path(n).relative_to(old_root)):h for n,h in base['runtime_inputs'].items()};new_files={str(Path(n).relative_to(new_root)):h for n,h in r['runtime_inputs'].items()}
 changed=sorted(n for n in old_files if old_files[n]!=new_files[n])
 expected=['source/src/backends/ModemBackendPool.js','source/src/sip/VmRegistrar.js','source/src/tunnel/UdpTcpTunnel.js']
 if a.carrier:expected+=['candidate.cpio.gz','source/src/backends/PjsipBackend.js']
 checks['only_lifecycle_and_carrier_files_change' if a.carrier else 'only_three_lifecycle_files_change']=set(old_files)==set(new_files) and changed==sorted(expected)
 if a.carrier:
  old_entries=records(gzip.decompress((old_root/'candidate.cpio.gz').read_bytes()));new_entries=records(gzip.decompress((new_root/'candidate.cpio.gz').read_bytes()))
  checks['archive_entry_names_and_metadata_unchanged']=len(old_entries)==len(new_entries) and all(n==nn and f[:6]+f[7:]==ff[:6]+ff[7:] for (n,f,b),(nn,ff,bb) in zip(old_entries,new_entries))
  entry_changes=[n for (n,f,b),(nn,ff,bb) in zip(old_entries,new_entries) if b!=bb]
  checks['only_modem_helper_and_init_archive_changes']=sorted(entry_changes)==['etc/init.d/S99modem-pjsip','usr/local/bin/modemd-ctrl','usr/local/bin/slmodemd']
 result={'passed':all(checks.values()),'checks':checks,'refresh_transactions':summaries,'baseline_REGISTER_responses':dict(old),'changed_runtime_files':changed,
  'tunnel_frames':{'from_guest':rx_count,'to_guest':tx_count},'producer_sha256':sha(out/'result.json'),'auditor_sha256':sha(Path(__file__)),
  'audit_inputs':{name:sha(ROOT/name) for name in ('lab/bbs/audit_lifecycle_sip.py','lab/bbs/synthmodem_vm_control.py','lab/bbs/synthmodem_lifecycle_runtime.py','lab/bbs/synthmodem_carrier_runtime.py')},
  'raw_capture_sha256':{n:sha(out/n) for n in ('internal-from-guest.bin','internal-to-guest.bin','qemu-0.log','node.log')},'carrier':a.carrier,
  'scope':'Independent actual guest tunnel SIP transaction/peer-log audit and exact runtime source comparison. Full DOS/menu/byte audit is separate; no physical ATA/modem acceptance.'}
 (out/'lifecycle-sip-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
