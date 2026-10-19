#!/usr/bin/env python3
"""Run compiled authored ASX through incremental recovered DOS dispatch."""
import argparse,json,os,subprocess
from pathlib import Path
from build_aspect_runtime import ROOT,OUT,sha
ORIGINAL='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
EXPECTED=['f44d1381879db32a3471ab7605c49a6d97b25395422c5a8604b45d9337216833',
 '2f3c68286f7445c3c1d401d1ed410239e9719f11687def70d37378e38cf93bb5',
 'ec40b46f8c508b585b8ef7eeb7f2398e5c081567fe83495721b87cd6e0ae9809',
 'b235ad26e9d5106fe3390f615c52f2868f44fb5ec54cad3352249a4285be8298',
 '13198f32453ef810aad7bdde574976081e28a8037b04581ede30be457a30cc10']
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--original',type=Path);args=p.parse_args()
 subprocess.run(['python3',str(ROOT/'standalone/build_aspect_runtime.py')],check=True)
 manifest=json.loads((OUT/'manifest.json').read_text());optional=None
 if args.original:
  assert sha(args.original)==ORIGINAL;original=args.original.read_bytes()
 for unit,digest in zip(manifest['support_units'],EXPECTED):
  path=OUT/f'support{unit["unit"]}.bin';assert sha(path)==unit['sha256']==digest
  if args.original:assert original[unit['file_start']:unit['file_start']+unit['bytes']]==path.read_bytes()
 if args.original:
  # Original string builtin19 routes via thunkC2C7 to overlay16 DAFB,
  # which returns a pointer to NUL. The owner supplies its own empty string.
  import struct
  assert struct.unpack_from('<H',original,0x25950+0x4cf8+19*2)[0]==0xc2c7
  assert original[109184-0xd0d0+0xdafb:109184-0xd0d0+0xdaff]==bytes.fromhex('b8 42 49 c3')
  assert original[0x25950+0x4942]==0
  optional=dict(original_sha256=ORIGINAL,exact_support_bytes=sum(u['bytes'] for u in manifest['support_units']),units=manifest['support_units'],empty_string_builtin=dict(index=19,resident_thunk='C2C7',overlay=16,entry='DAFB',returned_DS_offset='4942',observed_first_byte=0,maintained_scope='Only builtin19 returns an owned empty string; other string builtins remain unsupported.'))
 for name in ['DONE.TXT','PASS.TXT','FAIL.TXT']:(OUT/name).unlink(missing_ok=True)
 conf=f'''[sdl]\noutput=surface\n[cpu]\ncore=normal\ncputype=8086\ncycles=max\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount c "{OUT}"\nc:\nEXECUTE >RESULT.TXT\nif errorlevel 1 goto failed\necho PASS>PASS.TXT\ngoto done\n:failed\necho FAIL>FAIL.TXT\n:done\nexit\n'''
 (OUT/'dosbox.conf').write_text(conf)
 with (OUT/'dosbox.log').open('w') as log:
  subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(OUT/'dosbox.conf')],env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,check=True,timeout=60)
 summary=(OUT/'DONE.TXT').read_text().strip()
 assert (OUT/'PASS.TXT').exists() and not (OUT/'FAIL.TXT').exists(),(OUT/'RESULT.TXT').read_text()
 assert summary.startswith(f'ASPECT_RUNTIME {manifest["diagnostic_case_count"]} cases ') and summary.endswith('0 failures'),summary
 result=dict(passed=True,DOS_summary=summary,binary_sha256=sha(OUT/'EXECUTE.EXE'),manifest_sha256=sha(OUT/'manifest.json'),
  check_sha256=sha(Path(__file__).resolve()),result_sha256=sha(OUT/'RESULT.TXT'),optional_original=optional,
  original_inputs=[] if optional is None else [str(args.original)],fixture_count=manifest['fixture_count'],
  unsupported_slot_cases=manifest['unsupported_slot_cases'],
  scope='Actual recovered dispatcher executes compiled authored ASX through real DOS files/far heap and maintained resource owner. Incomplete39-slot command surface; all176 unsupported in-range slots abort. No full compiler/VM, arbitrary-bytecode safety or terminal integration.')
 (OUT/('checks-native.json' if optional else 'checks.json')).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
