#!/usr/bin/env python3
"""Record paired modem experiments without replacing stock compatibility status."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--buffered',required=True);p.add_argument('--control',required=True);p.add_argument('--prior-prerequisite',action='append',default=[],help='Retain a same-runtime DOS-harness pass that did not reach the editor; never use it as a compatibility run');a=p.parse_args()
 runs={}
 for kind,label in [('buffered',a.buffered),('immediate',a.control)]:
  assert label and all(c.isalnum() or c in '-_' for c in label)
  folder=ROOT/'build/bbs-lab/results/enigma'/label
  experiment=read(folder/'experiment.json');run=read(folder/'result.json');audit=read(folder/'semantic-audit.json');modem=read(folder/'modem.json')
  assert experiment['source_sha256']=={s:sha(ROOT/s) for s in experiment['source_sha256']}
  assert experiment['binary_sha256']==run['binary_sha256']==audit['binary_sha256']
  assert experiment['packet_delay_ms']==run['modem_packet_delay_ms']==audit['modem_packet_delay_ms']==modem['packet_delay_ms']
  assert experiment['DOS_harness_passed'] and audit['checks']['no_post_saved']
  assert audit['checks']['stock_editor_entered'],'Editor prerequisite failed; preserve this run and use a fresh label'
  writes=[e for e in modem['events'] if e['kind']=='buffered-serial-write']
  wire=(folder/'bbs-sent.bin').read_bytes()
  key_packets={}
  if writes:
   for key,seq in {'home':b'\x1b[H','insert':b'\x1b[2~'}.items():
    key_packets[key]=any(seq in wire[e['wire_offset']:e['wire_offset']+e['wire_bytes']] for e in writes)
  runs[kind]={'label':label,'experiment':experiment,'configuration':run['configuration'],'keyboard':run['keyboard'],'serial':run['serial'],'semantic_evidence':audit,'buffered_write_count':len(writes),'home_insert_in_individual_writes':key_packets,'retained_artifacts':{str(q.relative_to(ROOT)):sha(q) for q in sorted(folder.iterdir()) if q.is_file()}}
 b,c=runs['buffered'],runs['immediate']
 assert b['experiment']['packet_delay_ms']>0 and c['experiment']['packet_delay_ms']==0
 assert b['experiment']['source_sha256']==c['experiment']['source_sha256']
 for k in ['binary_sha256']:assert b['experiment'][k]==c['experiment'][k]
 for k in ['configuration','keyboard','serial']:assert b[k]==c[k],k
 assert b['buffered_write_count'] and all(b['home_insert_in_individual_writes'].values())
 result={'recorded':True,'binary_sha256':b['experiment']['binary_sha256'],'scope':'Paired actual DOS/stock ENiGMA local editor experiments. Same executable, keyboard recipe, serial settings and PRM; explicit modem packet delay differs. Server/user state was not reset between sequential runs. No physical Wi-Fi modem or general TCP boundary guarantee. Current immediate compatibility aggregate remains separate and unchanged.','buffered_editor_passed':b['experiment']['editor_passed'],'immediate_editor_passed':c['experiment']['editor_passed'],'runs':runs}
 prerequisites=[]
 for label in a.prior_prerequisite:
  assert label and all(c.isalnum() or c in '-_' for c in label)
  folder=ROOT/'build/bbs-lab/results/enigma'/label
  earlier=read(folder/'result.json');audit=read(folder/'semantic-audit.json');experiment=read(folder/'experiment.json')
  assert earlier['binary_sha256']==audit['binary_sha256']==experiment['binary_sha256']==result['binary_sha256']
  assert earlier['passed'] and not audit['checks']['stock_editor_entered'] and audit['checks']['no_post_saved']
  assert experiment['source_sha256']==b['experiment']['source_sha256']
  assert all(earlier[k]==b[k] for k in ['configuration','keyboard','serial'])
  prerequisites.append(dict(label=label,reason='Stock editor prerequisite not reached; excluded from paired editor compatibility.',run=earlier,semantic_evidence=audit,experiment=experiment,retained_artifacts={str(q.relative_to(ROOT)):sha(q) for q in sorted(folder.iterdir()) if q.is_file()}))
 if prerequisites:result['prerequisite_failures']=prerequisites
 target=ROOT/'docs/validation/bbs-enigma-packetization.json'
 if target.exists():
  previous=read(target)
  history=previous.pop('prior_experiments',[])
  previous_labels={k:v['label'] for k,v in previous['runs'].items()}
  current_labels={k:v['label'] for k,v in result['runs'].items()}
  if previous_labels!=current_labels:history.append(previous)
  if history:result['prior_experiments']=history
 target.write_text(json.dumps(result,indent=2)+'\n')
 for source,target_name in [('build/bbs-lab/packetization/result.json','bbs-modem-packetization.json'),('build/bbs-lab/protocol/result.json','bbs-modem-protocol.json')]:
  data=read(ROOT/source);assert data['passed'] and data['modem_source_sha256']==sha(ROOT/'lab/bbs/modem.py')
  (ROOT/'docs/validation'/target_name).write_text(json.dumps(data,indent=2)+'\n')
 print('Recorded buffered editor',result['buffered_editor_passed'],'immediate editor',result['immediate_editor_passed'])
if __name__=='__main__':main()
