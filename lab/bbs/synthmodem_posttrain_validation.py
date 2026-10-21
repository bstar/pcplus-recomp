"""Exact-file validation for the separately staged minimum-hold candidate."""
import json
from pathlib import Path
from synthmodem_vm_control import ROOT,sha

LEDGER=ROOT/'docs/validation/synthmodem-posttrain-runtime.json'


def validate(runtime):
 runtime=Path(runtime).resolve();ledger=json.loads(LEDGER.read_text());assert ledger['passed']
 expected=ledger['files'];assert {str(p.relative_to(runtime)) for p in runtime.rglob('*') if p.is_file()}==set(expected)
 for n,h in expected.items():assert sha(runtime/n)==h,n
 return {str(runtime/n):h for n,h in expected.items()}
