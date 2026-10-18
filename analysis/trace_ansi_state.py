#!/usr/bin/env python3
"""Focused REA inspection of shared CSI transitions in overlay-14 static context."""
import hashlib
import json
from pathlib import Path
from rea_mcp import ReaMcp

ROOT = Path(__file__).resolve().parent
image = ROOT / 'pcplus-overlay-entry-images/overlay-14.analysis.exe'
expected = '9072ab882b56031d3e981836250de0a87463d394c8cdb30db2a833db64059446'
assert hashlib.sha256(image.read_bytes()).hexdigest() == expected
output = ROOT / 'ansi-state'
output.mkdir(exist_ok=True)
rea = ReaMcp(output)
try:
    rea.call('open_binary',{'path':str(image),'provider_id':'ghidra'})
    for address in ['0x1e3f2','0x1e4a2','0x1ecd2']:
        for tool,suffix in [('procedure_assembly','asm'),('procedure_pseudo_code','c')]:
            result = rea.call(tool,{'procedure':address},address+'-'+suffix)
            content = result.get('normalized_result')
            if isinstance(content,str):
                prefix = ('/* REA pseudocode, not original source. Evidence '+result.get('evidence_id','unknown')+'. */\n') if suffix=='c' else ''
                (output/(address+'.'+suffix)).write_text(prefix+content+'\n')
            print(address,tool,result.get('evidence_id'),flush=True)
finally:
    rea.close()
