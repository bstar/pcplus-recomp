#!/usr/bin/env python3
"""Recorder-generation counterexamples through maintained compiler/native TX.

Cached source-built instruction units are hash-checked; no original executable,
DOS program or UART is used. Transport/delay callbacks are modeled. This tests
constraints for the source recorder, not an implemented recorder or UI owner.
"""
import argparse,hashlib,json,sys
from pathlib import Path
from check_aspect_serial_commands import Machine,DATA,PAUSE,EXPECTED
from build_aspect_serial_commands import ROOT,OUT
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source,CompileError


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 target=a.output.resolve();assert target.is_relative_to(ROOT/'build') and not target.exists()
 manifest=json.loads((OUT/'manifest.json').read_text());assert not manifest['original_inputs']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 images=[]
 for unit in manifest['units']:
  path=OUT/unit['name'];assert sha(path)==unit['sha256'];images.append((unit['start'],unit['end_exclusive'],path.read_bytes()))
 assert [sha(OUT/f'serial-commands{i}.bin') for i in range(1,8)]==EXPECTED
 rows=[]
 def case(label,raw,encoded,expected,pauses=0,accepted=True):
  source=b'proc main\r\ntransmit "'+encoded+b'"\r\nendproc\r\n'
  try:compile_source(source.decode('cp437'));compiled=True;error=None
  except CompileError as exc:compiled=False;error=str(exc)
  assert compiled==accepted,(label,compiled,error)
  m=Machine(images,b'\x64\0');m.write(DATA['bank'],encoded+b'\0\0');m.invoke('transmit')
  assert bytes(m.tx)==expected and len(m.pauses)==pauses,(label,m.tx,m.pauses)
  rows.append(dict(case=label,raw_hex=raw.hex(),literal_hex=encoded.hex(),source_compiles=compiled,
   compiler_error=error,transmitted_hex=bytes(m.tx).hex(),pause_calls=m.pauses,
   byte_exact_replay=compiled and bytes(m.tx)==raw and not m.pauses,expected_behavior_observed=True))
 def legacy(raw):return b''.join(b'^'+bytes([c+64]) if c<32 else bytes([c]) for c in raw)
 for raw in (b'ABC',b'\0',b'\r\n',bytes(range(1,32)),b'"',b'^M',b'^',b'^^^',b'~',b'\x80\xdb\xfe',b'\xff'):
  encoded=legacy(raw)
  expected=(b'' if raw in (b'^',b'~') else b'\r' if raw==b'^M' else b'^' if raw==b'^^^' else b'\0' if raw==b'\xff' else bytes(range(1,30))+b'^_' if raw==bytes(range(1,32)) else raw)
  case('legacy-'+raw.hex(),raw,encoded,expected,pauses=int(raw==b'~'),accepted=raw!=b'"')
 case('explicit-literal-caret',b'^',b'^^^',b'^')
 case('explicit-NUL-sentinel',b'\0',b'^@',b'\0')
 case('control30-before-caret-prefix',b'\x1e\x1f',b'^~^_',b'\x1e\x1f')
 for count in (26,27):
  source=b'proc main\r\ntransmit "'+b'^^^'*count+b'"\r\nendproc\r\n'
  try:compile_source(source.decode('cp437'));accepted=True
  except CompileError:accepted=False
  assert accepted==(count==26)
  rows.append(dict(case='escaped-caret-literal-limit-'+str(count),encoded_length=count*3,source_compiles=accepted,expected_behavior_observed=True))
 target.parent.mkdir(parents=True,exist_ok=True)
 result=dict(passed=True,cases=rows,case_count=len(rows),legacy_non_roundtrips=[r['case'] for r in rows[:11] if not r['byte_exact_replay']],
  inputs={str(q.relative_to(ROOT)):sha(q) for q in [Path(__file__).resolve(),ROOT/'src/aspect/compiler.py',ROOT/'standalone/check_aspect_serial_commands.py',ROOT/'standalone/check_aspect_console.py',OUT/'manifest.json']},
  instruction_units_sha256={str((OUT/u['name']).relative_to(ROOT)):u['sha256'] for u in manifest['units']},scope=__doc__)
 with target.open('x') as f:f.write(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(passed=True,case_count=len(rows),legacy_non_roundtrips=result['legacy_non_roundtrips'])))


if __name__=='__main__':main()
