#!/usr/bin/env python3
"""Read-only owned upload-target preflight and fresh synthetic DOS source."""
import argparse,json
from pathlib import Path
from audio_synchronet import ROOT,snapshot,sha
from audio_synchronet_cancel_fixed import AREA,payload,metadata,stored_files,name_for

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--slot',type=int,choices=range(1,1000),default=2);a=p.parse_args();out=a.output.resolve();NAME=name_for(a.slot)
 assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 before=snapshot();files=stored_files();assert NAME not in files and not (AREA/NAME).exists()
 value=metadata(out,NAME,'before');assert value is None
 source=out/'source.bin';source.write_bytes(payload(NAME))
 checks=dict(target_absent_on_disk=not (AREA/NAME).exists(),target_absent_from_official_metadata=value is None,existing_files_unchanged=files==stored_files(),server_inputs_preserved=before==snapshot())
 result=dict(passed=all(checks.values()),checks=checks,server=before,existing_files=files,name=NAME,source_path=str(source.relative_to(ROOT)),source_sha256=sha(source),
  inputs={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audio_synchronet_cancel_fixed.py',ROOT/'lab/bbs/audio_synchronet.py',ROOT/'lab/bbs/synchronet.py']},
  captures_sha256={p.name:sha(p) for p in out.iterdir() if p.is_file()},scope='Read-only FileBase.get confirms fresh target is absent; source is unique deterministic11521 bytes under ignored build storage. No server/account/config change and no actual audio/DOS upload acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(checks));assert result['passed']
