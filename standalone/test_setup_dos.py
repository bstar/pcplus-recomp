#!/usr/bin/env python3
"""Real DOS settings owner + BIOS-key UI workflows on synthetic local media."""
import hashlib,json,os,shutil,subprocess
from pathlib import Path
from check_setup_model import image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/setup';BASE=['wcl','-q','-bt=dos','-0','-ms','-s','-w4','-we','-k16384','-i='+str(ROOT/'src/config')]
COMMON=[ROOT/'src/config'/p for p in ['setup_document.c','setup_model.c','terminal_import.c','modem_import.c','prm_dos.c','prm_replace.c','prm_replace_fs.c']]
def build():
 subprocess.run(BASE+['-fe=OWNER.EXE',*map(str,COMMON),str(ROOT/'standalone/setup_document_host.c')],cwd=OUT,check=True)
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-dmain=setup_application_main','-fo=setup_ui.obj',str(ROOT/'src/config/setup_main.c')],cwd=OUT,check=True)
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-dprm_replace_delete=setup_fault_delete','-fo=replace_fault.obj',str(ROOT/'src/config/prm_replace.c')],cwd=OUT,check=True)
 subprocess.run(BASE+['-fe=RECOVERY.EXE','replace_fault.obj',*[str(p) for p in COMMON if p.name!='prm_replace.c'],str(ROOT/'standalone/setup_recovery_host.c')],cwd=OUT,check=True)
 subprocess.run(BASE+['-fe=UI.EXE','setup_ui.obj',*map(str,COMMON),str(ROOT/'standalone/setup_ui_host.c')],cwd=OUT,check=True)
def run(name,program,keys='',mode=''):
 directory=OUT/'tests'/name
 if directory.exists():shutil.rmtree(directory)
 directory.mkdir(parents=True)
 for exe in ['PRMEDIT.EXE','OWNER.EXE','UI.EXE','RECOVERY.EXE']:shutil.copyfile(OUT/exe,directory/exe)
 (directory/'VALID.PRM').write_bytes(image());(directory/'SHORT.PRM').write_bytes(image()[:-1])
 if name=='repair':
  raw=bytearray(image());raw[0x198]=2;(directory/'VALID.PRM').write_bytes(raw)
 schedule='ADDKEY p750 '+' p100 '.join(keys.split()) if keys else ''
 conf=f'''[sdl]
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
mount c "{directory}"
c:
{mode}
{schedule}
{program} >LOG.TXT
if errorlevel 1 goto fail
echo PASS>PASS.TXT
goto done
:fail
echo FAIL>FAIL.TXT
:done
exit
'''
 (directory/'dosbox.conf').write_text(conf)
 with (directory/'dosbox.log').open('w') as log:proc=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(directory/'dosbox.conf')],cwd=directory,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=30)
 assert proc.returncode==0 and (directory/'PASS.TXT').exists(),(name,(directory/'LOG.TXT').read_bytes())
 if name!='recovery':assert not (directory/'PRMEDIT.BAK').exists() and not (directory/'PRMEDIT.$$$').exists(),name
 return directory

def main():
 build();cases=[]
 d=run('owner','OWNER');assert b'SETUP DOCUMENT PASS' in (d/'LOG.TXT').read_bytes()
 cases.append({'case':'DOS-owner-load-atomic-save-external-opaque-change-readonly-recovery-collision-invalid-lock-missing','passed':True,'log':(d/'LOG.TXT').read_text().strip()})
 recipes=[('cancel','x escape y',image()),('save-baud','tab home del del del del 1 1 5 2 0 0 f10 escape',image()[:2]+b'\x08\0'+image()[4:]),('invalid-blocked','home del 5 f10 escape y',image()),('response-save','pgdown pgdown pgdown pgdown home del del del del del 1 b space 5 b f10 escape',None),('repair','f10 home del 0 f10 escape',image())]
 # Response 1 is R0 (52 30), five chars. Home/Delete empties it before hex edit.
 response=bytearray(image());response[0xc4:0xc7]=b'\x1b[\0'
 recipes[3]=(recipes[3][0],recipes[3][1],bytes(response))
 for name,keys,value in [
  ('translation-save','pgdown '+'tab '*8+'home del 2 f10 escape',2),
  ('translation-page-navigation','pgdown '+'tab '*8+'home del 2 tab s-tab home del 1 f10 escape',1)]:
  expected=bytearray(image());expected[0x1e0:0x1e2]=bytes([value,0]);recipes.append((name,keys,bytes(expected)))
 for name,keys,want in recipes:
  d=run(name,'UI VALID.PRM',keys);assert (d/'VALID.PRM').read_bytes()==want,name
  assert b'SETUP UI RESTORED' in (d/'LOG.TXT').read_bytes(),name
  cases.append({'case':name,'passed':True,'full_file_exact':True,'screen_cursor_shape_page_restored':True});print(name,'passed',flush=True)
 # Run the exact production executable too, independently of renamed-main host.
 d=run('production','PRMEDIT VALID.PRM','tab home del del del del 1 1 5 2 0 0 f10 escape')
 assert (d/'VALID.PRM').read_bytes()==recipes[1][2]
 cases.append({'case':'production-executable-save','passed':True,'full_file_exact':True})
 # Mono BIOS mode with same owned UI code and complete screen restoration.
 d=run('mono-cancel','UI VALID.PRM 7','escape',mode='mode mono')
 assert (d/'VALID.PRM').read_bytes()==image() and b'SETUP UI RESTORED' in (d/'LOG.TXT').read_bytes()
 cases.append({'case':'mono-cancel','passed':True,'full_file_exact':True,'screen_cursor_shape_page_restored':True})
 d=run('page-one','UI VALID.PRM 3 1','escape')
 assert (d/'VALID.PRM').read_bytes()==image() and b'SETUP UI RESTORED' in (d/'LOG.TXT').read_bytes()
 cases.append({'case':'active-page-one-cancel','passed':True,'screen_cursor_shape_page_restored':True})
 d=run('recovery','RECOVERY')
 assert b'SETUP RECOVERY PASS' in (d/'LOG.TXT').read_bytes() and (d/'PRMEDIT.BAK').read_bytes()==image()
 cases.append({'case':'injected-backup-cleanup-error-installed-baseline-retained-backup-and-locked-retry','passed':True})
 sources=[*COMMON,ROOT/'src/config/setup_main.c',ROOT/'standalone/setup_document_host.c',ROOT/'standalone/setup_ui_host.c',ROOT/'standalone/setup_recovery_host.c',Path(__file__).resolve(),ROOT/'standalone/check_setup_model.py']+list((ROOT/'src/config').glob('*.h'))
 result={'passed':True,'cases':cases,'binaries':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ['PRMEDIT.EXE','OWNER.EXE','UI.EXE','RECOVERY.EXE']},'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'scope':'Actual DOSBox-X filesystem and BIOS keyboard/video, synthetic settings only. UI host links identical UI source with renamed main to independently verify restoration; exact production EXE separately saves. No original PCSETUP, UART or physical hardware tests.'}
 (OUT/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print('DOS setup checks passed')
if __name__=='__main__':main()
