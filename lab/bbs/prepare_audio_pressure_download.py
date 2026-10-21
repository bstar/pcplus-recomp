#!/usr/bin/env python3
"""Register one fresh >64KiB owned ENiGMA download without replacing fixtures."""
import argparse,json,subprocess
from pathlib import Path
import enigma
from enigma_transfer import AREA,STORAGE,HELPER
from synthmodem_vm_control import ROOT,sha

NAME='PCPRESS.BIN'
SIZE=65797


def payload():return bytes((i*73+(i>>8)*19+37)&255 for i in range(SIZE))


def entries():
 js="""const c=require('./core/oputil/oputil_common');c.initConfigAndDatabases(e=>{if(e)throw e;const F=require('./core/file_entry');F.findByFileNameWildcard('*',(e,entries)=>{if(e&&e.code!==-33002)throw e;console.log(JSON.stringify((entries||[]).filter(f=>f.areaTag===process.argv[1]).map(f=>({fileId:f.fileId,fileName:f.fileName,areaTag:f.areaTag,storageTag:f.storageTag,filePath:f.filePath,fileSha256:f.fileSha256,meta:f.meta,desc:f.desc})).sort((a,b)=>a.fileId-b.fileId)));process.exit(0);});});"""
 return json.loads(subprocess.check_output(['node','-e',js,AREA],cwd=enigma.SOURCE,text=True))


def preserved_files():
 result={}
 for p in sorted(STORAGE.rglob('*')):
  assert not p.is_symlink(),p
  if p.is_file():
   s=p.stat();result[str(p.relative_to(STORAGE))]=dict(sha256=sha(p),bytes=s.st_size,inode=s.st_ino,mtime_ns=s.st_mtime_ns)
 return result


def validate(path):
 path=Path(path).resolve();assert path.is_relative_to(ROOT/'build')
 r=json.loads(path.read_text());assert r['passed'] and r['preparation_only'] and r['actual_DOS_audio_accepted'] is False
 assert r['name']==NAME and r['bytes']==SIZE and r['server_revision']==enigma.COMMIT
 for n,h in r['inputs'].items():assert sha(ROOT/n)==h,n
 for n,h in r['server_inputs'].items():assert sha(enigma.SOURCE/n)==h,n
 for n,h in r['captures_sha256'].items():assert sha(path.parent/n)==h,n
 source=STORAGE/NAME;assert source==ROOT/r['source'] and source.read_bytes()==payload() and sha(source)==r['sha256']
 current=preserved_files()
 for n,record in r['prior_files'].items():assert current[n]==record,n
 now=entries();selected=[e for e in now if e['fileName']==NAME];assert len(selected)==1
 assert all(e in now for e in r['metadata_before'])
 entry=selected[0];assert entry['fileId']==r['metadata_new']['fileId']
 assert Path(entry['filePath']).resolve()==source.resolve() and entry['fileSha256']==r['sha256']
 assert entry['areaTag']==entry['storageTag']==AREA and entry['meta']['byte_size']==SIZE
 assert sha(HELPER)==r['helper_sha256']
 return source,selected


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 pid=enigma.process_pid();assert pid and Path(f'/proc/{pid}/cwd').resolve()==enigma.SOURCE.resolve()
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=enigma.SOURCE,text=True).strip()==enigma.COMMIT
 subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=enigma.SOURCE,check=True)
 assert not subprocess.check_output(['ss','-Htn','state','established','sport','=',':23233'],text=True).strip(),'Owned lab connection active'
 source=STORAGE/NAME;assert not source.exists()
 before=entries();assert not any(e['fileName']==NAME for e in before)
 prior=preserved_files();server_names=['main.js','config/config.hjson','core/file_entry.js','core/oputil/oputil_file_base.js','core/oputil/oputil_common.js']
 server_names+=sorted(str(p.relative_to(enigma.SOURCE)) for p in (enigma.SOURCE/'config/menus').glob('*.hjson'))
 server_inputs={n:sha(enigma.SOURCE/n) for n in server_names}
 (out/'metadata-before.json').write_text(json.dumps(before,indent=2)+'\n')
 with source.open('xb') as f:f.write(payload())
 with (out/'scan.stdout').open('w') as stdout,(out/'scan.stderr').open('w') as stderr:
  subprocess.run(['node','oputil.js','fb','scan',AREA,'PCPRESS.*','--no-prompt'],cwd=enigma.SOURCE,stdout=stdout,stderr=stderr,check=True)
 after=entries();(out/'metadata-after.json').write_text(json.dumps(after,indent=2)+'\n');new=[e for e in after if e['fileName']==NAME]
 current=preserved_files();checks=dict(source_crosses64KiB=len(payload())==SIZE>65536,
  exact_new_source=source.read_bytes()==payload(),only_one_new_physical_file=set(current)==set(prior)|{NAME},
  all_prior_files_unchanged=all(current[n]==r for n,r in prior.items()),
  all_prior_metadata_unchanged=all(e in after for e in before),only_one_new_metadata_entry=len(after)==len(before)+1 and len(new)==1,
  official_source_metadata=len(new)==1 and new[0]['fileSha256']==sha(source) and new[0]['meta']['byte_size']==SIZE and Path(new[0]['filePath']).resolve()==source.resolve() and new[0]['areaTag']==new[0]['storageTag']==AREA,
  server_source_config_and_menus_unchanged=all(sha(enigma.SOURCE/n)==h for n,h in server_inputs.items()),
  all256_byte_values_exercised=set(payload())==set(range(256)))
 r=dict(passed=all(checks.values()),checks=checks,preparation_only=True,actual_DOS_audio_accepted=False,name=NAME,bytes=SIZE,
  source=str(source.relative_to(ROOT)),sha256=sha(source),server_revision=enigma.COMMIT,server_inputs=server_inputs,helper_sha256=sha(HELPER),
  metadata_before=before,metadata_new=new[0] if len(new)==1 else None,prior_files=prior,
  inputs={str(q.relative_to(ROOT)):sha(q) for q in (Path(__file__).resolve(),ROOT/'lab/bbs/enigma.py',ROOT/'lab/bbs/enigma_transfer.py')},
  captures_sha256={q.name:sha(q) for q in out.iterdir() if q.is_file()},
  scope='Preparation only: fresh65797-byte PCPRESS.BIN registered in the existing owned area through the stock official scan CLI and FileEntry API. Exact existing physical bytes/inode/size/mtime and all prior selected metadata preserve. Source/config/menus/helper stay fixed. No reference transfer, DOS/audio, sustained throughput, latency, protocol finish, physical hardware or full application acceptance.')
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');assert r['passed'];validate(out/'result.json')
 print(json.dumps({'passed':True,'checks':checks,'source':r['source'],'bytes':SIZE,'sha256':r['sha256']}))


if __name__=='__main__':main()
