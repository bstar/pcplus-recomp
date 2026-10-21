#!/usr/bin/env python3
"""Independently verify paired real-VM jitter-policy evidence and byte identities."""
import argparse,gzip,hashlib,json,struct
from pathlib import Path
from synthmodem_vm_control import ROOT,sha,records
from analyze_receive_trace import packets,pcm

UP=b'127.0.0.1:45505\r\x1b[?1;2c\x1b[1;1RNEXT\r'
DOWN=(bytes(range(256))*24)[:6000]

def decode(path):
 r=json.loads(path.read_text());return bytes.fromhex(''.join(v['hex'] for v in r['received']))

def raw_PCM_prefix_exact(out,summary):
 # Recompute from raw captures. Refreshed manifest hashes must not make a stale
 # analyzer's zero-difference claim sufficient after its PCM has changed.
 source=b''.join(pcm(v) for v in packets(out/'rtp-to-guest.bin'))
 guest=(out/'modem_rx_8k.raw').read_bytes();offset=summary['PCM'].get('dominant_offset_samples')
 if not isinstance(offset,int) or not 0<=offset<len(guest)//2:return False
 shift=offset*2;overlap=len(guest)-shift
 return overlap>0 and overlap<=len(source) and overlap//2==summary['PCM'].get('compared_samples') and not any(guest[:shift]) and guest[shift:]==source[:overlap]

