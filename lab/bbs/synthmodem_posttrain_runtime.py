#!/usr/bin/env python3
"""Stage an isolated monotonic minimum-hold repair on the framed runtime."""
import argparse,json,shutil
from pathlib import Path
from synthmodem_vm_control import ROOT,sha
from synthmodem_key_framing_runtime import validate as validate_reference

REFERENCE=ROOT/'build/bbs-lab/synthmodem-key-framing-runtime-01/runtime'
LEAF='source/src/session/CallSession.js'


def patch(source):
 start=source.index('  _onModemConnected() {');end=source.index('  // ─── Hangup',start)
 body=source[start:end]
 replacements=[
  ('    const startedAt = Date.now();','    const nowMs = () => Number(process.hrtime.bigint()) / 1e6;\n    const startedAt = nowMs();'),
  ('    let minHoldElapsed = false;\n',''),
  ('      lastByteAt = Date.now();','      lastByteAt = nowMs();'),
  ('      const waited = Date.now() - startedAt;','      const waited = Math.floor(nowMs() - startedAt);'),
  ('      minHoldElapsed = true;','      const now = nowMs();'),
  ('      if (Date.now() - lastByteAt >= quiescenceMs) {','      if (now - startedAt >= holdMs && now - lastByteAt >= quiescenceMs) {'),
  ('      const now = Date.now();','      const now = nowMs();\n      // An early timeout or short attach cap cannot bypass the minimum.\n      if (now - startedAt < holdMs) return;'),
  ('      if (minHoldElapsed && now - lastByteAt >= quiescenceMs) {','      if (now - lastByteAt >= quiescenceMs) {')]
 for old,new in replacements:
  assert body.count(old)==1,old
  body=body.replace(old,new)
 return source[:start]+body+source[end:]


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 inputs=validate_reference(REFERENCE);out.mkdir(parents=True);runtime=out/'runtime';shutil.copytree(REFERENCE,runtime)
 original=(REFERENCE/LEAF).read_text();(runtime/LEAF).write_text(patch(original))
 changed=[str(Path(n).relative_to(REFERENCE)) for n,h in inputs.items() if sha(runtime/Path(n).relative_to(REFERENCE))!=h]
 assert changed==[LEAF] and all(sha(Path(n))==h for n,h in inputs.items())
 result={'passed':True,'audio_runtime_accepted':False,'reference_inputs':inputs,'changed_files':changed,
  'stager_sha256':sha(Path(__file__)),'files':{str(p.relative_to(runtime)):sha(p) for p in runtime.rglob('*') if p.is_file()},
  'scope':'Stage only: exact accepted key-framing runtime with CallSession post-training minimum/quiescence clocks changed to monotonic time, both callback paths checking the minimum, and integer elapsed logging. Minimum dominates a shorter attach cap. Config defaults, kernel/initrd, DSP/helper/backend, Telnet code and original runtime stay unchanged. No actual SIP/audio/BBS/physical acceptance.'}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'runtime':str(runtime),'changed_files':changed}))

if __name__=='__main__':main()
