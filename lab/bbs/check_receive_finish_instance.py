#!/usr/bin/env python3
"""Verify receiver-fixture isolation and namespace selection before upload."""
import argparse,json,os,sqlite3
from pathlib import Path
import enigma,enigma_transfer,audio_upload
from enigma_upload_dos import metadata
from enigma_receive_finish_instance import ROOT,STOCK,PORT,bind,from_result,validate,sha


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--lab',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 lab=a.lab.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 info=validate(lab);context=bind(lab);source=lab/'source'
 assert enigma.process_pid() and Path(f'/proc/{enigma.process_pid()}/cwd').resolve()==source
 stock_before=metadata(STOCK,['AUDIOUP.BIN']);candidate_before=metadata(source,['AUDIOUP.BIN'])
 checks={'stock_entry_unchanged':stock_before==info['stock_upload'],
  'stock_source_inputs_unchanged':all(sha(STOCK/n)==h for n,h in info['stock_server_inputs'].items()),
  'stock_helper_unchanged':sha(STOCK.parent/'helpers/sexyz')==info['stock_helper_sha256'],
  'clone_has_no_upload':not candidate_before[0]['entries'] and not (source/'file_base/pcplus_transfer/AUDIOUP.BIN').exists(),
  'clone_source_equals_stock':all(sha(source/n)==h for n,h in info['stock_server_inputs'].items() if n!='config/config.hjson'),
  'exact_full_size_original_payload':len(audio_upload.payload())==11521 and set(audio_upload.payload())==set(range(256)),
  'retired_clone_bytes_preserved':sha(Path(info['copied_fixture_retirement']['preserved_bytes']))==info['copied_fixture_retirement']['entry']['fileSha256']}
 expected=json.loads((STOCK/'config/config.hjson').read_text())
 expected=json.loads(json.dumps(expected).replace(str(STOCK.parent/'helpers'),str(lab/'helpers')).replace(str(STOCK),str(source)))
 expected['loginServers']['telnet'].update(address='127.0.0.1',port=PORT)
 expected['fileTransferProtocols']['zmodem8kSexyz']['external']['recvCmd']=info['helper']
 checks['only_declared_configuration_differences']=json.loads((source/'config/config.hjson').read_text())==expected
 for name in ('db','logs','drop','file_base'):
  assert (source/name).resolve().is_relative_to(source) and not os.path.samefile(source/name,STOCK/name)
 for path in (source/'db').rglob('*.sqlite3'):
  with sqlite3.connect(f'file:{path}?mode=ro',uri=True) as db:assert db.execute('PRAGMA integrity_check').fetchone()==('ok',)
  assert not os.path.samefile(path,STOCK/path.relative_to(source))
 checks['private_runtime_and_consistent_database_snapshots']=True
 assert audio_upload.storage()==source/'file_base/pcplus_transfer' and not audio_upload.metadata()
 assert from_result({'server_fixture':context,'server_root':str(source)})==context
 assert from_result({}) is None and audio_upload.storage()==STOCK/'file_base/pcplus_transfer'
 assert audio_upload.metadata()==stock_before[0]['entries']
 checks['candidate_stock_context_roundtrip']=True
 for name,result in [('wrong-root',{'server_fixture':context,'server_root':str(STOCK)}),
  ('wrong-manifest-hash',{'server_fixture':dict(context,manifest_sha256='0'*64),'server_root':str(source)})]:
  try:from_result(result)
  except AssertionError:checks['reject_'+name]=True
  else:raise AssertionError(name)
  finally:from_result({})
 nav=json.loads((lab/'navigation/result.json').read_text())
 checks['actual_navigation_prerequisite']=nav['passed'] and nav['server_fixture']==context and nav['server_config_sha256']==info['config_sha256']
 assert metadata(STOCK,['AUDIOUP.BIN'])==stock_before and metadata(source,['AUDIOUP.BIN'])==candidate_before
 report={'passed':all(checks.values()),'checks':checks,'server_fixture':context,
  'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/enigma_receive_finish_instance.py',ROOT/'lab/bbs/audio_upload.py']},
  'scope':'Read-only actual prepared fixture, official metadata and SQLite integrity, declared config diff, namespace round-trip and malformed-context rejection. Stock upload/helper/code preserved; private runtime verified and navigation prerequisite retained. No actual upload/audio or physical acceptance.'}
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert report['passed']


if __name__=='__main__':main()
