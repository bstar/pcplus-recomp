#!/usr/bin/env python3
"""Read-only evidence of stock publication of the preserved failed reference."""
import argparse,hashlib,json,subprocess,re
from pathlib import Path
from audio_synchronet import ROOT,RUNTIME,sha,snapshot
from synchronet import ENV

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);out=p.parse_args().output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 before=snapshot();failure=ROOT/'docs/validation/synchronet-audio-upload-reference-01.json';f=json.loads(failure.read_text());cohort=ROOT/f['cohort']
 for n,h in f['captures_sha256'].items():assert sha(cohort/n)==h,n
 target=RUNTIME/'data/dirs/pcplab/SXAUREF1.BIN';data=target.read_bytes();assert sha(target)==f['partial_sha256'] and data==(cohort/'source.bin').read_bytes()[:1024]
 script=out/'metadata.js';script.write_text("var f=new FileBase('pcplab');if(!f.open())throw Error(f.last_error);print('PCPLAB_JSON:'+JSON.stringify(f.get('SXAUREF1.BIN')));f.close();\n")
 r=subprocess.run([str(RUNTIME/'exec/jsexec'),'-n',str(script)],env=ENV(),capture_output=True,text=True,check=True)
 (out/'metadata.stdout').write_text(r.stdout);(out/'metadata.stderr').write_text(r.stderr)
 value=json.loads(r.stdout.split('PCPLAB_JSON:',1)[1].splitlines()[0]);assert value['name']=='SXAUREF1.BIN' and value['size']==1024 and value['sha1']==hashlib.sha1(data).hexdigest()
 log=RUNTIME/'data/logs/102126.log';raw=log.read_bytes();marker=b'U+ uploaded SXAUREF1.BIN (1024 bytes) to Main PCPlus Lab';assert raw.count(marker)==1
 at=raw.index(marker);start=raw.rfind(b'@ ',0,at);end=raw.index(b'\r\n\r\n',at)+4;session=raw[start:end]
 assert re.search(rb'\bE\s+1024[^\r\n]*1 errors[^\r\n]*SXAUREF1\.BIN',session)
 (out/'server-session.log').write_bytes(session);(out/'partial.bin').write_bytes(data)
 assert before==snapshot() and sha(target)==f['partial_sha256']
 result=dict(passed=False,diagnosis_confirmed=True,original_failure_receipt=str(failure.relative_to(ROOT)),original_failure_sha256=sha(failure),metadata=value,partial_sha256=sha(target),
  inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audio_synchronet.py',ROOT/'lab/bbs/synchronet.py']},captures_sha256={str(p.relative_to(ROOT)):sha(p) for p in out.iterdir() if p.is_file()},
  scope='Stock Synchronet/sexyz indexes the preserved1024-byte partial from the failed reference despite a receiver E/error record, and writes an upload-success log. Metadata/storage/U+ alone therefore cannot prove protocol success or source completeness. This diagnostic leaves the partial, metadata and original captures intact. Require full wire CRC/control/finish, exact known source and zero-error receive in actual audio acceptance; cancellation/loss cleanup remains open.')
 target_receipt=ROOT/'docs/validation/synchronet-upload-partial-publication.json';assert not target_receipt.exists()
 target_receipt.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'diagnosis_confirmed':True,'compatibility_accepted':False,'partial_bytes':len(data)}))
