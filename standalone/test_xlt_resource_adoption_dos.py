#!/usr/bin/env python3
"""Real DOS publication, canonical Reload/Edit identity and pending-offer refusal."""
import argparse,hashlib,json,os,shutil,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
NAMES=['virgin-mode1-cwd-reload-editor','virgin-mode0','virgin-mode2','invalid-canonical-identities','invalid-extents-and-aliases','pending-reload-preserved','pending-settings-preserved','disable-and-reenable-identity','63-byte-canonical-identity','pending-offer-preserved','caller-storage-reuse','reported-close-error-after-close','uncertain-close-still-open']
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 built=ROOT/'build/xlt-resource-adoption';m=json.loads((built/'manifest.json').read_text());assert not m['original_inputs']
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 assert sha(built/'XLTADOPT.EXE')==m['binary_sha256'];shutil.copyfile(built/'XLTADOPT.EXE',out/'XLTADOPT.EXE')
 files={'NEW.XLT':bytes(255-i for i in range(256)),'OTHER/PCPLUS.XLT':bytes(i^0xaa for i in range(256)),'PCPLUS.XLT':bytes(range(256)),'ABCDEFGH/IJKLMNOP/QRSTUVWX/YZABCDEF/GHIJKLMN/ABCDEFG/NEW.XLT':bytes(255-i for i in range(256))}
 assert len('C:\\'+next(n for n in files if n.startswith('ABCDEFGH')).replace('/',chr(92)))==63
 for n,b in files.items():q=out/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
 commands=[]
 for i in range(len(NAMES)):commands+=['cd \\',f'C:\\XLTADOPT {i} >C:\\R{i:02}.TXT','if errorlevel 1 goto failed',f'ren C:\\REPORT.BIN R{i:02}.BIN']
 commands+=['cd \\','echo PASS>PASS.TXT','exit',':failed','cd \\','echo FAIL>FAIL.TXT','exit']
 config='[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\nset PCPLUS=\n'+'\n'.join(commands)+'\n';(out/'dosbox.conf').write_text(config)
 with (out/'dosbox.log').open('w') as log:r=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=120)
 assert r.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),[(q.name,q.read_text()) for q in sorted(out.glob('R*.TXT'))]
 cases=[]
 for i,n in enumerate(NAMES):
  mode,checks,opens,reads,closes,canonical,bad=struct.unpack('<7H',(out/f'R{i:02}.BIN').read_bytes());assert mode==i and not bad and opens==closes
  cases.append(dict(case=n,passed=True,native_assertions=checks,opens=opens,reads=reads,closes=closes,canonicalizations=canonical))
 for n,b in files.items():assert (out/n).read_bytes()==b,n
 for n,h in m['sources'].items():assert sha(ROOT/n)==h,n
 result=dict(passed=True,binary_sha256=m['binary_sha256'],sources=m['sources'],case_count=len(cases),cases=cases,native_assertions=sum(c['native_assertions'] for c in cases),original_inputs=[],test_sources={'standalone/test_xlt_resource_adoption_dos.py':sha(Path(__file__))},artifacts={str(q.relative_to(out)):sha(q) for q in out.rglob('*') if q.is_file()},scope=__doc__+' Actual production owner, table reader and DOS filesystem; wrappers only count calls/flags. No selected-entry application, UART/mode/mask publication, BBS rendering, physical hardware or card claim.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(cases),'DOS workflows;',result['native_assertions'],'native assertions')
if __name__=='__main__':main()
