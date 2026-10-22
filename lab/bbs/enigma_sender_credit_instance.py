#!/usr/bin/env python3
"""Isolated download-only ENiGMA fixture for the finite-credit/EOF sender."""
import argparse,json,os,shutil,socket,sqlite3,subprocess
from pathlib import Path
import enigma
from synthmodem_vm_control import ROOT,sha

STOCK=ROOT/'build/bbs-lab/enigma/source'
PORT=23237
KIND='sexyz-send-credit-eof-candidate'
MANIFEST='sender-credit-instance.json'


def entries(source):
 js="""const c=require('./core/oputil/oputil_common');c.initConfigAndDatabases(e=>{if(e)throw e;const F=require('./core/file_entry');F.findByFileNameWildcard('*',(e,rows)=>{if(e&&e.code!==-33002)throw e;console.log(JSON.stringify((rows||[]).filter(f=>f.areaTag==='pcplus_transfer').map(f=>({fileId:f.fileId,fileName:f.fileName,areaTag:f.areaTag,storageTag:f.storageTag,filePath:f.filePath,fileSha256:f.fileSha256,meta:f.meta,desc:f.desc})).sort((a,b)=>a.fileId-b.fileId)));process.exit(0);});});"""
 return json.loads(subprocess.check_output(['node','-e',js],cwd=source,text=True))


def files(source):
 storage=source/'file_base/pcplus_transfer';result={}
 for p in sorted(storage.rglob('*')):
  assert not p.is_symlink(),p
  if p.is_file():
   s=p.stat();result[str(p.relative_to(storage))]=dict(sha256=sha(p),bytes=s.st_size,inode=s.st_ino,mtime_ns=s.st_mtime_ns)
 return result


def stock_preserved(info):
 assert all(sha(STOCK/n)==h for n,h in info['stock_server_inputs'].items())
 assert sha(STOCK.parent/'helpers/sexyz')==info['stock_helper_sha256']
 assert files(STOCK)==info['stock_files'] and entries(STOCK)==info['stock_entries']


def expected_config(lab):
 config=json.loads((STOCK/'config/config.hjson').read_text())
 config=json.loads(json.dumps(config).replace(str(STOCK.parent/'helpers'),str(lab/'helpers')).replace(str(STOCK),str(lab/'source')))
 config['loginServers']['telnet'].update(address='127.0.0.1',port=PORT)
 config['fileTransferProtocols']['zmodem8kSexyz']['external']['sendCmd']=str(lab/'helpers/sexyz-txcredit-eof')
 return config


def validate(lab):
 lab=Path(lab).resolve();assert lab.is_relative_to(ROOT/'build/bbs-lab') and lab!=STOCK.parent
 info=json.loads((lab/MANIFEST).read_text());assert info['kind']==KIND and info['port']==PORT
 source=lab/'source';helper=lab/'helpers/sexyz-txcredit-eof'
 assert info['source']==str(source) and info['helper']==str(helper)
 receipt=ROOT/'docs/validation/sexyz-send-credit-eof-candidate.json';r=json.loads(receipt.read_text())
 assert r['passed'] and sha(receipt)==info['candidate_receipt_sha256']
 assert sha(helper)==info['helper_sha256']==r['candidate_helper_sha256']
 assert sha(source/'config/config.hjson')==info['config_sha256']
 assert json.loads((source/'config/config.hjson').read_text())==expected_config(lab)
 assert str(STOCK) not in (source/'config/config.hjson').read_text()
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()==enigma.COMMIT
 assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=source,text=True).strip()
 for name in ('db','logs','drop','file_base'):
  assert (source/name).resolve().is_relative_to(source) and not os.path.samefile(source/name,STOCK/name)
 for p in (source/'db').rglob('*.sqlite3'):
  assert not os.path.samefile(p,STOCK/p.relative_to(source))
 assert sha(lab/'helpers/sexyz')==info['stock_helper_sha256']
 for n,h in info['stock_server_inputs'].items():
  if n!='config/config.hjson':assert sha(source/n)==h,n
 stock_preserved(info);return info


def bind(lab):
 lab=Path(lab).resolve();info=validate(lab)
 enigma.LAB=lab;enigma.SOURCE=lab/'source';enigma.PORT=PORT
 import enigma_transfer
 enigma_transfer.LAB=lab;enigma_transfer.SOURCE=enigma.SOURCE
 enigma_transfer.STORAGE=enigma.SOURCE/'file_base/pcplus_transfer';enigma_transfer.HELPER=Path(info['helper'])
 from enigma_fixture import refresh_download_context
 refresh_download_context()
 return dict(kind=KIND,lab=str(lab.relative_to(ROOT)),manifest=str((lab/MANIFEST).relative_to(ROOT)),
  manifest_sha256=sha(lab/MANIFEST),helper_sha256=info['helper_sha256'],source=str(enigma.SOURCE),port=PORT)


def from_result(result):
 context=result['server_fixture'];assert context['kind']==KIND
 lab=(ROOT/context['lab']).resolve();assert lab.is_relative_to(ROOT/'build/bbs-lab')
 path=(ROOT/context['manifest']).resolve();assert path==lab/MANIFEST and sha(path)==context['manifest_sha256']
 bound=bind(lab);assert context==bound and result['server_root']==bound['source'];return bound