def inspect(out,variant,builds,network_profile='buffered-release'):
 r=json.loads((out/'result.json').read_text());analysis=json.loads((out/'PCM-analysis.json').read_text());checks={}
 checks['immutable_source']=all(sha(ROOT/n)==h for n,h in r['frozen_inputs'].items())
 checks['immutable_runtime']=all(sha(Path(n))==h for n,h in r['tested_inputs'].items())
 checks['captures_match_receipt']=all(sha(out/n)==h for n,h in r['captures_sha256'].items())
 checks['analysis_inputs_match']=all(sha(out/n)==h for n,h in analysis['frozen_inputs'].items())
 checks['analysis_source_matches']=sha(ROOT/'lab/bbs/analyze_receive_trace.py')==analysis['analyzer_sha256']
 checks['authored_expected_bytes']=(out/'expected-upstream.bin').read_bytes()==UP and (out/'expected-downstream.bin').read_bytes()==DOWN
 checks['caller_output_exact']=(out/'caller-decoded.bin').read_bytes()==DOWN
 checks['offline_caller_exact']=decode(out/'offline-caller.json')==UP
 for name,source in [('offline-caller.json','diagnose_audio_caller.js'),('offline-guest.json','diagnose_receive_pcm.js')]:
  d=json.loads((out/name).read_text());checks[name+'_identity']=d['checker_sha256']==sha(ROOT/'lab/bbs'/source) and d['capture_sha256']==sha(out/('rtp-from-caller.bin' if name=='offline-caller.json' else 'modem_rx_8k.raw')) and d['decoder_sha256']==sha(out/'runtime/source/src/dsp/protocols/V22Demodulator.js')
 checks['real_training_and_cleanup']=all(r['checks'][n] for n in ('registered','real_RING_and_init_OK','both_DSP_CONNECT','teardown','no_errors','guest_PCM_export'))
 checks['correct_variant']=r['dmodem_variant']==variant and r['networkProfile']==network_profile
 raw=(out/'control-wire.bin').read_bytes();at=0;data=bytearray();statuses=[];responses=bytearray()
 while at<len(raw):
  assert at+3<=len(raw);n,k=struct.unpack_from('<HB',raw,at);assert 1<=n<=4094 and at+n+2<=len(raw)
  b=raw[at+3:at+n+2];at+=n+2
  if k==0x15:data.extend(b)
  elif k==0x13:statuses.append(json.loads(b))
  elif k==0x12:responses.extend(b)
 checks['actual_single_guest_carrier']=sum(v.get('event')=='connect' and v.get('rate')==1200 for v in statuses)==1 and b'CONNECT 1200' in responses
 checks['guest_frames_equal_observed_data']=bytes(data)==(out/'guest-decoded.bin').read_bytes()
 workload=(out/'guest-workload.bin').read_bytes();checks['workload_is_actual_guest_prefix']=bytes(data).startswith(workload)
 timeline=[json.loads(v) for v in (out/'timing.jsonl').read_text().splitlines()];release=[v for v in timeline if v['type']=='network-delay-release']
 if network_profile=='buffered-release':
  checks['one_bounded_lossless_release']=len(release)==1 and release[0]['previousDelayMs']==300 and 12<=release[0]['bufferedPackets']<64 and r['checks']['delay_route_preserves_order_and_payload']
 else:
  assert network_profile=='buffered-increase'
  increase=[v for v in timeline if v['type']=='network-delay-increase']
  checks['one_bounded_delay_increase']=not release and len(increase)==1 and increase[0]['previousDelayMs']==0 and increase[0]['nextDelayMs']==120 and increase[0]['bufferedPackets']==0 and 0<=r['networkPendingPackets']<=8 and r['checks']['delay_route_preserves_order_and_payload']
 start=[v for v in timeline if v['type']=='workload-start'];connect=[int(v['ns']) for v in timeline if v['type'] in ('caller-CONNECT','guest-CONNECT')]
 checks['declared_post_training_idle']=len(start)==1 and len(connect)==2 and int(start[0]['ns'])-max(connect)>=6400000000
 streams={n:packets(out/n) for n in ('rtp-from-caller.bin','rtp-after-delay.bin','rtp-to-guest.bin')}
 for name,ps in streams.items():
  headers=[struct.unpack_from('>HII',p,2) for p in ps]
  checks[name+'_continuous']=bool(headers) and all(seq==(headers[0][0]+i)%65536 and ts==(headers[0][1]+160*i)%2**32 and ssrc==headers[0][2] for i,(seq,ts,ssrc) in enumerate(headers))
 for name in ('rtp-after-delay.bin','rtp-to-guest.bin'):
  ps=streams[name];checks[name+'_unaltered_prefix']=bool(ps) and ps==streams['rtp-from-caller.bin'][:len(ps)]
 entries=records(gzip.decompress((out/'runtime/candidate.cpio.gz').read_bytes()))
 checks['boot_image_selected_binary']=sum(n=='usr/local/bin/d-modem' and hashlib.sha256(b).hexdigest()==builds[variant]['executable_sha256'] for n,_,b in entries)==1
 observed=workload[r['onlineStart']:]
 summary={'checks':checks,'upstream_exact':observed==UP,'guest_workload_bytes':len(observed),'offline_guest_exact':decode(out/'offline-guest.json')==UP,
  'PCM':analysis['sample_alignment'],'upstream_changes':analysis['upstream_changes'],'release':release,
  'producer_passed':r['passed'],'producer_sha256':sha(out/'result.json'),'PCM_analysis_sha256':sha(out/'PCM-analysis.json'),
  'captures_sha256':r['captures_sha256'],'frozen_inputs':r['frozen_inputs'],'tested_inputs':r['tested_inputs']}
 return summary,entries,r

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--baseline-variant',choices=['baseline','candidate'],default='baseline')
 p.add_argument('--candidate-variant',choices=['candidate','buffered'],default='candidate')
 p.add_argument('--network-profile',choices=['buffered-release','buffered-increase'],default='buffered-release');a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 ledger=ROOT/'docs/validation/synthmodem-jitter-policy.json';builds=json.loads(ledger.read_text())['builds'];reports={};images={};results={}
 buffered_build=None
 if a.candidate_variant=='buffered':
  from check_buffered_dmodem_build import verify
  buffered_build=verify(json.loads((a.candidate/'result.json').read_text())['dmodem_build'])
  builds['buffered']=buffered_build
 for name,cohort,variant in [('baseline',a.baseline,a.baseline_variant),('candidate',a.candidate,a.candidate_variant)]:reports[name],images[name],results[name]=inspect(cohort.resolve(),variant,builds,a.network_profile)
 changed=[];assert len(images['baseline'])==len(images['candidate'])
 metadata_equal=True
 for (n,f,b),(nn,ff,bb) in zip(images['baseline'],images['candidate']):
  metadata_equal &= n==nn and f[:6]+f[7:]==ff[:6]+ff[7:]
  if b!=bb:changed.append(n)
 base=results['baseline'];cand=results['candidate'];checks={}
 checks['all_provenance_and_transport_invariants']=all(v for r in reports.values() for v in r['checks'].values())
 checks['same_fixture_sources']=base['frozen_inputs']==cand['frozen_inputs']
 def inputs(r,cohort):return {str(Path(n).relative_to(cohort.resolve()/'runtime')):h for n,h in r['tested_inputs'].items() if not n.endswith('/candidate.cpio.gz')}
 checks['same_kernel_and_JS_sources']=inputs(base,a.baseline)==inputs(cand,a.candidate)
 checks['only_dmodem_differs_in_boot_archives']=metadata_equal and changed==['usr/local/bin/d-modem']
 checks['baseline_counterexample_reproduced']=not reports['baseline']['upstream_exact'] and reports['baseline']['PCM'].get('differing_samples',0)>0
 checks['candidate_preserves_upstream_and_PCM']=reports['candidate']['upstream_exact'] and reports['candidate']['offline_guest_exact'] and reports['candidate']['PCM'].get('guest_PCM_equals_delayed_RTP_prefix') is True
 checks['candidate_raw_PCM_matches_RTP_prefix']=raw_PCM_prefix_exact(a.candidate.resolve(),reports['candidate'])
 r={'passed':all(checks.values()),'checks':checks,'cohorts':reports,'changed_archive_bodies':changed,'auditor_sha256':sha(Path(__file__)),'build_ledger_sha256':sha(ledger),
  'network_profile':a.network_profile,'baseline_variant':a.baseline_variant,'candidate_variant':a.candidate_variant,'buffered_build':buffered_build,
  'scope':'Independent actual-VM binary/source/archive identities, framed guest data, exact caller payload, RTP continuity and lossless timing-route comparison. Candidate acceptance is limited to this controlled V22/1200 diagnostic, not full DOS/BBS/hardware or proof of the earlier intermittent event.'}
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'checks':checks,'result':str(out/'result.json')},indent=2));return 0 if r['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
