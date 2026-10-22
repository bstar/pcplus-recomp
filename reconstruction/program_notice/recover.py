#!/usr/bin/env python3
"""Analyst-only notice provenance from genuine MZ mappings and saved REA evidence."""
import hashlib,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def main():
    original=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
    digest=hashlib.sha256(original).hexdigest();assert digest=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
    rows=json.loads((ROOT/'analysis/program-notice-01.rea.json').read_text())['records']
    read=next(r for r in rows if r['operation']=='read_bytes' and r['normalized_result']['address']=='0x1427f')
    mapping=next(r for r in rows if r['operation']=='address_to_file_offset' and r['normalized_result']['address']=='0x1427f')
    dossier=next(r for r in rows if r['operation']=='analyze_function' and r['parameters']['procedure']=='0x1429a')
    for r in (read,mapping,dossier):assert r['subject']['digest']['sha256']==digest
    offset=mapping['normalized_result']['file_offset'];assert offset==int.from_bytes(original[8:10],'little')*16+0x427f
    data=original[offset:offset+190];assert read['normalized_result']['complete'] and bytes.fromhex(read['normalized_result']['bytes_hex'])==data
    with tempfile.TemporaryDirectory() as temp:
        binary=Path(temp)/'core.bin'
        subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/',str(ROOT/'reconstruction/program_notice/core.asm'),'-o',str(binary)],check=True)
        assert binary.read_bytes()==data
    proof=dict(original_sha256=digest,file='reconstruction/program_notice/core.asm',start=0x427f,end=0x433d,file_offset=offset,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),read_evidence=read['evidence_id'],mapping_evidence=mapping['evidence_id'],function_evidence=dossier['evidence_id'],entries={'error_bx':0x427f,'message_stack':0x4288,'window':0x429a},limitations=['Exact native controller and wrapper recovery only. Dependency execution is separately declared.','Original signed/16-bit centering is not clipped; long messages can generate invalid window coordinates.','Native wait counts three clock changes, has no UART service, and cannot finish without a key if the clock stops.','No application publication or whole PROGRAM/window/ASPECT completion.'])
    (ROOT/'reconstruction/program_notice/provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
    print('Recovered',len(data),'exact timed-notice bytes')
if __name__=='__main__':main()
