#!/usr/bin/env python3
"""Private original-ASPECT string command and comparison compiler corpus."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SHA='5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
def sha(data):return hashlib.sha256(data).hexdigest()
def corpus():
 cases={}
 def add(name,decl,body,helper=''):
  assert name not in cases
  source=decl+'\nproc main\n'+body+'\nendproc\n'+helper
  cases[name]=(source.replace('\n','\r\n').encode('cp437'),name)
 add('LEN','string value\ninteger outcome','value = "HELLO"\nstrlen value outcome','')
 add('LENREV','string value\ninteger outcome','value = "HELLO"\nstrlen outcome value','')
 add('PEEK','string value\ninteger outcome','value = "ABC"\nstrpeek value 1 outcome','')
 add('PEEKREV','string value\ninteger outcome','value = "ABC"\nstrpeek outcome value 1','')
 add('POKE','string value','value = "ABC"\nstrpoke value 1 90','')
 add('LOWER','string value','value = "AbCz09!"\nstrlwr value','')
 add('UPPER','string value','value = "AbCz09!"\nstrupr value','')
 add('LOWHI','string value','value = "AéZÇ"\nstrlwr value','')
 add('UPHI','string value','value = "aézÇ"\nstrupr value','')
 add('CAT','string value','value = "AB"\nstrcat value "CD"','')
 add('CATLEN','string value','value = "AB"\nstrcat value "CDEF" 2','')
 add('CPYLEN','string value','value = "ABCDE"\nstrcpy value "WXYZ" 2','')
 add('SET','string value','value = "ABCDE"\nstrset value 65','')
 add('SETLEN','string value','value = "ABCDE"\nstrset value 65 3','')
 add('UPDATE','string value','value = "ABCDE"\nstrupdt value "xy" 1 2','')
 add('SUBCOPY','string value','substr value "ABCDE" 1 3','')
 add('CMPEQ','integer outcome','strcmp "ABC" "ABC"\noutcome = 1','')
 add('CMPNE','integer outcome','strcmp "ABC" "ABD"\noutcome = 1','')
 add('CMPLEN','integer outcome','strcmp "ABC" "ABD" 2\noutcome = 1','')
 add('LENEMP','string value\ninteger outcome','value = ""\nstrlen value outcome','')
 add('LENMAX','string value\ninteger outcome','value = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"\nstrlen value outcome','')
 add('CATOFL','string value','value = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"\nstrcat value "BC"','')
 add('CATFULL','string value','value = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"\nstrcat value "B"','')
 add('CATEMPTY','string value','value = "AB"\nstrcat value ""','')
 add('CATZERO','string value','value = "AB"\nstrcat value "CD" 0','')
 add('BADLEN','string value','strcpy value "ABC" 81','')
 add('BADINDEX','string value\ninteger outcome','value = "ABC"\nstrpeek value 80 outcome','')
 add('BADCHAR','string value','value = "ABC"\nstrpoke value 1 256','')
 add('SUBEND','string value','substr value "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAZ" 79 1','')
 add('BADSUM','string value','value = "ABCDE"\nstrupdt value "xy" 79 2','')
 add('LOCAL','string outcome','string value\nvalue = "AbC"\nstrlwr value\noutcome = value','')
 add('PARAM','string outcome','call helper with "AbC"','proc helper\nstrparm value\nstrupr value\noutcome = value\nendproc\n')
 add('PGET','integer outcome','call helper with "ABC"','proc helper\nstrparm value\nstrpeek value 2 outcome\nendproc\n')
 add('LOCALCAT','string outcome','string value = "AB"\nstrcat value "CD"\noutcome = value','')
 add('GLBGLB','string value,source','value = "AB"\nsource = "CD"\nstrcat value source','')
 add('PEEKHI','string value\ninteger outcome','value = "é"\nstrpeek value 0 outcome','')
 add('POKEHI','string value','value = "ABC"\nstrpoke value 1 130','')
 add('SETZERO','string value','value = "ABCDE"\nstrset value 0 3','')
 add('NOLEN','string value','strlwr value 2','')
 add('BADCOUNT','string value','strcat value','')
 add('IFEQ','integer outcome','if "ABC" == "ABC"\noutcome = 7\nelse\noutcome = 9\nendif','')
 add('IFNE','integer outcome','if "ABC" != "ABD"\noutcome = 7\nelse\noutcome = 9\nendif','')
 add('IFLT','integer outcome','if "ABC" < "ABD"\noutcome = 7\nelse\noutcome = 9\nendif','')
 add('IFLE','integer outcome','if "ABC" <= "ABC"\noutcome = 7\nelse\noutcome = 9\nendif','')
 add('IFGT','integer outcome','if "ABD" > "ABC"\noutcome = 7\nelse\noutcome = 9\nendif','')
 add('IFGE','integer outcome','if "ABC" >= "ABC"\noutcome = 7\nelse\noutcome = 9\nendif','')
 add('IFCASE','integer outcome','if "abc" == "ABC"\noutcome = 7\nelse\noutcome = 9\nendif','')
 add('IFHI','integer outcome','if "é" > "Z"\noutcome = 7\nelse\noutcome = 9\nendif','')
 add('IFEMPTY','integer outcome','if "" == ""\noutcome = 7\nelse\noutcome = 9\nendif','')
 add('IFEQSTAT',"integer outcome",'strcmp "ABC" "ABC"\nif success\noutcome = 7\nelse\noutcome = 9\nendif')
 add('IFNESTAT',"integer outcome",'strcmp "ABC" "ABD"\nif failure\noutcome = 7\nelse\noutcome = 9\nendif')
 add('IFLTSTAT',"integer outcome",'strcmp "ABC" "ABD"\nif failure < 0\noutcome = 7\nelse\noutcome = 9\nendif')
 add('IFGTSTAT',"integer outcome",'strcmp "ABD" "ABC"\nif failure > 0\noutcome = 7\nelse\noutcome = 9\nendif')
 add('IFCSSTAT',"integer outcome",'strcmp "abc" "ABC"\nif failure > 0\noutcome = 7\nelse\noutcome = 9\nendif')
 add('IFHISTAT',"integer outcome",'strcmp "é" "Z"\nif failure > 0\noutcome = 7\nelse\noutcome = 9\nendif')
 add('IFEMPST',"integer outcome",'strcmp "" ""\nif success\noutcome = 7\nelse\noutcome = 9\nendif')
 add("IFPREFIX","integer outcome",'strcmp "ABC" "ABD" 2\nif success\noutcome = 7\nelse\noutcome = 9\nendif')
 add("IFLOCAL","integer outcome",'string va = "ABC",vb = "ABC"\nstrcmp va vb\nif success\noutcome = 7\nelse\noutcome = 9\nendif')
 add("IFPARAM","integer outcome",'call helper with "ABC" "ABD"','proc helper\nstrparm va,vb\nstrcmp va vb\nif failure < 0\noutcome = 7\nelse\noutcome = 9\nendif\nendproc\n')
 add('IFNEFAIL',"integer outcome",'strcmp "ABC" "ABD"\nif success\noutcome = 7\nelse\noutcome = 9\nendif')
 add('IFEQFAIL',"integer outcome",'strcmp "ABC" "ABC"\nif failure\noutcome = 7\nelse\noutcome = 9\nendif')
 add('CMPRLT',"integer outcome",'strcmp "A" "B"\noutcome = failure')
 add('CMPRGT',"integer outcome",'strcmp "B" "A"\noutcome = failure')
 add('CMPREQ',"integer outcome",'strcmp "A" "A"\noutcome = failure')
 add('CMPZERO',"integer outcome",'strcmp "ABC" "ABD" 0\nif success\noutcome = 7\nelse\noutcome = 9\nendif')
 return cases

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--output',type=Path,required=True);p.add_argument('--only',action='append')
 a=p.parse_args();out=a.output.resolve()
 assert out.parent==ROOT/'analysis/aspect-string-commands' and out.name.startswith('compiler-')
 binary=(ROOT/'analysis/pcplus-install/ASPCOMP.EXE').read_bytes();assert sha(binary)==SHA
 out.mkdir(parents=True,exist_ok=False);(out/'ASPCOMP.EXE').write_bytes(binary)
 cases=corpus()
 if a.only:
  assert all(n in cases for n in a.only) and len(set(a.only))==len(a.only)
  cases={n:cases[n] for n in a.only}
 batch=['@echo off']
 for name,(source,_) in cases.items():
  assert len(name)<=8
  (out/(name+'.ASP')).write_bytes(source)
  batch += [f'ASPCOMP {name}.ASP > {name}.LOG',f'if errorlevel 1 goto E{name}',f'echo ZERO>{name}.RC',
   f'goto D{name}',f':E{name}',f'echo NONZERO>{name}.RC',f':D{name}']
 batch+=['echo COMPLETE>DONE.TXT'];(out/'RUN.BAT').write_bytes(('\r\n'.join(batch)+'\r\n').encode())
 config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=386
cycles=fixed 6000
[mixer]
nosound=true
[autoexec]
@echo off
mount c "{out}"
c:
call RUN.BAT
exit
'''
 (out/'dosbox.conf').write_text(config)
 with (out/'dosbox.log').open('w') as log:
  result=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,
   env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=60)
 assert result.returncode==0 and (out/'DONE.TXT').read_text().strip()=='COMPLETE'
 records=[]
 for name,(source,intent) in cases.items():
  log=(out/(name+'.LOG')).read_bytes();compiled=out/(name+'.ASX');success=b'Script file successfully compiled!' in log
  rc=(out/(name+'.RC')).read_text().strip();assert rc in ('ZERO','NONZERO') and (rc=='ZERO')==success and success==compiled.exists()
  errors=[s for s in log.decode('cp437').splitlines() if s.startswith('Error')]
  record=dict(name=name,intent=intent,source=source.decode('cp437'),source_sha256=sha(source),success=success,
   return_class=rc,errors=errors,log_sha256=sha(log))
  if success:
   data=compiled.read_bytes();record.update(bytes=len(data),asx_sha256=sha(data),hex=data.hex(' '),
    indexed_bytes=[dict(offset=i,hex=f'{byte:02x}') for i,byte in enumerate(data)])
  records.append(record)
 report=dict(compiler_sha256=SHA,harness_sha256=sha(Path(__file__).read_bytes()),cases=records,
  scope='Original compiler string-command/comparison emission only. All ASP scripts authored here; no ASX executed. Compilation success does not establish computed result, parameter ownership, string runtime semantics or complete compiler grammar.')
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 for r in records:print(r['name'],r.get('hex',r['errors']))
 print(json.dumps(dict(cases=len(records),accepted=sum(r['success'] for r in records)),indent=2))


if __name__=='__main__':main()
