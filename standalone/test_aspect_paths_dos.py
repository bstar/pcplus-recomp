#!/usr/bin/env python3
"""DOS-compiled path scripts on owned mapped files, including CWD/drive retention."""
import argparse,hashlib,json,os,re,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);a=p.parse_args();assert re.fullmatch('[A-Za-z0-9_-]+',a.label)
 out=ROOT/'build/aspect-paths-dos'/a.label;out.mkdir(parents=True,exist_ok=False);program=out/'program';program.mkdir();drive=out/'drive';drive.mkdir()
 for leaf,where in [('ASPECT.EXE','aspect-runner'),('ASPCOMP.EXE','aspect-compiler-dos')]:shutil.copyfile(ROOT/'build'/where/leaf,program/leaf)
 inputs={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'build/aspect-runner/ASPECT.EXE',ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE',Path(__file__)]}
 (drive/'FULL').mkdir();(drive/'FULL/KEEP.TXT').write_bytes(b'OWNED GUARD FILE\0\xff');(drive/'REMOVE.BIN').write_bytes(bytes(range(256))*257)
 scripts={};expectations={}
 def report(label):return 'message "'+label+'"\nitoa failure result\nmessage result\n'
 body='string pathvar, result\nproc main\nstring sub="SUB"\npathvar="BOX"\nset msg_crlf on\n'
 for label,action in [('MK_NEW','mkdir pathvar'),('MK_EXISTS','mkdir pathvar'),('CD_GOOD','chdir pathvar'),('MK_SUB','mkdir sub'),('CD_BAD','chdir "NOPE"'),('MK_STILL','mkdir "STILL"'),('DEL_MISS','delete "..\\MISSING.BIN"'),('DEL_GOOD','delete "..\\REMOVE.BIN"'),('RM_FULL','rmdir "..\\FULL"'),('CD_PARENT','chdir ".."'),('RM_SUB','rmdir "BOX\\SUB"'),('RM_STILL','rmdir "BOX\\STILL"'),('RM_BOX','rmdir pathvar')]:body+=action+'\n'+report(label)
 scripts['FILES']=body+'endproc\n';expectations['FILES']={'MK_NEW':0,'MK_EXISTS':-1,'CD_GOOD':-1,'MK_SUB':0,'CD_BAD':0,'MK_STILL':0,'DEL_MISS':-1,'DEL_GOOD':0,'RM_FULL':'positive','CD_PARENT':'same-RM_FULL','RM_SUB':0,'RM_STILL':0,'RM_BOX':0}
 scripts['DRIVE']='string result\nproc main\nset msg_crlf on\nmkdir "EXISTS"\nmkdir "EXISTS"\nchdir "C:"\n'+report('DRIVE_STATUS')+'mkdir "ONC"\nchdir "ONC"\nmkdir "CHILD"\n'+report('DRIVE_CHILD')+'endproc\n';expectations['DRIVE']={'DRIVE_STATUS':-1,'DRIVE_CHILD':0}
 scripts['PARAM']='string result\nproc main\nstring localpath="LOCAL"\nset msg_crlf on\ncall worker with localpath\nendproc\nproc worker\nstrparm patharg\nmkdir patharg\n'+report('PARAM_MK')+'rmdir patharg\n'+report('PARAM_RM')+'endproc\n';expectations['PARAM']={'PARAM_MK':0,'PARAM_RM':0}
 scripts['HIGH']='string result\nproc main\nset msg_crlf on\nmkdir "DÉR"\n'+report('HIGH_MK')+'rmdir "DÉR"\n'+report('HIGH_RM')+'endproc\n';expectations['HIGH']={'HIGH_MK':0,'HIGH_RM':0}
 batch=['@echo off']
 for name,source in scripts.items():
  compile_source(source)  # Reject an invalid authored fixture before starting DOS.
  (drive/(name+'.ASP')).write_bytes(source.replace('\n','\r\n').encode('cp437'))
  batch+=['D:','cd \\',f'C:\\ASPCOMP D:\\{name}.ASP >D:\\{name}.CMP',f'if errorlevel 1 goto failed',f'C:\\ASPECT D:\\{name}.ASX >D:\\{name}.LOG',f'if errorlevel 1 goto failed',f'cd >D:\\{name}.CWD']
 batch+=['D:','cd \\','echo PASS>D:\\PASS.TXT','goto done',':failed','echo FAIL>D:\\FAIL.TXT',':done','exit'];(drive/'RUN.BAT').write_text('\n'.join(batch)+'\n')
 (out/'expectations.json').write_text(json.dumps(dict(scripts=scripts,status=expectations,inputs=inputs,scope='DOS compiler then runtime, separately compared host bytecode. All mutations target fresh owned mapped test drives.'),indent=2)+'\n')
 cfg=f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{program}"\nmount d "{drive}"\nd:\ncall D:\\RUN.BAT\nexit\n';(out/'dosbox.conf').write_text(cfg)
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=40)
 assert (drive/'PASS.TXT').exists() and not (drive/'FAIL.TXT').exists(),'Compiler/runtime failure; retain per-case logs'
 statuses={};cwd={}
 for name,source in scripts.items():
  assert (drive/(name+'.ASX')).read_bytes()==compile_source(source),name
  lines=(drive/(name+'.LOG')).read_text(encoding='cp437').splitlines();values={}
  for tag,expected in expectations[name].items():
   assert lines.count(tag)==1,(name,tag,lines);value=int(lines[lines.index(tag)+1]);values[tag]=value
   assert value>0 if expected=='positive' else value==values['RM_FULL'] if expected=='same-RM_FULL' else value==expected,(name,tag,value,expected)
  statuses[name]=values;cwd[name]=(drive/(name+'.CWD')).read_text().strip().upper()
 assert cwd=={'FILES':'D:\\','DRIVE':'C:\\ONC','PARAM':'D:\\','HIGH':'D:\\'},cwd
 assert not (drive/'BOX').exists() and not (drive/'SUB').exists() and not (drive/'STILL').exists() and not (drive/'LOCAL').exists() and not (drive/'REMOVE.BIN').exists()
 assert (drive/'FULL/KEEP.TXT').read_bytes()==b'OWNED GUARD FILE\0\xff' and (program/'ONC/CHILD').is_dir()
 assert inputs=={p:sha(ROOT/p) for p in inputs}
 assert sha(program/'ASPECT.EXE')==inputs['build/aspect-runner/ASPECT.EXE'] and sha(program/'ASPCOMP.EXE')==inputs['build/aspect-compiler-dos/ASPCOMP.EXE']
 report=dict(passed=True,scripts=len(scripts),status_checks=sum(map(len,expectations.values())),statuses=statuses,cwd=cwd,inputs=inputs,runner_sha256=sha(program/'ASPECT.EXE'),compiler_sha256=sha(program/'ASPCOMP.EXE'),checker_sha256=sha(Path(__file__)),guard_file_preserved=True,source_and_DOS_bytecode_equal=True,
  scope='Actual8086 DOS original-free compiler and ASPECT runtime, real mkdir/delete/rmdir/chdir/drive syscalls and host-visible filesystem effects. Global/local/parameter/CP437 operands, expected failure continuation, native comparison distinctions, preserved nonempty guard, relative hierarchy and retained CWD/default-drive after child exit. Fresh owned mapped drives only; not physical filesystem crash recovery or complete language.')
 (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
