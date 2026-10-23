#!/usr/bin/env python3
"""Analyst-only verification against genuine REA source mappings; not a build input."""
import hashlib,json,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    original=(ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE').read_bytes()
    digest=sha(original);assert digest=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
    records=json.loads((ROOT/'analysis/program-sound-01.rea.json').read_text())['records'];units=[]
    for name,start,end,read_start in [('switch',0x376d,0x378b,0x376d),('tone',0x7722,0x774d,0x7722),('bell',0x774e,0x775a,0x7722),('ports',0x7fa0,0x7fb7,0x7fa0)]:
        address=hex(0x10000+read_start)
        read=next(r for r in records if r['operation']=='read_bytes' and r['normalized_result']['address']==address)
        mapping=next(r for r in records if r['operation']=='address_to_file_offset' and r['normalized_result']['address']==address)
        assert read['subject']['digest']['sha256']==mapping['subject']['digest']['sha256']==digest
        at=mapping['normalized_result']['file_offset']+start-read_start;body=original[at:at+end-start]
        assert at==int.from_bytes(original[8:10],'little')*16+start
        assert read['normalized_result']['complete'] and body==bytes.fromhex(read['normalized_result']['bytes_hex'])[start-read_start:end-read_start]
        path=f'reconstruction/program_sound/{name}.asm'
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'unit.bin';subprocess.run(['nasm','-fbin','-I'+str(ROOT/'reconstruction/uart')+'/',str(ROOT/path),'-o',str(target)],check=True)
            assert target.read_bytes()==body,name
        units.append(dict(name=name,file=path,start=start,end=end,file_offset=at,bytes=len(body),sha256=sha(body),read_evidence=read['evidence_id'],mapping_evidence=mapping['evidence_id']))
    proof=dict(original_sha256=digest,units=units,recovered_bytes=sum(u['bytes'] for u in units),reused_delay='reconstruction/notice_window/pace.asm',limitations=['Native configured220/440Hz sound, PIT and speaker instructions only.','Exact calibrated busy delay blocks without UART service; calibration is an external platform responsibility.','Generic tone divides by unchecked frequency and uses wrapped16-bit duration multiplication.','Native sound clears speaker gate bits at completion, rather than restoring a preexisting active speaker owner.','Maintained bounded UART-serviced sound, application configuration binding and physical audio remain open.'])
    (ROOT/'reconstruction/program_sound/provenance.json').write_text(json.dumps(proof,indent=2)+'\n');print(proof['recovered_bytes'],'exact native sound bytes')
if __name__=='__main__':main()
