#!/usr/bin/env python3
"""Verify linked process-bank placement, bridges and all object transfers."""
import json,re,subprocess
from pathlib import Path
from build_aspect_process import ROOT,sha
def main():
    reports={}
    for name,baseline in [('terminal-process-bank','terminal-exit'),('terminal-process-bank-mouse','terminal-exit-mouse')]:
        out=ROOT/'build'/name;manifest=json.loads((out/'manifest.json').read_text())
        assert manifest['banked_process'] and manifest['terminal_exit_guard'] and manifest['experimental_external_render']
        assert manifest['binary_sha256']==sha(out/'TERMINAL.EXE')
        for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
        layout=manifest['memory_layout'];assert layout['process_bridge_pairs_verified']==1
        assert layout['process_near_entry_bytes']==22 and layout['process_bank_bytes']==635
        objects=[p for p in out.glob('unit-*.obj') if b'src/process/dos_exec.asm' in p.read_bytes()]
        assert len(objects)==1
        listing=out/'process-bank-audit.dis'
        subprocess.run(['wdis','-e','-l='+str(listing),str(objects[0])],check=True)
        sections=re.split(r'^Segment:\s+(\w+)[^\n]*\n',listing.read_text(),flags=re.M)
        transfers=[];far=0
        for index in range(1,len(sections),2):
            segment,text=sections[index:index+2]
            if segment not in ['_TEXT','PROCESS_CODE']:continue
            labels=set(re.findall(r'^[0-9a-f]{4}\s+([\w$]+):\s*$',text,re.M|re.I))
            for match in re.finditer(r'^([0-9a-f]{4})\s+((?:[0-9a-f]{2}\s+)+)(call|j\w+|loop)\s+(\S+)',text,re.M|re.I):
                at,encoded,operation,target=match.groups();opcode=encoded.split()[0].upper()
                if opcode in ['9A','EA']:
                    assert segment=='_TEXT' and operation=='call' and target=='PROCESS_GROUP:process_run_far'
                    far+=1
                else:assert target in labels,(segment,at,operation,target)
                transfers.append(dict(segment=segment,offset=at,operation=operation,target=target,opcode=opcode))
        assert far==1 and len(transfers)>30
        old=json.loads((ROOT/'build'/baseline/'manifest.json').read_text())['memory_layout']
        assert layout['near_bytes']==old['near_bytes']
        saved=old['resident_code_bytes']-layout['resident_code_bytes'];assert saved==(592 if name.endswith('mouse') else 594)
        report=dict(passed=True,binary_sha256=manifest['binary_sha256'],object_sha256=sha(objects[0]),listing_sha256=sha(listing),
            transfers=transfers,near_code_saved=saved,near_spare=layout['resident_code_spare_bytes'],bank_bytes=layout['process_bank_bytes'],
            sources=manifest['sources'],checker_sha256=sha(Path(__file__)))
        (out/'bank-checks.json').write_text(json.dumps(report,indent=2)+'\n');reports[name]=report
    print('Both process banks: one far crossing, all other transfers stay in their object segment;594/592 near bytes saved')
if __name__=='__main__':main()
