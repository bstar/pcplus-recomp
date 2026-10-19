#!/usr/bin/env python3
"""Private original ASPECT compiler parameter/string corpus; no ASX execution."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SHA='5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
def sha(data):return hashlib.sha256(data).hexdigest()
def corpus():
 cases={}
 def add(name,globals_,body,helper='',intent=''):
  assert name not in cases
  text=(globals_+'\n' if globals_ else '')+'proc main\n'+body+'\nendproc\n'+helper
  cases[name]=(text.replace('\n','\r\n').encode('ascii'),intent or name)
 add('INTARG','integer outcome','call helper with 7','proc helper\nintparm value\noutcome = value\nendproc\n')
 add('LONGARG','long outcome','call helper with 65537','proc helper\nlongparm value\noutcome = value\nendproc\n')
 add('STRARG','string outcome','call helper with "HELLO"','proc helper\nstrparm value\noutcome = value\nendproc\n')
 add('EMPTYSTR','string outcome','call helper with ""','proc helper\nstrparm value\noutcome = value\nendproc\n')
 add('INTEXPR','integer outcome','call helper with 3 + 4 * 2','proc helper\nintparm value\noutcome = value\nendproc\n')
 add('LONGEXPR','long outcome','call helper with 65537 + 5L','proc helper\nlongparm value\noutcome = value\nendproc\n')
 add('MIXED','integer iout\nlong lout\nstring sout','call helper with 7 65537 "HELLO"','proc helper\nintparm iv\nlongparm lv\nstrparm sv\niout = iv\nlout = lv\nsout = sv\nendproc\n')
 add('COMMAS','integer iout\nlong lout\nstring sout','call helper with 7,65537,"HELLO"','proc helper\nintparm iv\nlongparm lv\nstrparm sv\niout = iv\nlout = lv\nsout = sv\nendproc\n')
 add('NESTED','integer outcome','call first with 7','proc first\nintparm value\ncall second with value + 5\nendproc\nproc second\nintparm value\noutcome = value\nendproc\n')
 add('LOCALS','integer outcome','integer localv = 3\ncall helper with localv + 4','proc helper\nintparm value\ninteger localv = 5\noutcome = value + localv\nendproc\n')
 add('STRLOCAL','string outcome','string localv\nlocalv = "HELLO"\ncall helper with localv','proc helper\nstrparm value\noutcome = value\nendproc\n')
 add('STRGLOB','string input,outcome','input = "HELLO"\ncall helper with input','proc helper\nstrparm value\noutcome = value\nendproc\n')
 add('STRMUT','string input,outcome','input = "ORIGINAL"\ncall helper with input','proc helper\nstrparm value\nvalue = "CHANGED"\noutcome = value\nendproc\n')
 add('INTMUT','integer input,outcome','input = 7\ncall helper with input','proc helper\nintparm value\nvalue = 9\noutcome = value\nendproc\n')
 add('LONGMUT','long input,outcome','input = 65537\ncall helper with input','proc helper\nlongparm value\nvalue = 65539\noutcome = value\nendproc\n')
 add('STRGASS','string first,second','first = "HELLO"\nsecond = first','')
 add('STRLASS','string outcome','string first,second\nfirst = "HELLO"\nsecond = first\noutcome = second','')
 add('STRINIT','string outcome','string localv = "HELLO"\noutcome = localv','')
 add('STRMAX','string outcome','call helper with "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"','proc helper\nstrparm value\noutcome = value\nendproc\n')
 add('STRNEST','string outcome','call first with "HELLO"','proc first\nstrparm value\ncall second with value\nendproc\nproc second\nstrparm value\noutcome = value\nendproc\n')
 add('INTS2','integer first,second','call helper with 7 9','proc helper\nintparm va,vb\nfirst = va\nsecond = vb\nendproc\n')
 add('LONGS2','long first,second','call helper with 65537 65539','proc helper\nlongparm va,vb\nfirst = va\nsecond = vb\nendproc\n')
 add('STRS2','string first,second','call helper with "FIRST" "SECOND"','proc helper\nstrparm va,vb\nfirst = va\nsecond = vb\nendproc\n')
 add('FLOAT','integer outcome','call helper with 7.0','proc helper\nfloatparm value\noutcome = 1\nendproc\n')
 add('BADCOUNT','integer outcome','call helper','proc helper\nintparm value\noutcome = value\nendproc\n')
 add('BADTYPE','integer outcome','call helper with "HELLO"','proc helper\nintparm value\noutcome = value\nendproc\n')
 add('BADLONG','long outcome','call helper with 7','proc helper\nlongparm value\noutcome = value\nendproc\n')
 add('BADWITH','integer outcome','call helper 7','proc helper\nintparm value\noutcome = value\nendproc\n')
 add('TOOMANY','integer outcome','call helper with 7 9','proc helper\nintparm value\noutcome = value\nendproc\n')
 add('BADSTR','string outcome','call helper with 7','proc helper\nstrparm value\noutcome = value\nendproc\n')
 add('INTEVAL','integer outcome','integer argument\nargument = 3 + 4 * 2\ncall helper with argument','proc helper\nintparm value\noutcome = value\nendproc\n')
 add('LONGEVAL','long outcome','long argument\nargument = 65537 + 5L\ncall helper with argument','proc helper\nlongparm value\noutcome = value\nendproc\n')
 add('NESTEVAL','integer outcome','call first with 7','proc first\nintparm value\ninteger intermediate\nintermediate = value + 5\ncall second with intermediate\nendproc\nproc second\nintparm value\noutcome = value\nendproc\n')
 add('LOCEVAL','integer outcome','integer localv = 3\ninteger argument\nargument = localv + 4\ncall helper with argument','proc helper\nintparm value\ninteger localv = 5\noutcome = value + localv\nendproc\n')
 add('ARGNOSPC','integer outcome','call helper with 3+4','proc helper\nintparm value\noutcome = value\nendproc\n')
 add('ARGPAR','integer outcome','call helper with (3+4)','proc helper\nintparm value\noutcome = value\nendproc\n')
 add('ARGBRACK','integer outcome','call helper with [3+4]','proc helper\nintparm value\noutcome = value\nendproc\n')
 add('STRRECUR','string live','live = "LIVE"\ncall helper with live','proc helper\nstrparm value\ncall helper with value\nendproc\n',intent='string argument recursion must reach native stack guard and free live global string')
 add('PARZERO','string live','live = "ALIVE"\ncall helper with 7','proc helper\nintparm value\nvalue = value / 0\nendproc\n',intent='division error inside active typed frame with live global string')
 add('PARFHEAP','string live','live = "ALIVE"\ncall helper with 7.0','proc helper\nfloatparm value\nendproc\n',intent='unavailable float parameter after global assignment must unwind and free string')
 return cases

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--output',type=Path,required=True);p.add_argument('--only',action='append')
 a=p.parse_args();out=a.output.resolve()
 assert out.parent==ROOT/'analysis/aspect-parameters' and out.name.startswith('compiler-')
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
  record=dict(name=name,intent=intent,source=source.decode('ascii'),source_sha256=sha(source),success=success,
   return_class=rc,errors=errors,log_sha256=sha(log))
  if success:
   data=compiled.read_bytes();record.update(bytes=len(data),asx_sha256=sha(data),hex=data.hex(' '),
    indexed_bytes=[dict(offset=i,hex=f'{byte:02x}') for i,byte in enumerate(data)])
  records.append(record)
 report=dict(compiler_sha256=SHA,harness_sha256=sha(Path(__file__).read_bytes()),cases=records,
  scope='Original compiler typed-parameter/string emission only. All ASP scripts authored here; no ASX executed. Compilation success does not establish computed result, parameter ownership, string runtime semantics or complete compiler grammar.')
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 for r in records:print(r['name'],r.get('hex',r['errors']))
 print(json.dumps(dict(cases=len(records),accepted=sum(r['success'] for r in records)),indent=2))


if __name__=='__main__':main()
