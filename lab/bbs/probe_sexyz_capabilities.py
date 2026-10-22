#!/usr/bin/env python3
"""Measure stock SEXYZ framing for CRC/duplex flags and CLI protocol modes.

This changes only fixture-generated complete ZRINIT offers in fast local pipes.
It does not change DOS, a live BBS or the audio campaign.
"""
import argparse,ctypes as C,json,subprocess,time
from pathlib import Path
from probe_sexyz_receive_credit import CreditProbe,ROOT,HELPER,NAME,payload,sha,P,U
from audit_zmodem import audit_batch,audit_controls,scan


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--library-proof',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 proof=a.library_proof.resolve();out=a.output.resolve();assert proof.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 old=json.loads(proof.read_text());assert old['passed']
 for n,h in old['inputs'].items():assert sha(ROOT/n)==h,n
 library=proof.parent/'session.so';assert sha(library)==old['library_sha256']
 helper=HELPER.resolve();assert sha(helper)==old['helper_sha256'] and old['stock_BBS_helper']
 lib=C.CDLL(str(library));lib.zm_run.argtypes=[P,P,P,U]
 out.mkdir(parents=True);body=payload();rows=[]
 variants=[(True,flags,credit) for flags in (0,1,2,3,32,33,34,35) for credit in (256,8192)]
 variants += [(False,flags,credit) for flags in (1,35) for credit in (256,8192)]
 for zedzap,flags,credit in variants:
  label=f'{"zedzap8K" if zedzap else "standard1K"}-flags{flags:02x}-credit{credit}';folder=out/label;folder.mkdir();source=folder/NAME;source.write_bytes(body)
  command=[str(helper),'-raw']+(['-8'] if zedzap else [])+['sz',NAME]
  with (folder/'helper.stderr').open('xb') as log:
   peer=subprocess.Popen(command,cwd=folder,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,bufsize=0)
   try:
    f=CreditProbe(lib,peer=peer,offer=flags<<24|credit);status=f.run();peer.wait(timeout=10)
    (folder/'sender.bin').write_bytes(f.peer_wire);(folder/'receiver.bin').write_bytes(f.tx)
    (folder/'trace.json').write_text(json.dumps(f.trace,separators=(',',':'))+'\n')
    assert status==peer.returncode==0 and not f.errors and f.received=={NAME:body}
    protocol=audit_batch(bytes(f.peer_wire),{NAME:body});protocol['controls']=audit_controls(protocol,bytes(f.tx),f.trace,'bbs',time.monotonic()+1)
    packets=protocol['files'][0]['packets'];groups=[];pending=0
    for q in packets:
     pending+=q['length']
     if q['ending'] in (104,107):groups.append(pending);pending=0
    assert pending==0 and groups
    # Hex CRC16 control headers remain valid with CRC32 data negotiation.
    formats=sorted({e['format'] for e in protocol['events'] if e['kind']=='header' and e['type']==10})
    assert formats==([67] if flags&32 else [65]),formats
    assert f.replacements>=2 and all(h['position']==flags<<24|credit for h in scan(bytes(f.tx)) if h['type']==1)
    for entry in protocol['files']:assert entry.pop('source')==body
    (folder/'sender.bin').write_bytes(f.peer_wire);(folder/'receiver.bin').write_bytes(f.tx)
    (folder/'trace.json').write_text(json.dumps(f.trace,separators=(',',':'))+'\n');(folder/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    row=dict(case=label,passed=True,zedzap8K=zedzap,flags=flags,credit=credit,CRC32=bool(flags&32),full_duplex=bool(flags&1),overlap=bool(flags&2),
     command=command,data_header_formats=formats,helper_exit=peer.returncode,native_status=status,source_bytes=len(body),max_packet_payload=max(q['length'] for q in packets),max_synchronous_group_payload=max(groups),
     credit_honored=max(groups)<=credit and max(q['length'] for q in packets)<=credit,captures_sha256={q.name:sha(q) for q in folder.iterdir() if q.is_file()})
    rows.append(row);print(json.dumps({k:row[k] for k in ('case','max_packet_payload','max_synchronous_group_payload','credit_honored')}),flush=True)
   finally:
    if peer.poll() is None:peer.kill();peer.wait()
    peer.stdin.close();peer.stdout.close()
 report=dict(passed=True,case_count=len(rows),cases=rows,helper_sha256=sha(helper),library_sha256=sha(library),source_sha256=sha(out/rows[0]['case']/NAME),
  library_proof=str(proof.relative_to(ROOT)),library_proof_sha256=sha(proof),
  inputs={str(q.relative_to(ROOT)):sha(q) for q in [Path(__file__).resolve(),ROOT/'lab/bbs/probe_sexyz_receive_credit.py',ROOT/'lab/bbs/audit_zmodem.py',ROOT/'standalone/check_zmodem.py']},
  scope=__doc__+' Every case requires actual helper/native receiver completion, exact65797-byte file, independent source/CRC/EOF/ZFIN/OO/opposite controls and selected header format. Mode/flag measurements do not establish DOS/BBS/audio behavior, slow-link timing or general compatibility; no fallback is installed.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,case_count=len(rows))))


if __name__=='__main__':main()
