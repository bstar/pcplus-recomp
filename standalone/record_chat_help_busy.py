#!/usr/bin/env python3
"""Bind busy/full-FIFO Help admission and sampled module identity evidence."""
import argparse,json
from pathlib import Path
from build_context_help import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('matrix','cold','negative','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();sources={};receipts={}
 def load(path,positive=True):
  path=path.resolve();assert path.is_relative_to(ROOT)
  r=json.loads(path.read_text());assert r['passed']==positive,path;receipts[str(path.relative_to(ROOT))]=sha(path)
  for n,h in r.get('sources',{}).items():
   assert sha(ROOT/n)==h,n
   assert n not in sources or sources[n]==h,n
   sources[n]=h
  return r
 matrix=load(a.matrix/'result.json');cold=load(a.cold/'result.json');negative=load(a.negative/'result.json',False);products=matrix['products']
 assert cold['products']==negative['products']==products
 expected={(r,k) for r in (25,28,43,50) for k in (1,31)}
 assert len(matrix['cases'])==8 and {(r['rows'],r['keys']) for r in matrix['cases']}==expected
 samples=[]
 for case in matrix['cases']:
  file=ROOT/case['receipt'];assert case['passed'] and sha(file)==case['receipt_sha256']
  r=load(file);assert r['products']==products and not r['observer_damage'] and all(r['checks'].values()) and not r['image_differences']
  w,b=r['observer_words'],r['busy_words'];assert w[:2]==[0x4842,3] and w[3]==case['rows']
  assert b[1]&16 and not b[1]&32 and b[11]==case['keys']+1
  wait_ticks=(b[8]-b[7])&65535;assert 0<wait_ticks<36
  assert w[11]==w[12]==w[13] and w[14:19]==[2,0,0,1,11] and w[19:24]==[2,0,0,1,1]
  samples.append(dict(rows=case['rows'],ordinary_keys=case['keys'],FIFO_peak=b[11],native_wait_ticks=wait_ticks,parent_DS=w[10],module_segment=w[11],loaded_image_sha256=r['loaded_image_sha256']))
 assert negative['observer_damage'] and negative['image_differences']==[negative['constants']['IMAGE_BYTES']-1] and negative['observer_words'][22:24]==[0,0]
 assert {k for k,v in negative['checks'].items() if not v}=={'loaded_module_matches_product','loaded_image_unchanged_during_and_after_Help'}
 assert negative['constants']['IMAGE_BYTES']==11396
 assert {r['case'] for r in cold['runs']}=={'normal','flow','Chat-25','Chat-50','Busy-1','Busy-31'}
 for r in cold['runs']:assert all(r['checks'].values())
 for n,h in cold['overlay_sources'].items():assert sha(ROOT/n)==h,n
 baseline=ROOT/'docs/validation/chat-help-recovery.json';previous=json.loads(baseline.read_text());assert previous['passed'] and previous['products']==products
 receipts[str(baseline.relative_to(ROOT))]=sha(baseline)
 sources['standalone/record_chat_help_busy.py']=sha(Path(__file__))
 report=dict(passed=True,products=products,sources=sources,receipts=receipts,module_samples=samples,
  summary=dict(native_busy_Help_sessions=8,rows=[25,28,43,50],ordinary_keys=[1,31],maximum_FIFO=32,initialized_module_bytes=11396,negative_changed_offset=11395,cold_source_files=cold['source_files'],cold_cases=[r['case'] for r in cold['runs']]),
  limitations=['Code identity is sampled before/at/after Help; not a continuous trace or an independent sample of the private loader handle.',
   'Before-frame is the real PROGRAM saved buffer, not an earlier independent VGA capture.',
   'Help beyond FIFO capacity, other native waits/flow stalls, geometry and allocation/lifetime faults remain open.',
   'Same product as prior BBS checkpoint; no BBS rerun or Chat/Help invocation during BBS here.',
   'No physical deployment/acceptance, SIP/audio acceptance, other contexts or full original parity.'],
  scope='Real DOS8086 native TEXT/echo wait and BIOS typeahead, deferred Help at exact FIFO capacity, private PROGRAM state and exact frame/input return. Actual loaded image independently rebased from source MZ, then byte-compared at Help and return. Negative changes observer copy only and is rejected at its final byte. Source-only cold rebuild repeats two busy cases at25 rows plus earlier four Help sessions; eight-case height matrix separate. Application products unchanged.')
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('PASS busy Chat Help and sampled image identity receipt')
if __name__=='__main__':main()
