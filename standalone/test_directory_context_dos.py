#!/usr/bin/env python3
"""Real DOS retention across a changed directory and installed accounting save."""
import hashlib,json,os,shutil,subprocess
from pathlib import Path
from check_setup_model import image
from check_directory_live import record,text
from directory_test_support import accounting_check
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/directory-context'
def main():
 folder=OUT/'run'
 if folder.exists():shutil.rmtree(folder)
 folder.mkdir();shutil.copyfile(OUT/'CONTEXT.EXE',folder/'CONTEXT.EXE')
 header=b'9,\0'.ljust(25,b'\0')+b'-\0'.ljust(25,b'\0')+bytes(200)
 raw=header+b''.join(text(record(),25,21,b'A55b') for _ in range(200));assert len(raw)==23050
 (folder/'VALID.PRM').write_bytes(image());(folder/'FROZEN.DIR').write_bytes(raw);(folder/'STATE.DIR').write_bytes(raw);(folder/'SHORT.DIR').write_bytes(raw[:-1])
 source_hashes={n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in ['VALID.PRM','FROZEN.DIR','SHORT.DIR']}
 config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=386
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=disabled
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{folder}"
c:
CONTEXT >LOG.TXT
if errorlevel 1 goto fail
echo PASS>PASS.TXT
goto done
:fail
echo FAIL>FAIL.TXT
:done
exit
'''
 (folder/'dosbox.conf').write_text(config)
 with (folder/'dosbox.log').open('w') as log:proc=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],stdout=log,stderr=log,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),check=True,timeout=30)
 log=(folder/'LOG.TXT').read_text();modified_header=b'X\0'.ljust(25,b'\0')+b'Y\0'.ljust(25,b'\0')+bytes(200)
 checks={'DOS_exit_and_internal_checks':proc.returncode==0 and (folder/'PASS.TXT').exists() and 'DIRECTORY CONTEXT PASS 24 checks' in log,'read_only_fixtures_unchanged':source_hashes=={n:hashlib.sha256((folder/n).read_bytes()).hexdigest() for n in source_hashes},'explicit_header_change_plus_exact_accounting_patch_only':accounting_check(modified_header+raw[250:],(folder/'STATE.DIR').read_bytes(),17,1),'no_recovery_files':not (folder/'PCPSTG.$$$').exists() and not (folder/'PCPBAK.$$$').exists()}
 result={'passed':all(checks.values()),'binary_sha256':hashlib.sha256((OUT/'CONTEXT.EXE').read_bytes()).hexdigest(),'checks':checks,'log':log.strip(),'fixture_before_sha256':source_hashes,'sources':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['standalone/test_directory_context_dos.py','standalone/directory_context_host.c','standalone/directory_test_support.py','standalone/check_setup_model.py','standalone/check_directory_live.py']},'scope':'Actual DOS source-owned context load, independent raw selection comparison, explicit changed legacy header, retained/fresh candidate targets, real staged accounting update and read failure atomicity. Only STATE.DIR is intentionally changed; original fixture files remain unchanged. No live setup UI, canonical filesystem identity or physical modem proof.'}
 (OUT/'dos-results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert result['passed']
if __name__=='__main__':main()