def setup(lab,package):
 lab=Path(lab).resolve();package=Path(package).resolve()
 assert lab.is_relative_to(ROOT/'build/bbs-lab') and not lab.exists()
 with socket.socket() as probe:probe.bind(('127.0.0.1',PORT))
 assert not subprocess.check_output(['ss','-Htn','state','established','sport','=',':23233'],text=True).strip()
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=STOCK,text=True).strip()==enigma.COMMIT
 subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=STOCK,check=True)
 receipt=ROOT/'docs/validation/sexyz-send-credit-eof-candidate.json';candidate=json.loads(receipt.read_text())
 assert candidate['passed'] and sha(package/'bin/sexyz')==candidate['candidate_helper_sha256']
 names=['main.js','package-lock.json','core/client.js','core/file_transfer.js','core/file_entry.js','config/config.hjson']
 names+=sorted(str(p.relative_to(STOCK)) for p in (STOCK/'config/menus').glob('*.hjson'))
 info=dict(kind=KIND,source=str(lab/'source'),port=PORT,helper=str(lab/'helpers/sexyz-txcredit-eof'),
  helper_sha256=sha(package/'bin/sexyz'),candidate_package=str(package),candidate_receipt_sha256=sha(receipt),
  stock_server_inputs={n:sha(STOCK/n) for n in names},stock_helper_sha256=sha(STOCK.parent/'helpers/sexyz'),
  stock_files=files(STOCK),stock_entries=entries(STOCK))
 lab.mkdir();source=lab/'source'
 subprocess.run(['git','clone','--shared','--no-hardlinks','--no-checkout',str(STOCK),str(source)],check=True)
 subprocess.run(['git','checkout','--detach',enigma.COMMIT],cwd=source,check=True)
 (source/'node_modules').symlink_to(STOCK/'node_modules',target_is_directory=True)
 shutil.copytree(STOCK/'config',source/'config',dirs_exist_ok=True);shutil.copytree(STOCK/'file_base',source/'file_base')
 for name in ('logs','drop','db/mods'):(source/name).mkdir(parents=True,exist_ok=True)
 snapshots={}
 for path in sorted((STOCK/'db').rglob('*.sqlite3')):
  target=source/path.relative_to(STOCK);target.parent.mkdir(parents=True,exist_ok=True)
  with sqlite3.connect(f'file:{path}?mode=ro',uri=True) as db:
   with sqlite3.connect(target) as copy:
    db.backup(copy);assert copy.execute('PRAGMA integrity_check').fetchone()==('ok',)
  snapshots[str(path.relative_to(STOCK))]=sha(target)
 helpers=lab/'helpers';helpers.mkdir();shutil.copy2(STOCK.parent/'helpers/sexyz',helpers/'sexyz')
 shutil.copy2(package/'bin/sexyz',helpers/'sexyz-txcredit-eof');(helpers/'sexyz-txcredit-eof').chmod(0o755)
 (source/'config/config.hjson').write_text(json.dumps(expected_config(lab),indent=2)+'\n')
 info.update(config_sha256=sha(source/'config/config.hjson'),database_initial_snapshots=snapshots,
  scope='Separate loopback ENiGMA checkout at the stock pin, with private SQLite snapshots/storage/runtime and read-only shared node_modules. Only the ZedZap send command selects the EOF/finite-credit candidate; receive commands use a byte-identical stock helper copy. Stock source/config/helper/files/selected metadata remain unchanged. No transfer or audio acceptance follows from setup.')
 (lab/MANIFEST).write_text(json.dumps(info,indent=2)+'\n');(lab/'metadata.json').symlink_to(MANIFEST)
 context=bind(lab)
 from prepare_audio_pressure_download import NAME,SIZE,payload,preserved_files,validate as validate_fixture
 selected=entries(source);new=[e for e in selected if e['fileName']==NAME];assert len(new)==1
 path=source/'file_base/pcplus_transfer'/NAME;assert path.read_bytes()==payload() and path.stat().st_size==SIZE
 assert all(Path(e['filePath']).resolve().is_relative_to(source/'file_base') for e in selected)
 prior=preserved_files();del prior[NAME]
 output=lab/'pressure-fixture';output.mkdir()
 (output/'metadata-snapshot.json').write_text(json.dumps(selected,indent=2)+'\n')
 checks=dict(exact_copied_pressure_source=True,official_copied_entry_matches_bytes=new[0]['fileSha256']==sha(path),
  all_copied_entries_use_private_storage=True,private_consistent_database_snapshots=True,stock_preserved=True,
  all256_byte_values_exercised=set(payload())==set(range(256)))
 r=dict(passed=all(checks.values()),checks=checks,preparation_only=True,actual_DOS_audio_accepted=False,
  name=NAME,bytes=SIZE,server_revision=enigma.COMMIT,source=str(path.relative_to(ROOT)),sha256=sha(path),
  server_inputs={n:sha(source/n) for n in names},helper_sha256=info['helper_sha256'],server_fixture=context,
  metadata_before=[e for e in selected if e['fileName']!=NAME],metadata_new=new[0],prior_files=prior,
  inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/enigma_fixture.py',ROOT/'lab/bbs/prepare_audio_pressure_download.py',receipt]},
  captures_sha256={'metadata-snapshot.json':sha(output/'metadata-snapshot.json')},
  scope='Copied synthetic pressure fixture with official metadata from consistent snapshots, private storage and unchanged stock custody. This is a separately identified candidate board, not a new stock scan or a transfer/audio acceptance.')
 (output/'result.json').write_text(json.dumps(r,indent=2)+'\n');assert r['passed'];validate_fixture(output/'result.json')
 print(json.dumps(dict(prepared=str(lab),port=PORT,helper_sha256=info['helper_sha256'],stock_preserved=True)))


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['setup','start','status','stop']);p.add_argument('--lab',type=Path,required=True);p.add_argument('--package',type=Path);a=p.parse_args()
 if a.command=='setup':assert a.package;setup(a.lab,a.package)
 else:
  bind(a.lab);{'start':enigma.start,'status':enigma.status,'stop':enigma.stop}[a.command]()


if __name__=='__main__':main()
