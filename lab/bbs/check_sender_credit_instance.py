#!/usr/bin/env python3
"""Read-only isolation, source custody and cached namespace checks."""
import argparse,json,sqlite3
from pathlib import Path
import enigma,enigma_transfer,audio_download,audio_pressure_download,audit_audio_download
import prepare_audio_pressure_download as fixture
from enigma_fixture import from_result
from enigma_sender_credit_instance import ROOT,STOCK,PORT,MANIFEST,bind,validate,entries,files,sha


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--lab',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 lab=a.lab.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 info=validate(lab);context=bind(lab);source=lab/'source'
 pid=enigma.process_pid();assert pid and Path(f'/proc/{pid}/cwd').resolve()==source
 before={str(p):files(p) for p in (STOCK,source)};metadata={str(p):entries(p) for p in (STOCK,source)}
 checks=dict(stock_source_config_helper_files_metadata_preserved=True,clone_source_pin_and_clean_tree=True,
  only_declared_config_differences=True,private_runtime_files_and_database_inodes=True)
 for path in (source/'db').rglob('*.sqlite3'):
  with sqlite3.connect(f'file:{path}?mode=ro',uri=True) as db:assert db.execute('PRAGMA integrity_check').fetchone()==('ok',)
 checks['all_private_databases_pass_integrity']=True
 for module in (audio_download,fixture,audit_audio_download):
  assert module.STORAGE==source/'file_base/pcplus_transfer' and module.HELPER==Path(info['helper'])
 assert audio_pressure_download.HELPER==audio_pressure_download.PressureDownload.HELPER==Path(info['helper'])
 assert fixture.validate(lab/'pressure-fixture/result.json')[0].parent==source/'file_base/pcplus_transfer'
 checks['preloaded_download_modules_bind_candidate']=True
 assert from_result(dict(server_fixture=context,server_root=str(source),route='download'))==context
 assert from_result({}) is None and enigma.SOURCE==STOCK
 for module in (audio_download,fixture,audit_audio_download):
  assert module.STORAGE==STOCK/'file_base/pcplus_transfer' and module.HELPER==STOCK.parent/'helpers/sexyz'
 assert audio_pressure_download.PressureDownload.HELPER==STOCK.parent/'helpers/sexyz'
 checks['candidate_stock_cached_context_roundtrip']=True
 for label,result in [
  ('wrong_root',dict(server_fixture=context,server_root=str(STOCK),route='download')),
  ('wrong_manifest_hash',dict(server_fixture=dict(context,manifest_sha256='0'*64),server_root=str(source),route='download')),
  ('wrong_helper_hash',dict(server_fixture=dict(context,helper_sha256='0'*64),server_root=str(source),route='download')),
  ('wrong_port',dict(server_fixture=dict(context,port=PORT+1),server_root=str(source),route='download')),
  ('wrong_route',dict(server_fixture=context,server_root=str(source),route='upload')),
  ('wrong_kind',dict(server_fixture=dict(context,kind='unknown'),server_root=str(source),route='download'))]:
  try:from_result(result)
  except AssertionError:checks['reject_'+label]=True
  else:raise AssertionError(label)
  finally:from_result({})
 assert {str(p):files(p) for p in (STOCK,source)}==before
 assert {str(p):entries(p) for p in (STOCK,source)}==metadata
 checks['checks_do_not_mutate_either_board_files_or_entries']=True
 context=bind(lab)
 result=dict(passed=all(checks.values()),checks=checks,server_fixture=context,server_PID=pid,
  inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/enigma_fixture.py',ROOT/'lab/bbs/enigma_sender_credit_instance.py',ROOT/'lab/bbs/audio_pressure_download.py',ROOT/'lab/bbs/audit_audio_download.py',lab/MANIFEST]},
  scope='Actual running isolated fixture, read-only official metadata/SQLite checks, stock custody and declared config comparison. Preloaded cached download modules round-trip between candidate and stock; malformed root/manifest/helper/port/kind/route contexts reject. No transfer/audio or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed'];print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
