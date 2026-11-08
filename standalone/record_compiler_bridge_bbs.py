#!/usr/bin/env python3
"""Bind compiler-bridge lab payload, cold rebuild and stock BBS transfer evidence."""
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('payload','proof','runtime','contract','output'):p.add_argument('--'+name,type=Path,required=True)
 for name in ('enigma-download','enigma-upload','sync-download','sync-upload'):p.add_argument('--'+name,required=True)
 a=p.parse_args();payload=read(a.payload/'package.json');proof=read(a.proof/'result.json');contract=read(a.contract/'result.json')
 assert payload['passed'] and proof['passed'] and contract['passed']
 assert proof['lab_payload']['products']==contract['products']==payload['products']
 assert len(payload['products'])==9 and all(sha(a.payload/n)==h for n,h in payload['products'].items())
 resolver=ROOT/'lab/bbs/product_inputs.py'
 guard="    if manifest.get('experimental_compiler_lease_bridge'):\n        module=manifest.get('experimental_compiler_lease_module')\n        assert isinstance(module,dict) and module.get('whole_kernel') is True, 'Compiler bridge requires its matched whole-kernel module'\n"
 current=resolver.read_text();assert current.count(guard)==1
 previous=hashlib.sha256(current.replace(guard,'',1).encode()).hexdigest()
 groups={};receipts={};sources={str(resolver.relative_to(ROOT)):sha(resolver)}
 for key,server,direction,size in (('enigma_download','enigma','download',11521),('enigma_upload','enigma','upload',65539),('sync_download','synchronet','download',11521),('sync_upload','synchronet','upload',65539)):
  label=getattr(a,key);assert re.fullmatch('[a-z0-9-]+',label)
  wrapper=ROOT/'build/bbs-lab'/(label+'-transfer');result=read(wrapper/'result.json')
  output=ROOT/'build/bbs-lab/results'/server/label;protocol=read(output/'result.json')
  assert result['passed'] and all(result['checks'].values()) and not result['protocol_errors']
  assert all(result['protocol_checks'].values()) and protocol['passed'] and protocol['cpu']=='8086'
  assert result['terminal_sha256']==protocol['binary_sha256']==payload['products']['TERMINAL.EXE']
  assert ('mount c "'+str(a.payload.resolve())+'"') in (output/'dosbox.conf').read_text()
  assert result['mode']==direction and result['fixture']['bytes']==size
  frozen=result.get('product_inputs',result.get('products'))
  for n,h in {**frozen,**result['server_inputs']}.items():
   if n=='lab/bbs/product_inputs.py':assert h in (sha(resolver),previous)
   else:assert sha(ROOT/n)==h,n
  for n,h in result['proxy']['installed_sources'].items():assert sha(a.runtime/n)==h,n
  for folder in (wrapper,output,ROOT/'build/bbs-lab'/(label+'-proxy')):
   for f in folder.rglob('*'):
    if f.is_file():receipts[str(f.relative_to(ROOT))]=sha(f)
  groups[key]=dict(fixture=result['fixture'],checks=result['checks'],protocol_checks=result['protocol_checks'],
   product_inputs=frozen,server_inputs=result['server_inputs'],proxy_sources=result['proxy']['installed_sources'],
   resolver_sha256=frozen['lab/bbs/product_inputs.py'],mounted_payload=True,cpu='8086',scope=protocol['scope'])
 for path in (a.payload/'package.json',a.proof/'result.json',a.contract/'result.json'):
  receipts[str(path.resolve().relative_to(ROOT))]=sha(path)
 for name in ('standalone/package_compiler_bridge_lab.py','standalone/test_compiler_bridge_lab_payload.py','standalone/prove_compiler_bridge_source.py','standalone/record_compiler_bridge_bbs.py'):sources[name]=sha(ROOT/name)
 review=ROOT/'analysis/aspect-get-string-filter-20261108.rea.json'
 failed=ROOT/'build/bbs-lab/compiler-bridge-enigma-upload-20261108-transfer/result.json'
 failure=read(failed);assert not failure['passed'] and failure['protocol_checks']['ZFILE_data_CRC_ZEOF_ZFIN_OO_confirmed']
 record=dict(checkpoint_verified=True,application_bytes_changed=False,software_transfer_verified=True,
  release_eligible=False,installed_changed=False,selector_changed=False,physical_verified=False,original_application_build_inputs=[],
  products=payload['products'],BBS_transfers=groups,payload_contract=contract['checks'],
  source_rebuild=dict(path=str((a.proof/'result.json').relative_to(ROOT) if a.proof.is_absolute() else a.proof/'result.json'),source_count=proof['source_count'],DOS_cases=proof['DOS_cases'],termination_cases=proof['termination_cases'],artifacts=proof['artifacts'],lab_payload=proof['lab_payload']),
  resolver_variants=dict(current_sha256=sha(resolver),download_variant_sha256=previous,transformation='Remove the exact mandatory whole-kernel guard block; other source bytes unchanged.'),
  native_review=dict(original_sha256='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904',evidence_id='ev_94dd779c586e196c322f03573bb5c82d27e5edbe9e0cf0f66f9eafeaa372c1dc',provider='Ghidra12.1.2',resident_start='3f9c',end_exclusive='3fb0',bytes=20,behavior='Near word-pointer callback: Enter13 returns99, otherwise0; no input mutation or external calls.',private_snapshot_sha256=sha(review),application_behavior_changed=False),
  failed_fixture=dict(path=str(failed.relative_to(ROOT)),sha256=sha(failed),passed=False,checks=failure['protocol_checks'],reason='30-second wait reached Upload Details before file-base commit/menu completion; repeated with established60-second fixture timing and a new name.'),
  sources=sources,receipts=receipts,remaining=['Physical Boca/SPA2102/SIP/audio/CTS/DCD and target DOS acceptance.','Current-parent LoC main rendering, source login, cancel/retry, carrier-loss/reconnect and sustained transfer composition.','Full language, other emulations/protocols/Host parity and complete release packaging.'])
 a.output.write_text(json.dumps(record,indent=2)+'\n');print('Verified compiler-bridge BBS transfers:',len(groups),'payload files:',len(payload['products']))


if __name__=='__main__':main()
