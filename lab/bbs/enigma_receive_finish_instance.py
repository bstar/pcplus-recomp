#!/usr/bin/env python3
"""Separate loopback board for the Nix receiver candidate; preserve stock state."""
import argparse,hashlib,json,shutil,socket,sqlite3,subprocess
from pathlib import Path
import enigma

ROOT=Path(__file__).resolve().parents[2]
STOCK=ROOT/'build/bbs-lab/enigma/source'
PORT=23235

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def validate(lab):
 lab=Path(lab).resolve();assert lab.is_relative_to(ROOT/'build/bbs-lab') and lab!=STOCK.parent
 path=lab/'receive-finish-instance.json';info=json.loads(path.read_text())
 assert info['kind']=='sexyz-receive-finish-candidate' and info['port']==PORT
 assert Path(info['source'])==lab/'source'
 assert Path(info['helper'])==lab/'helpers/sexyz-rxfinish'
 assert sha(Path(info['helper']))==info['helper_sha256']
 receipt=json.loads((ROOT/'docs/validation/sexyz-receive-finish-candidate.json').read_text())
 assert receipt['passed'] and info['helper_sha256']==receipt['candidate_sha256']
 assert sha(lab/'source/config/config.hjson')==info['config_sha256']
 config=json.loads((lab/'source/config/config.hjson').read_text())
 assert config['loginServers']['telnet']['address']=='127.0.0.1' and config['loginServers']['telnet']['port']==PORT
 assert config['fileTransferProtocols']['zmodem8kSexyz']['external']['recvCmd']==info['helper']
 assert config['fileBase']['storageTags']['pcplus_transfer']==str(lab/'source/file_base/pcplus_transfer')
 for name in ('db','logs','drop','file_base'):
  assert (lab/'source'/name).is_dir() and (lab/'source'/name).resolve().is_relative_to(lab/'source')
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=lab/'source',text=True).strip()==enigma.COMMIT
 assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=lab/'source',text=True).strip()
 return info

def bind(lab):
 info=validate(lab);lab=Path(lab).resolve()
 enigma.LAB=lab;enigma.SOURCE=lab/'source';enigma.PORT=info['port']
 import enigma_transfer
 enigma_transfer.LAB=lab;enigma_transfer.SOURCE=enigma.SOURCE
 enigma_transfer.STORAGE=enigma.SOURCE/'file_base/pcplus_transfer'
 enigma_transfer.HELPER=Path(info['helper'])
 path=lab/'receive-finish-instance.json'
 return {'kind':info['kind'],'lab':str(lab.relative_to(ROOT)),
  'manifest':str(path.relative_to(ROOT)),'manifest_sha256':sha(path),
  'helper_sha256':info['helper_sha256'],'source':str(enigma.SOURCE)}

def from_result(result):
 context=result.get('server_fixture')
 if not context:
  assert result.get('server_root',str(STOCK))==str(STOCK)
  enigma.LAB=STOCK.parent;enigma.SOURCE=STOCK;enigma.PORT=23233
  import enigma_transfer
  enigma_transfer.LAB=STOCK.parent;enigma_transfer.SOURCE=STOCK
  enigma_transfer.STORAGE=STOCK/'file_base/pcplus_transfer';enigma_transfer.HELPER=STOCK.parent/'helpers/sexyz'
  return None
 lab=(ROOT/context['lab']).resolve();path=(ROOT/context['manifest']).resolve()
 assert lab.is_relative_to(ROOT/'build/bbs-lab') and path==lab/'receive-finish-instance.json'
 assert sha(path)==context['manifest_sha256']
 bound=bind(ROOT/context['lab']);assert bound==context
 assert result['server_root']==bound['source']
 return bound

