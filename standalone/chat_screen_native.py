"""Native3D94 CPU reference; explicit BIOS09/02 and scroll2530 boundaries."""
import struct
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_INTR
from unicorn.x86_const import *


class NativePane:
    def __init__(self,units,rows,attribute,bar,clear):
        self.rows=rows;self.attribute=attribute;self.bar=bar
        divider=33 if rows>28 else 19
        self.panes=[[1,divider-1,divider-1,0],[divider+1,rows-2,divider+1,0]]
        self.frame=[clear*256+32]*(rows*80)
        for row in (0,divider,rows-1):self.frame[row*80:row*80+80]=[bar*256+32]*80
        for at,label in ((36,b'REMOTE'),(divider*80+37,b'LOCAL'),((rows-1)*80+25,b'Chat Mode - Press ESC to end')):
            self.frame[at:at+len(label)]=[bar*256+b for b in label]
        self.u=Uc(UC_ARCH_X86,UC_MODE_16);self.u.mem_map(0,0x100000)
        for address,code in units.items():self.u.mem_write(0x10000+address,code)
        self.u.mem_write(0x12530,b'\xc2\x08\x00')
        for at,value in ((0x1f70,attribute),(0x3258,79),(0x7a7a,160),(0x325a,80),
                         (0x7a66,1),(0x900c,0),(0xcdfa,0),(0x3734,0)):
            self.word(at,value)
        self.u.hook_add(UC_HOOK_CODE,self.code)
        self.u.hook_add(UC_HOOK_INTR,self.interrupt)
        self.stopped=False;self.hardware=(0,0)

    def word(self,at,value):self.u.mem_write(0x50000+at,struct.pack('<H',value&65535))
    def read(self,at):return struct.unpack('<H',self.u.mem_read(0x50000+at,2))[0]

    def code(self,u,address,size,_):
        if address==0x1f800:self.stopped=True;u.emu_stop()
        elif address==0x12530:
            sp=u.reg_read(UC_X86_REG_SP)
            attr,bottom,top,lines=[self.read(sp+n) for n in (2,4,6,8)]
            assert lines==1 and top&255==0 and bottom&255==79
            first,last=top>>8,bottom>>8
            assert 0<=first<=last<self.rows and attr==self.attribute
            self.frame[first*80:last*80]=self.frame[(first+1)*80:(last+1)*80]
            self.frame[last*80:(last+1)*80]=[(attr<<8)|32]*80

    def interrupt(self,u,number,_):
        assert number==0x10
        ax=u.reg_read(UC_X86_REG_AX);bx=u.reg_read(UC_X86_REG_BX)
        if ax>>8==2:
            dx=u.reg_read(UC_X86_REG_DX);self.hardware=(dx>>8,dx&255)
        else:
            assert ax>>8==9 and u.reg_read(UC_X86_REG_CX)==1 and bx>>8==0
            row,col=self.hardware;assert 0<=row<self.rows and 0<=col<80
            self.frame[row*80+col]=((bx&255)<<8)|(ax&255)

    def put(self,which,value):
        first,last,row,col=self.panes[which]
        self.hardware=(row,col);self.stopped=False
        for at,v in ((0x399c,row),(0x399e,col),(0x39a2,row),(0x39a0,col),(0x3348,col),
                     (0x3344,row*160+col*2),(0x3346,row*80+col)):
            self.word(at,v)
        for i,v in enumerate((0xf800,value,first,last)):self.word(0xf000+i*2,v)
        for reg,v in ((UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x5000),(UC_X86_REG_SS,0x5000),
                      (UC_X86_REG_SP,0xf000),(UC_X86_REG_BP,0x1234),(UC_X86_REG_SI,0x5678),(UC_X86_REG_DI,0x9abc),
                      (UC_X86_REG_EFLAGS,0x202)):
            self.u.reg_write(reg,v)
        self.u.emu_start(0x13d94,0,count=10000)
        assert self.stopped and self.u.reg_read(UC_X86_REG_SP)==0xf002
        assert self.u.reg_read(UC_X86_REG_BP)==0x1234 and self.u.reg_read(UC_X86_REG_SI)==0x5678 and self.u.reg_read(UC_X86_REG_DI)==0x9abc
        assert self.u.reg_read(UC_X86_REG_DS)==self.u.reg_read(UC_X86_REG_SS)==0x5000
        row,col=self.read(0x399c),self.read(0x399e)
        assert self.hardware==(row,col)
        self.panes[which][2:]=[row,col]
