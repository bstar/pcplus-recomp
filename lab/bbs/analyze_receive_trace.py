#!/usr/bin/env python3
"""Compare captured RTP PCM with actual guest pre-resample audio, by frame hash."""
import argparse,collections,difflib,hashlib,json,re,struct
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def packets(path):
 b=path.read_bytes();at=0;out=[]
 while at<len(b):
  assert at+4<=len(b);n=struct.unpack_from('<I',b,at)[0];at+=4;assert at+n<=len(b)
  if n:
   assert n==172 and b[at]==0x80 and b[at+1]&127==0;out.append(b[at:at+n])
  at+=n
 return out
def pcm(packet):
 result=[]
 for x in packet[12:]:
  v=x^255;t=(((v&15)<<3)+132)<<((v>>4)&7);result.append(132-t if v&128 else t-132)
 return struct.pack('<160h',*result)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('cohort',type=Path);a=p.parse_args();out=a.cohort.resolve()
 ext=packets(out/'rtp-from-caller.bin');tunnel=packets(out/'rtp-to-guest.bin')
 guest=(out/'modem_rx_8k.raw').read_bytes();assert len(guest)%320==0
 expected=[hashlib.sha256(pcm(b)).hexdigest() for b in tunnel]
 actual=[hashlib.sha256(guest[i:i+320]).hexdigest() for i in range(0,len(guest),320)]
 changes=[];matches=0
 for op,i,j,k,l in difflib.SequenceMatcher(a=expected,b=actual,autojunk=False).get_opcodes():
  if op=='equal':matches+=j-i
  else:changes.append({'operation':op,'RTP_frame_start':i,'RTP_frame_end':j,'guest_frame_start':k,'guest_frame_end':l})
 # Packet boundaries need not coincide with the guest callback boundary.
 # Use unique waveform anchors, then compare every overlapping PCM sample at
 # the dominant offset; this distinguishes fixed latency from altered audio.
 source=b''.join(pcm(b) for b in tunnel);anchors=[]
 for i in range(0,len(tunnel),10):
  start=i*320+64;anchor=source[start:start+64]
  if len(anchor)!=64 or not any(anchor):continue
  if source.find(anchor)!=start or source.find(anchor,start+1)>=0:continue
  at=guest.find(anchor)
  if at<0 or guest.find(anchor,at+1)>=0:continue
  assert at%2==0;anchors.append({'RTP_frame':i,'guest_sample':(at-64)//2,'offset_samples':(at-start)//2})
 offsets=collections.Counter(v['offset_samples'] for v in anchors)
 alignment={'unique_anchors':len(anchors),'offset_histogram':dict(offsets),'offset_changes':[]}
 previous=None
 for v in anchors:
  if v['offset_samples']!=previous:alignment['offset_changes'].append(v);previous=v['offset_samples']
 if offsets:
  offset=offsets.most_common(1)[0][0];shift=offset*2;start=max(0,shift);end=min(len(guest),len(source)+shift)
  assert end>start
  diffs=[i//2 for i in range(start,end,2) if guest[i:i+2]!=source[i-shift:i-shift+2]]
  alignment.update(dominant_offset_samples=offset,dominant_offset_ms=offset/8,compared_samples=(end-start)//2,
   differing_samples=len(diffs),first_difference_sample=diffs[0] if diffs else None,last_difference_sample=diffs[-1] if diffs else None,
   leading_padding_is_silence=not any(guest[:start]),guest_PCM_equals_delayed_RTP_prefix=not diffs and not any(guest[:start]))
 timings=[json.loads(s) for s in (out/'timing.jsonl').read_text().splitlines()];gaps={}
 for kind in ('rtp-from-caller','rtp-to-guest'):
  rows=[v for v in timings if v['type']==kind and v['sequence'] is not None]
  deltas=[(int(b['ns'])-int(a['ns']))/1e6 for a,b in zip(rows,rows[1:])]
  gaps[kind]={'packets':len(rows),'max_gap_ms':max(deltas,default=0),'over40ms':sum(x>40 for x in deltas),'over100ms':sum(x>100 for x in deltas)}
 r=json.loads((out/'result.json').read_text());expected_up=(out/'expected-upstream.bin').read_bytes()
 if 'onlineStart' in r:prefix=r['onlineStart']
 else:
  holds=re.findall(r'Post-train hold complete .*dropped (\d+) bytes\)',(out/'node.log').read_text());assert len(holds)==1;prefix=int(holds[0])
 observed=(out/'guest-workload.bin').read_bytes()[prefix:]
 upstream=[{'operation':op,'expected_start':i,'expected_end':j,'actual_start':k,'actual_end':l,'expected_hex':expected_up[i:j].hex(),'actual_hex':observed[k:l].hex()}
  for op,i,j,k,l in difflib.SequenceMatcher(a=expected_up,b=observed,autojunk=False).get_opcodes() if op!='equal']
 expected_set=set(expected);common=min(len(ext),len(tunnel))
 result={'external_RTP_equals_tunnel_RTP':ext==tunnel,'common_RTP_prefix_exact':ext[:common]==tunnel[:common],
  'external_packets':len(ext),'tunnel_packets':len(tunnel),'guest_frames':len(actual),
  'exact_PCM_frame_matches':matches,'guest_frames_not_found_in_RTP':sum(x not in expected_set for x in actual),
  'frame_alignment_changes':changes,'packet_arrival_gaps':gaps,'upstream_changes':upstream,
  'sample_alignment':alignment,'pre_workload_guest_bytes':prefix,
  'frozen_inputs':{n:sha(out/n) for n in ('rtp-from-caller.bin','rtp-to-guest.bin','modem_rx_8k.raw','timing.jsonl','expected-upstream.bin','guest-workload.bin','result.json')},
  'analyzer_sha256':sha(Path(__file__)),'scope':'Exact G.711 decoding/frame-hash alignment and observed host UDP arrival times. Changed guest PCM proves a media-path difference, not its internal cause. No physical modem/ATA.'}
 (out/'PCM-analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
