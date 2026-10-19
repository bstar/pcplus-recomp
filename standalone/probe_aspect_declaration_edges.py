#!/usr/bin/env python3
"""Optional local original-compiler oracle. Never used by application builds."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ORIGINAL_SHA='5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
CASES={
 'MISSEND':'proc main\ninteger a=(1\nendproc\n',
 'TRAIL':'proc main\ninteger a=1,b=(2\nendproc\n',
 'NEGDEPTH':'proc main\ninteger a=1)\nendproc\n',
 'EMPTYRHS':'proc main\ninteger a=\nendproc\n',
 'UNUSED':'proc removed\ninteger a=(1\nendproc\nproc main\nendproc\n',
 'GLOBAL':'integer a(\nproc main\nendproc\n',
 'PARAM':'proc worker\nintparm a(\nendproc\nproc main\nendproc\n',
 'WORDREAL':'proc main\npause -32768.0\nendproc\n',
 'CLOSED':'proc main\ninteger a=(1)\nendproc\n',
 'NESTINIT':'proc main\ninteger a=(1+(2)),b=3\nendproc\n',
}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--original',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--freeze',type=Path);args=parser.parse_args()
 assert sha(args.original)==ORIGINAL_SHA;out=args.output.resolve();assert out.is_relative_to(ROOT/'analysis')
 out.mkdir(parents=True,exist_ok=False);(out/'ASPCOMP.EXE').write_bytes(args.original.read_bytes());batch=['@echo off']
 for name,source in CASES.items():
  (out/(name+'.ASP')).write_bytes(source.encode('cp437'))
  batch.extend([f'ASPCOMP {name}.ASP >{name}.LOG',f'if errorlevel 1 goto E{name}',f'echo ZERO>{name}.RC',f'goto D{name}',f':E{name}',f'echo ERROR>{name}.RC',f':D{name}'])
 batch.append('echo DONE>DONE.TXT');(out/'RUN.BAT').write_bytes(('\n'.join(batch)+'\n').encode('ascii'))
 (out/'dosbox.conf').write_text(f'[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=386\ncycles=max\n[autoexec]\n@echo off\nmount c "{out}"\nc:\ncall RUN.BAT\nexit\n')
 with (out/'dosbox.log').open('w') as log:subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=60)
 assert (out/'DONE.TXT').read_text().strip()=='DONE';yes=[];no=[]
 for name,source in CASES.items():
  log=(out/(name+'.LOG')).read_bytes();success=b'Script file successfully compiled!' in log;assert success==((out/(name+'.RC')).read_text().strip()=='ZERO')==(out/(name+'.ASX')).exists()
  record=dict(name=name,source=source,source_sha256=sha(out/(name+'.ASP')),log_sha256=sha(out/(name+'.LOG')))
  if success:record.update(hex=(out/(name+'.ASX')).read_bytes().hex(),asx_sha256=sha(out/(name+'.ASX')));yes.append(record)
  else:record['errors']=[s for s in log.decode('cp437').splitlines() if s.startswith('Error')];no.append(record)
 report=dict(schema='aspect-declaration-edges-v1',compiler_sha256=ORIGINAL_SHA,probe_sha256=sha(Path(__file__)),batch_sha256=sha(out/'RUN.BAT'),vectors=yes,rejected=no,scope='Actual original DOS compiler outcomes for authored malformed declaration and WORD real boundary cases. No static decompilation or runtime VM claim.')
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 if args.freeze:
  report['provenance']=dict(report=str((out/'report.json').relative_to(ROOT)),report_sha256=sha(out/'report.json'))
  args.freeze.write_text(json.dumps(report,indent=2)+'\n')
 print('Original declaration oracle:',len(yes),'accepted,',len(no),'rejected')
if __name__=='__main__':main()
