#!/usr/bin/env python3
"""Compare streamed startup help with the unchanged source-built control."""
import argparse,json,os,re,shutil,struct,subprocess
from pathlib import Path
from build_context_help import ROOT,sha


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('terminal','control','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();binary=a.terminal.resolve();control=a.control.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 c=json.loads(control.with_name('manifest.json').read_text());m=json.loads(binary.with_name('manifest.json').read_text())
 assert c['binary_sha256']==sha(control)=='856a9c85887312099ae92a9f47592ca8b04f6812e7e6e404ad240bad63a6f6d7'
 assert m['binary_sha256']==sha(binary) and m['experimental_line_port_overlay']
 symbols={n:(int(s,16),int(o,16))for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',control.with_name('terminal.map').read_text(),re.M|re.I)}
 raw=control.read_bytes();start=struct.unpack_from('<H',raw,8)[0]*16
 seg,offset=symbols['terminal_usage'];end_seg,end=symbols['terminal_usage_end'];assert seg==end_seg
 golden=raw[start+seg*16+offset:start+seg*16+end-1]
 payload=binary.with_name('PCLINE.OVL').read_bytes();v=m['line_port_overlay']
 assert payload[v['usage_offset']:v['usage_offset']+v['usage_bytes']]==golden and len(golden)==1492
 missing=out/'missing';missing.mkdir();shutil.copyfile(binary,missing/'TERMINAL.EXE')
 cases=[]
 for name,product,cwd,present in [('control',control.parent,'d',True),('same-drive',binary.parent,'c',True),('other-drive',binary.parent,'d',True),('missing',missing,'d',False)]:
  folder=out/name;folder.mkdir(exist_ok=True)
  (folder/'CHECK.BAT').write_text('@echo off\nC:\\TERMINAL /? >D:\\USAGE.TXT\nif errorlevel 1 goto bad\necho PASS>D:\\RESULT.TXT\ngoto end\n:bad\necho FAIL>D:\\RESULT.TXT\n:end\nexit\n')
  (folder/'dosbox.conf').write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[autoexec]
mount c "{product}"
mount d "{folder}"
{cwd}:
D:\CHECK.BAT
exit
''')
  with(folder/'dosbox.log').open('w')as log:
   subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(folder/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=20)
  output=(folder/'USAGE.TXT').read_bytes()
  assert(folder/'RESULT.TXT').read_text().strip()==('PASS'if present else'FAIL'),name
  assert output==(golden if present else b'Cannot read PCLINE.OVL.\r\n'),(name,output)
  cases.append(dict(case=name,expected_success=present,stdout_sha256=sha(folder/'USAGE.TXT'),stdout_bytes=len(output)))
 assert sha(binary)==m['binary_sha256'] and sha(control)==c['binary_sha256'] and sha(binary.with_name('PCLINE.OVL'))==v['sha256']
 result=dict(passed=True,parent_sha256=sha(binary),control_sha256=sha(control),overlay_sha256=v['sha256'],cases=cases,
  sources={n:sha(ROOT/n)for n in ('standalone/test_line_port_usage_dos.py',)},
  scope='Actual DOS8086 /? output/exit status: byte-exact source-built control text, both current drives and missing companion. No BBS or physical acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('DOS startup help: exact1492 bytes, both drives, missing-module exit passed')


if __name__=='__main__':main()
