#!/usr/bin/env python3
"""Verify relocated startup help and guarded shutdown on actual DOS."""
import argparse,json,os,re,shutil,struct,subprocess
from pathlib import Path
from build_guarded_helper import ROOT,GUARDED,CONTROL
from prove_guarded_helper_source import sha
def usage(folder):
 text=(folder/'terminal.map').read_text()
 symbols={n:(int(s,16),int(o,16))for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',text,re.M|re.I)}
 raw=(folder/'TERMINAL.EXE').read_bytes();header=struct.unpack_from('<H',raw,8)[0]*16
 lo=symbols['terminal_usage'];hi=symbols['terminal_usage_end'];assert lo[0]==hi[0]
 result=raw[header+lo[0]*16+lo[1]:header+hi[0]*16+hi[1]];assert result[-1:]==b'$'
 return result[:-1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--terminal',type=Path,default=ROOT/'build'/GUARDED/'TERMINAL.EXE');a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build')and not out.exists();out.mkdir(parents=True)
 binary=a.terminal.resolve();m=json.loads((binary.parent/'manifest.json').read_text())
 assert m['terminal_traps']and m['terminal_exit_guard']and sha(binary)==m['binary_sha256']
 for name,digest in m['sources'].items():assert sha(ROOT/name)==digest,name
 expected=usage(binary.parent);assert expected==usage(ROOT/'build'/CONTROL)
 shutil.copyfile(binary,out/'TERMINAL.EXE')
 commands=['TERMINAL /? >HELP.TXT','if errorlevel 1 goto failed',
  'TERMINAL /INVALID >INVALID.TXT','if not errorlevel 1 goto failed',
  'echo PASS>PASS.TXT','exit',':failed','echo FAIL>FAIL.TXT','exit']
 config=out/'dosbox.conf';config.write_text('[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=fixed 12000\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "'+str(out)+'"\nc:\n'+'\n'.join(commands)+'\n')
 with (out/'dosbox.log').open('w')as log:
  run=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(config)],cwd=out,
   env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=30)
 assert run.returncode==0 and(out/'PASS.TXT').exists()and not(out/'FAIL.TXT').exists()
 assert(out/'HELP.TXT').read_bytes()==(out/'INVALID.TXT').read_bytes()==expected
 sources=dict(m['sources']);sources.update({n:sha(ROOT/n)for n in ['standalone/check_guarded_helper_usage_dos.py','standalone/build_guarded_helper.py','standalone/prove_guarded_helper_source.py']})
 result=dict(passed=True,binary_sha256=sha(binary),usage_bytes=len(expected),sources=sources,scope=__doc__+' Exact unchanged help bytes, valid help exit0 and invalid-option exit1; no UART or hardware driver acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS far usage:',len(expected),'bytes and two guarded exits')
if __name__=='__main__':main()
