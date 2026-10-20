#!/usr/bin/env python3
"""Stage/verify the accepted gateway with only the sparse-data helper replaced."""
import argparse,gzip,hashlib,json,shutil,struct,subprocess
from pathlib import Path
from synthmodem_vm_control import ROOT,MEDIA,sha,records,archive

GATEWAY=ROOT/'docs/validation/synthmodem-gateway.json'
SPARSE=ROOT/'docs/validation/synthmodem-sparse.json'
REFERENCE=ROOT/'build/bbs-lab/synthmodem-gateway-01/runtime'

def validate(runtime):
 """Verify every gateway file and every initrd entry; never trust a supplied receipt."""
 prior=json.loads(GATEWAY.read_text());candidate=json.loads(SPARSE.read_text())
 assert prior['passed'] and candidate['passed']
 expected={str(Path(n).relative_to(REFERENCE)):h for n,h in prior['tested_inputs'].items()}
 actual={str(p.relative_to(runtime)) for p in runtime.rglob('*') if p.is_file()}
 assert actual==set(expected),(actual-set(expected),set(expected)-actual)
 for n,h in expected.items():
  if n!='candidate.cpio.gz':assert sha(runtime/n)==h,n
 image=runtime/'candidate.cpio.gz'
 if sha(image)!=expected['candidate.cpio.gz']:
  original=ROOT/'build/bbs-lab/synthmodem-vm-cache/vm/images/rootfs-slmodemd-pjsip.cpio.gz'
  assert sha(original)==MEDIA[original.name]
  old=records(gzip.decompress(original.read_bytes()));new=records(gzip.decompress(image.read_bytes()))
  assert len(old)==len(new)
  changes=[]
  for (on,of,ob),(nn,nf,nb) in zip(old,new):
   assert on==nn
   # Only the body size of the replaced executable may differ in metadata.
   assert of[:6]+of[7:]==nf[:6]+nf[7:]
   if ob!=nb:changes.append(on)
   if on=='usr/local/bin/modemd-ctrl':
    assert hashlib.sha256(nb).hexdigest()==candidate['nix_build']['sha256']
    assert nb[:5]==b'\x7fELF\x01' and struct.unpack_from('<H',nb,18)[0]==3
  assert changes==['usr/local/bin/modemd-ctrl'],changes
 return {str(runtime/n):sha(runtime/n) for n in expected}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 baseline=a.baseline.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build')
 inputs=validate(baseline);prior=json.loads(GATEWAY.read_text());candidate=json.loads(SPARSE.read_text())
 assert sha(baseline/'candidate.cpio.gz')==prior['tested_inputs'][str(REFERENCE/'candidate.cpio.gz')]
 frozen={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'lab/bbs/synthmodem_vm_control.py',GATEWAY,SPARSE,ROOT/'nix/flake.nix',ROOT/'nix/flake.lock']}
 built=json.loads(subprocess.check_output(['nix','--extra-experimental-features','nix-command flakes','build',str(ROOT/'nix')+'#synthmodem-control-i386','--no-link','--json'],text=True))
 helper=Path(built[0]['outputs']['out'])/'bin/modemd-ctrl';assert sha(helper)==candidate['nix_build']['sha256']
 assert 'INTERP' not in subprocess.check_output(['readelf','-l',str(helper)],text=True)
 out.mkdir(parents=True,exist_ok=False);runtime=out/'runtime';shutil.copytree(baseline,runtime)
 entries=records(gzip.decompress((baseline/'candidate.cpio.gz').read_bytes()));changed=[]
 for i,(n,f,b) in enumerate(entries):
  if n=='usr/local/bin/modemd-ctrl':entries[i]=(n,f,helper.read_bytes());changed.append(n)
 assert changed==['usr/local/bin/modemd-ctrl']
 entries.append(('TRAILER!!!',[0]*13,b''));(runtime/'candidate.cpio.gz').write_bytes(gzip.compress(archive(entries),mtime=0))
 tested=validate(runtime)
 assert all(sha(Path(n))==h for n,h in inputs.items()) and all(sha(ROOT/n)==h for n,h in frozen.items())
 result={'passed':True,'runtime_inputs':inputs,'tested_inputs':tested,'frozen_inputs':frozen,'helper_sha256':sha(helper),'build':built,
  'scope':'Staging and exhaustive archive/source identity verification only; unchanged normal init and DSP, no VM execution or compatibility claim.'}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'runtime':str(runtime),'image_sha256':sha(runtime/'candidate.cpio.gz')},indent=2))
if __name__=='__main__':main()
