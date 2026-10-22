"""Explicit >64KiB stock-BBS audio campaign, separate from the default fixture."""
import argparse,json
from pathlib import Path
import audio_download
from prepare_audio_pressure_download import NAME,SIZE,validate,entries,HELPER
from synthmodem_vm_control import ROOT,sha

WATCHDOG=54000
OUTER_TIMEOUT=3020


def report(path):
 path=Path(path).resolve();assert path.is_relative_to(ROOT/'build')
 r=json.loads(path.read_text());assert r['passed'] and all(r['checks'].values())
 for n,h in r['inputs'].items():assert sha(ROOT/n)==h,n
 for n,h in r['captures_sha256'].items():assert sha(path.parent/n)==h,n
 return r


def prerequisites(fixture,reference,keys):
 source,before=validate(fixture);ref=report(reference);key=report(keys)
 assert ref['fixture']==str(Path(fixture).resolve().relative_to(ROOT)) and ref['fixture_sha256']==sha(Path(fixture))
 assert ref.get('server_fixture')==json.loads(Path(fixture).read_text()).get('server_fixture')
 assert ref['reference_bytes']==SIZE and ref['reference_sha256']==sha(source)
 assert ref['checks']['complete_source_CRC_EOF_ZFIN_OO_and_opposite_controls']
 assert len(ref['protocol']['files'])==1 and ref['protocol']['files'][0]['name']==NAME
 assert ref['protocol']['files'][0]['sha256']==sha(source) and ref['protocol']['files'][0]['length']==SIZE
 assert key['pressure'] and key['watchdog_BIOS_ticks']==WATCHDOG
 assert key['expected_BIOS_words']==[0x1f53,0x1c0d,0x1950,0x2e43,0x1950,0x1352,0x1245,0x1f53,0x1f53,0x342e,0x3042,0x1749,0x314e,0x1c0d,0x1c0d,0x2d00]
 assert key['checks']['wrong_filename_does_not_release_exit'] and key['checks']['default_production_helper_binary_exact']
 assert key['production_helper_sha256']==sha(Path(keys).parent/'PRODUCTION.COM')
 return source,before,ref,key


class PressureDownload:
 HELPER=HELPER
 def __init__(self,path):
  path=Path(path).resolve();assert path.is_relative_to(ROOT/'build')
  self.preparation=json.loads(path.read_text());r=self.preparation
  assert r['passed'] and r['preparation_only'] and not r['actual_DOS_audio_accepted']
  self.server_fixture=r.get('server_fixture')
  if self.server_fixture:
   from enigma_fixture import from_result
   assert from_result(dict(server_fixture=self.server_fixture,server_root=self.server_fixture['source'],route='download'))==self.server_fixture
  assert r['watchdog_BIOS_ticks']==WATCHDOG and r['outer_timeout_seconds']==OUTER_TIMEOUT
  for n,h in r['inputs'].items():assert sha(ROOT/n)==h,n
  self.fixture=ROOT/r['fixture'];self.reference=ROOT/r['reference'];self.keys=ROOT/r['keys']
  self.path,self.before,ref,key=prerequisites(self.fixture,self.reference,self.keys)
  self.production_helper_sha256=key['production_helper_sha256']
  self.frozen_inputs=list(r['inputs'])+[str(path.relative_to(ROOT)),str(self.path.relative_to(ROOT)),str(HELPER.relative_to(ROOT))]
 def source(self):return self.path,self.before
 def navigation(self,wait,mark):
  script=audio_download.navigation(wait,mark);assert script.count('PCXTEST.BIN')==2
  return script.replace('PCXTEST.BIN',NAME)
 configure_profile=staticmethod(audio_download.configure_profile)
 def check(self,out,rows,path,before):
  assert path==self.path;after=[e for e in entries() if e['fileName']==NAME];target=out/'RECV'/NAME
  executions=[i for i,r in enumerate(rows) if r.get('msg')=='Executing external protocol']
  exits=[i for i,r in enumerate(rows) if r.get('msg')=='Process exited' and r.get('exitCode')==0]
  tail=[r.get('menuName') for r in rows[exits[-1]+1:]] if exits else [];resumed=False
  try:
   first=tail.index('fileBaseMainMenu');search=tail.index('fileBaseSearch',first+1);tail.index('fileBaseListEntries',search+1);resumed=True
  except ValueError:pass
  checks=dict(exact_download=target.is_file() and target.read_bytes()==path.read_bytes(),
   only_expected_download={p.name for p in (out/'RECV').iterdir()}=={NAME},
   no_receive_stage=not any(p.name.startswith(('PCRX.','PCZRX.')) for p in out.rglob('*')),
   actual_helper_exit_zero=len(executions)==len(exits)==1 and executions[0]<exits[0],
   posttransfer_search_and_list=resumed,
   official_download_counter_advanced=len(after)==1 and after[0]['meta'].get('dl_count',0)==before[0]['meta'].get('dl_count',0)+1)
  return checks,dict(expected_path=str(path),expected_bytes=SIZE,expected_sha256=sha(path),metadata_before=before,metadata_after=after,
   menus_after_helper_exit=tail,pressure=True,scope='Coarse pressure-file gates only; independent full byte/protocol/control/cleanup and caller waveform audits remain mandatory.')


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixture',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--keys',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 fixture_info=json.loads(a.fixture.read_text());server_fixture=fixture_info.get('server_fixture')
 if server_fixture:
  from enigma_fixture import from_result
  assert from_result(dict(server_fixture=server_fixture,server_root=server_fixture['source'],route='download'))==server_fixture
 source,before,ref,key=prerequisites(a.fixture.resolve(),a.reference.resolve(),a.keys.resolve())
 records=[a.fixture.resolve(),a.reference.resolve(),a.keys.resolve()];inputs={str(q.relative_to(ROOT)):sha(q) for q in records}
 for path in records:
  r=json.loads(path.read_text());inputs.update(r['inputs'])
 inputs.update({str(q.relative_to(ROOT)):sha(q) for q in (Path(__file__).resolve(),ROOT/'lab/bbs/audio_download.py')})
 r=dict(passed=True,preparation_only=True,actual_DOS_audio_accepted=False,fixture=str(records[0].relative_to(ROOT)),reference=str(records[1].relative_to(ROOT)),keys=str(records[2].relative_to(ROOT)),
  server_fixture=server_fixture,source=str(source.relative_to(ROOT)),bytes=SIZE,sha256=sha(source),watchdog_BIOS_ticks=WATCHDOG,outer_timeout_seconds=OUTER_TIMEOUT,
  production_helper_sha256=key['production_helper_sha256'],default_helper_binary_exact=True,inputs=inputs,
  check_counts=dict(fixture=len(json.loads(records[0].read_text())['checks']),reference=len(ref['checks']),BIOS_helper=len(key['checks'])),
  scope='Preparation only for one actual DOS/audio '+('isolated sender-candidate' if server_fixture else 'stock')+' ENiGMA65797-byte automatic ZMODEM download and post-helper Search/List. Default helper binary remains exact; pressure helper changes only its explicit filename/BIOS words and watchdog. Existing fixture custody, real independent reference transfer, full CRC/finish and BIOS guard are prerequisites. Slow-path integrity/efficiency/cleanup, physical hardware and all application gates remain unverified.')
 out.parent.mkdir(parents=True,exist_ok=True)
 with out.open('x') as f:f.write(json.dumps(r,indent=2)+'\n')
 PressureDownload(out);print(json.dumps({'passed':True,'check_counts':r['check_counts'],'preparation_only':True}))


if __name__=='__main__':main()
