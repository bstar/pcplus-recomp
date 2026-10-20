#!/usr/bin/env python3
"""Replay the linked private-JFT owner with explicit DOS PSP metadata."""
import json,struct
from pathlib import Path
from dos_image import DosImage
from build_aspect_process import ROOT,OUT,sha
from unicorn import UC_HOOK_INTR,UC_HOOK_INSN
from unicorn.x86_const import *


class Handles(DosImage):
    def __init__(self,count=20,offset=17,segment=0x8800):
        super().__init__(OUT/'ASPECT.EXE',OUT/'ASPECT.map')
        self.uc.mem_write(0x80000,b'\xcd\x20');self.uc.mem_write(0x80032,struct.pack('<3H',count,offset,segment))
        self.address=segment*16+offset;self.count=count
        if self.address+count<=0x100000:self.uc.mem_write(self.address,bytes((i%250)+1 for i in range(count)))
        self.uc.hook_add(UC_HOOK_INTR,self.interrupt)
        for instruction in (UC_X86_INS_IN,UC_X86_INS_OUT):self.uc.hook_add(UC_HOOK_INSN,self.forbidden,None,1,0,instruction)
    def forbidden(self,*args):raise AssertionError('JFT owner reached port IO')
    def interrupt(self,uc,number,data):
        assert number==0x21 and uc.reg_read(UC_X86_REG_AH)==0x62
        uc.reg_write(UC_X86_REG_BX,0x8000)
    def begin(self,descriptors,count=None):
        self.uc.mem_write(self.data_base+0xc000,struct.pack('<'+'H'*len(descriptors),*descriptors))
        return self.call('_process_handles_begin',[0xc000,len(descriptors) if count is None else count])
    def table(self):return bytes(self.uc.mem_read(self.address,self.count))


def main():
    cases=[]
    for capacity in (20,40,255):
        for offset in (0,17,65536-capacity):
            m=Handles(capacity,offset);original=m.table();descriptors=[0,2,4,6,8,10,capacity-1]
            assert m.begin(descriptors)==0 and m.get('_process_handles_active')==1
            expected=bytearray(original)
            for i in descriptors:expected[i]=255
            assert m.table()==expected and m.begin(descriptors)==1
            # An unrelated parent's entry is not rolled back by this owner.
            m.uc.mem_write(m.address+1,b'M');expected[1]=77;original=original[:1]+b'M'+original[2:]
            assert m.call('_process_handles_end')==0 and m.table()==original
            assert m.get('_process_handles_active')==0 and m.call('_process_handles_end')==1
            cases.append(dict(case='selected-only-and-external-table',capacity=capacity,offset=offset,passed=True))
    for descriptors,count in [([],0),([1]*8,8),([20],1),([1,1],2)]:
        m=Handles();original=m.table();assert m.begin(descriptors,count)==1
        assert m.table()==original and m.get('_process_handles_active')==0
        cases.append(dict(case='bad-descriptors',descriptors=descriptors,count=count,passed=True))
    for capacity,offset,segment in [(0,0,0x8800),(256,0,0x8800),(20,65530,0x8800),(20,0x1000,0xffff)]:
        m=Handles(capacity,offset,segment);assert m.begin([1])==1 and m.get('_process_handles_active')==0
        cases.append(dict(case='bad-table',capacity=capacity,offset=offset,segment=segment,passed=True))
    m=Handles();m.uc.mem_write(m.address+1,b'\xff');original=m.table();assert m.begin([1])==1 and m.table()==original
    cases.append(dict(case='closed-handle-reject',passed=True))
    m=Handles();original=m.table();assert m.begin([1,3])==0;m.uc.mem_write(m.address+1,b'Z')
    assert m.call('_process_handles_end')==1 and m.table()==original and m.get('_process_handles_active')==0
    cases.append(dict(case='foreign-slot-change-detected-and-owned-entries-restored',passed=True))
    report=dict(passed=True,cases=cases,binary_sha256=sha(OUT/'ASPECT.EXE'),manifest_sha256=sha(OUT/'manifest.json'),
        checker_sha256=sha(Path(__file__)),scope='Actual linked JFT code; DOS62 PSP is modeled. External-table/bounds/ownership evidence only, not execution under another DOS kernel.')
    (OUT/'handles.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Private DOS handles:',len(cases),'linked cases PASS')


if __name__=='__main__':main()