def setup(lab):
 from enigma_upload_dos import metadata
 lab=Path(lab).resolve();assert lab.is_relative_to(ROOT/'build/bbs-lab') and not lab.exists()
 with socket.socket() as probe:probe.bind(('127.0.0.1',PORT))
 original=json.loads((ROOT/'docs/validation/synthmodem-audio-upload-02.json').read_text())
 stock_inputs={n:sha(STOCK/n) for n in original['server_inputs']}
 assert stock_inputs==original['server_inputs']
 old_helper=STOCK.parent/'helpers/sexyz';helper_sha=sha(old_helper)
 before=metadata(STOCK,['AUDIOUP.BIN']);assert len(before)==1 and len(before[0]['entries'])==1
 entry=before[0]['entries'][0];stock_file=Path(entry['filePath'])
 assert stock_file.resolve()==STOCK/'file_base/pcplus_transfer/AUDIOUP.BIN'
 assert sha(stock_file)==entry['fileSha256']==original['source_and_installed_file_sha256']
 with sqlite3.connect(f'file:{STOCK/"db/user.sqlite3"}?mode=ro',uri=True) as db:
  assert {r[0] for r in db.execute('SELECT user_name FROM user')}=={'locadmin','loclab'}
 candidate_receipt=json.loads((ROOT/'docs/validation/sexyz-receive-finish-candidate.json').read_text())
 assert candidate_receipt['passed'] and not candidate_receipt['candidate_audio_accepted']
 outputs=list(map(Path,(ROOT/'build/bbs-lab/sexyz-finish-build-paths.txt').read_text().splitlines()))
 package=next(p for p in outputs if 'finish-candidate' in p.name)
 binary=package/'bin/sexyz';assert sha(binary)==candidate_receipt['candidate_sha256']
 lab.mkdir();source=lab/'source'
 subprocess.run(['git','clone','--shared','--no-hardlinks','--no-checkout',str(STOCK),str(source)],check=True)
 subprocess.run(['git','checkout','--detach',enigma.COMMIT],cwd=source,check=True)
 (source/'node_modules').symlink_to(STOCK/'node_modules',target_is_directory=True)
 shutil.copytree(STOCK/'config',source/'config',dirs_exist_ok=True)
 shutil.copytree(STOCK/'file_base',source/'file_base')
 for name in ('logs','drop','db/mods'):(source/name).mkdir(parents=True,exist_ok=True)
 snapshots={}
 for path in sorted((STOCK/'db').rglob('*.sqlite3')):
  target=source/'db'/path.relative_to(STOCK/'db');target.parent.mkdir(parents=True,exist_ok=True)
  with sqlite3.connect(f'file:{path}?mode=ro',uri=True) as db:
   with sqlite3.connect(target) as copied:
    db.backup(copied);assert copied.execute('PRAGMA integrity_check').fetchone()==('ok',)
  snapshots[str(path.relative_to(STOCK))]=sha(target)
 helpers=lab/'helpers';helpers.mkdir();shutil.copy2(old_helper,helpers/'sexyz')
 helper=helpers/'sexyz-rxfinish';shutil.copyfile(binary,helper);helper.chmod(0o755)
 config=json.loads((STOCK/'config/config.hjson').read_text())
 text=json.dumps(config).replace(str(STOCK.parent/'helpers'),str(helpers)).replace(str(STOCK),str(source))
 config=json.loads(text);config['loginServers']['telnet'].update(address='127.0.0.1',port=PORT)
 config['fileTransferProtocols']['zmodem8kSexyz']['external']['recvCmd']=str(helper)
 assert 'paths' not in config and str(STOCK) not in json.dumps(config)
 (source/'config/config.hjson').write_text(json.dumps(config,indent=2)+'\n')
 cloned=metadata(source,['AUDIOUP.BIN']);assert len(cloned[0]['entries'])==1
 cloned_entry=cloned[0]['entries'][0];cloned_file=Path(cloned_entry['filePath'])
 assert cloned_file.resolve()==source/'file_base/pcplus_transfer/AUDIOUP.BIN'
 assert sha(cloned_file)==entry['fileSha256']
 # Only the copied synthetic entry is retired, through the official API.
 # Preserve its bytes and row first; the original board is never modified.
 backup=lab/'copied-AUDIOUP-preserved.bin'
 with backup.open('xb') as f:f.write(cloned_file.read_bytes())
 removed=subprocess.run(['node','oputil.js','fb','rm',str(cloned_entry['fileId']),'--phys-file'],cwd=source,text=True,capture_output=True,check=True)
 assert not metadata(source,['AUDIOUP.BIN'])[0]['entries'] and not cloned_file.exists()
 assert metadata(STOCK,['AUDIOUP.BIN'])==before and sha(stock_file)==entry['fileSha256']
 assert stock_inputs=={n:sha(STOCK/n) for n in stock_inputs} and sha(old_helper)==helper_sha
 info={'kind':'sexyz-receive-finish-candidate','source':str(source),'port':PORT,
  'helper':str(helper),'helper_sha256':sha(helper),'candidate_package':str(package),
  'config_sha256':sha(source/'config/config.hjson'),'database_initial_snapshots':snapshots,
  'stock_server_inputs':stock_inputs,'stock_helper_sha256':helper_sha,'stock_upload':before,
  'copied_fixture_retirement':{'entry':cloned_entry,'preserved_bytes':str(backup),'preserved_sha256':sha(backup),'official_cli_stdout':removed.stdout},
  'scope':'Separate loopback source-identical ENiGMA board, consistent synthetic DB snapshots and private writable storage. Only ZedZap receive command selects the candidate; stock board/helper/upload and SIP/DSP runtime remain unchanged. Copied AUDIOUP entry/bytes are preserved then retired in this clone only; fresh same-size/same-payload upload required.'}
 (lab/'receive-finish-instance.json').write_text(json.dumps(info,indent=2)+'\n')
 (lab/'metadata.json').symlink_to('receive-finish-instance.json')
 validate(lab);print(json.dumps({'prepared':str(lab),'endpoint':f'127.0.0.1:{PORT}','helper_sha256':info['helper_sha256'],'stock_preserved':True}))

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['setup','start','status','stop']);p.add_argument('--lab',type=Path,required=True);a=p.parse_args()
 if a.command=='setup':setup(a.lab)
 else:
  bind(a.lab)
  {'start':enigma.start,'status':enigma.status,'stop':enigma.stop}[a.command]()

if __name__=='__main__':main()
