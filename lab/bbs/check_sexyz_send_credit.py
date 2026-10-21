#!/usr/bin/env python3
"""Verify isolated sender source closure and finite-credit boundary transfers."""
import argparse,ctypes as C,json,os,subprocess,time
from pathlib import Path
from probe_sexyz_receive_credit import CreditProbe
from audit_zmodem import audit_batch,audit_controls
from synthmodem_vm_control import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate-proof',type=Path,required=True);p.add_argument('--stock-proof',type=Path,required=True);p.add_argument('--baseline-helper',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 candidate_path=a.candidate_proof.resolve();stock_path=a.stock_proof.resolve();out=a.output.resolve()
 assert all(q.is_relative_to(ROOT/'build') for q in (candidate_path,stock_path,out)) and not out.exists();out.mkdir(parents=True)
 def proof(path):
  r=json.loads(path.read_text());assert r['passed'] and all(c['passed'] and all(c['checks'].values()) for c in r['cases'])
  for n,h in r['inputs'].items():assert sha(ROOT/n)==h,n
  for c in r['cases']:
   for n,h in c['captures_sha256'].items():assert sha(path.parent/c['name']/n)==h,n
  assert sha(Path(r['helper_path']))==r['helper_sha256'];return r
 candidate=proof(candidate_path);stock=proof(stock_path);assert not candidate['stock_BBS_helper'] and stock['stock_BBS_helper']
 helper=Path(candidate['helper_path']);baseline=a.baseline_helper.resolve();base=baseline.parent.parent/'share/sexyz-source';changed=helper.parent.parent/'share/sexyz-source'
 original=json.loads((base/'source-manifest.json').read_text());manifest=json.loads((changed/'send-credit-manifest.json').read_text())
 assert original['upstream_commit']==manifest['upstream_commit']=='e7a825704ef5329c7ef8408749671291a85ef7f2'
 assert (base/'source-manifest.json').read_bytes()==(changed/'source-manifest.json').read_bytes()
 for n,h in original['files'].items():assert sha(base/n)==h,n
 names={q.name for q in base.iterdir() if q.suffix in ('.c','.h')};assert names=={q.name for q in changed.iterdir() if q.suffix in ('.c','.h')}
 different=[n for n in sorted(names) if (base/n).read_bytes()!=(changed/n).read_bytes()];assert different==['zmodem.c']
 old=(base/'zmodem.c').read_text();new=(changed/'zmodem.c').read_text()
 head='\nint zmodem_send_from(';tail='\nBOOL zmodem_send_file('
 assert old[:old.index(head)]==new[:new.index(head)] and old[old.index(tail):]==new[new.index(tail):]
 assert sha(base/'zmodem.c')==manifest['before_sha256'] and sha(changed/'zmodem.c')==manifest['after_sha256']
 assert sha(ROOT/'tools/patch-sexyz-send-credit.py')==manifest['patcher_sha256']
 for c in candidate['cases']:assert c['max_packet_payload']<=c['advertised_credit'] and c['max_synchronous_group_payload']<=c['advertised_credit']
 assert all(c['max_packet_payload']==8192 for c in stock['cases'])
 library=candidate_path.parent/'session.so';assert sha(library)==candidate['library_sha256'];lib=C.CDLL(str(library));lib.zm_run.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint]
 rows=[]
 def run(label,credit,flags,size,selected=helper,corrupt=False):
  folder=out/label;folder.mkdir();source=folder/'CREDIT.BIN';body=(bytes(range(256))*((size+255)//256))[:size];source.write_bytes(body);os.utime(source,(946684800,946684800))
  with (folder/'helper.stderr').open('xb') as log:
   peer=subprocess.Popen([str(selected),'-raw','-8','sz',source.name],cwd=folder,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,bufsize=0)
   try:
    f=CreditProbe(lib,peer=peer,offer=(32|flags)<<24|credit,corrupt=corrupt);status=f.run();peer.wait(timeout=10)
    assert status==peer.returncode==0 and not f.errors and f.received=={source.name:body}
    assert f.corruptions==int(corrupt)
    protocol=audit_batch(bytes(f.peer_wire),{source.name:body});protocol['controls']=audit_controls(protocol,bytes(f.tx),f.trace,'bbs',time.monotonic()+1)
    parts=protocol['files'][0]['packets'];groups=[];group=0
    for q in parts:
     group+=q['length']
     if q['ending'] in (104,107):groups.append(group);group=0
    assert group==0 and groups
    for file in protocol['files']:assert file.pop('source')==body
    if credit and selected==helper:assert max(groups)<=credit and max(q['length'] for q in parts)<=credit
    (folder/'sender.bin').write_bytes(f.peer_wire);(folder/'receiver.bin').write_bytes(f.tx);(folder/'engine-input.bin').write_bytes(f.engine_wire)
    (folder/'trace.json').write_text(json.dumps(f.trace,separators=(',',':'))+'\n');(folder/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    row=dict(name=label,passed=True,credit=credit,CANOVIO=bool(flags&2),source_bytes=size,source_sha256=sha(source),injected_engine_byte_errors=f.corruptions,
     helper_sha256=sha(selected),native_status=status,helper_exit=peer.returncode,max_packet=max(q['length'] for q in parts),max_group=max(groups),packet_lengths=[q['length'] for q in parts],
     source_preserved=source.read_bytes()==body,captures_sha256={q.name:sha(q) for q in folder.iterdir() if q.is_file()})
    assert row['source_preserved'];rows.append(row);return row
   finally:
    if peer.poll() is None:peer.kill();peer.wait()
    peer.stdin.close();peer.stdout.close()
 for credit in (1,7,127,128,256,1024,1025,8192):
  for flags in (1,3):
   for size in sorted({max(1,credit-1),credit,credit+1,credit*2+3}):run(f'credit{credit}-flags{flags}-size{size}',credit,flags,size)
 for size in (1,1024,8192,16387):
  normal=run(f'unlimited-stock-{size}',0,3,size,selected=Path(stock['helper_path']))
  proposed=run(f'unlimited-candidate-{size}',0,3,size)
  assert normal['packet_lengths']==proposed['packet_lengths'] and normal['max_group']==proposed['max_group']
 for credit in (256,1024):run(f'CRC-recovery-credit{credit}',credit,3,1284,corrupt=True)
 result=dict(passed=True,cases=rows,case_count=len(rows),changed_C_headers=different,all_source_files_except_one_unchanged=True,only_send_function_changed=True,
  stock_proof=str(stock_path.relative_to(ROOT)),stock_proof_sha256=sha(stock_path),candidate_proof=str(candidate_path.relative_to(ROOT)),candidate_proof_sha256=sha(candidate_path),
  baseline_helper=str(baseline),baseline_helper_sha256=sha(baseline),candidate_helper=str(helper),candidate_helper_sha256=sha(helper),patch_manifest=manifest,
  source_files={n:sha(changed/n) for n in sorted(names)},
  inputs={str(q.relative_to(ROOT)):sha(q) for q in (Path(__file__).resolve(),ROOT/'lab/bbs/probe_sexyz_receive_credit.py',ROOT/'lab/bbs/audit_zmodem.py',ROOT/'tools/patch-sexyz-send-credit.py',ROOT/'nix/sexyz-send-credit.nix',ROOT/'tools/build-sexyz-send-credit')},
  scope='Isolated source-built sender candidate only. Pinned62-file source closure changes only zmodem_send_from in zmodem.c. Real helper/maintained host receiver transfers cover finite credit1..8192, overlap on/off, short/exact/oversize file boundaries and two injected receive-byte CRC recoveries. Four zero-credit candidate/stock packet/group comparisons preserve unlimited framing. Native callbacks use in-memory storage; no actual DOS/16-bit ABI/BBS/audio/slow timing/physical or application acceptance follows.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'case_count':len(rows),'changed_C_headers':different}))


if __name__=='__main__':main()
