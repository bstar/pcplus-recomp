"""DOS file/namespace additions to the existing live PROGRAM hardware model."""
import struct
from unicorn.x86_const import *
from check_program_actions_live import LiveProgram
from check_setup_model import image
from check_startup_import import terminal_expected
from check_modem_import import expected as modem_expected

class LiveSettings(LiveProgram):
 def __init__(self,path=b'TEST.PRM',**kw):
  self.raw=image();self.after_raw=None;self.cwd=b'D:\\WORK';self.canonical_error=0
  self.open_error=self.read_error=self.close_error=0;self.position=0;self.file_calls=[];self.local_text=bytearray();self.child_cwd=None
  super().__init__(child_status=0,**kw)
  self.put('terminal_option_mask',48)
  self.uc.mem_write(self.symbols['terminal_config_path'],path.ljust(64,b'\0'))
  self.uc.mem_write(self.symbols['terminal_configuration_values'],terminal_expected(self.raw))
  self.uc.mem_write(self.symbols['terminal_modem_settings'],modem_expected(self.raw))
  self.uc.mem_write(self.symbols['terminal_dial_target'],b'Local.Example:23'.ljust(64,b'\0'))
  self.call('terminal_apply_configuration')
  # Existing LiveProgram owns a38400 UART. Its negotiated effective rate may
  # differ from the source PRM's1200; binding must remember the SOURCE rate.
  self.put('terminal_baud_low',38400);self.put('terminal_baud_high',0)
  assert self.call('terminal_connection_prepare')==0
  assert self.call('terminal_reset_capture')==0
  self.call('terminal_setup_bind')
 def string(self,segment,pointer):return bytes(self.uc.mem_read(segment*16+pointer,128)).split(b'\0')[0]
 def interrupt(self,u,number,data):
  ax=u.reg_read(UC_X86_REG_AX);ah=ax>>8
  if number==0x10 and ah==14:self.local_text.append(ax&255)
  if number==0x21 and ax==0x6000:
   source=self.string(u.reg_read(UC_X86_REG_DS),u.reg_read(UC_X86_REG_SI))
   dest=u.reg_read(UC_X86_REG_ES)*16+u.reg_read(UC_X86_REG_DI)
   canonical=source.upper() if len(source)>2 and source[1:2]==b':' else self.cwd+b'\\'+source.upper()
   self.file_calls.append(('canonical',source,canonical))
   if not self.canonical_error:u.mem_write(dest,canonical+b'\0')
   u.reg_write(UC_X86_REG_AX,self.canonical_error);self.set_carry(bool(self.canonical_error));return
  if number==0x21 and ah==0x3d and ax&255==0:
   path=self.string(u.reg_read(UC_X86_REG_DS),u.reg_read(UC_X86_REG_DX));self.file_calls.append(('open',path))
   self.position=0;u.reg_write(UC_X86_REG_AX,self.open_error or 7);self.set_carry(bool(self.open_error));return
  if number==0x21 and ah==0x3f:
   assert u.reg_read(UC_X86_REG_BX)==7
   n=u.reg_read(UC_X86_REG_CX);pointer=u.reg_read(UC_X86_REG_DS)*16+u.reg_read(UC_X86_REG_DX)
   block=self.raw[self.position:self.position+n];self.file_calls.append(('read',len(block)))
   if not self.read_error:u.mem_write(pointer,block);self.position+=len(block)
   u.reg_write(UC_X86_REG_AX,self.read_error or len(block));self.set_carry(bool(self.read_error));return
  if number==0x21 and ah==0x3e and u.reg_read(UC_X86_REG_BX)==7:
   self.file_calls.append(('close',7));u.reg_write(UC_X86_REG_AX,self.close_error);self.set_carry(bool(self.close_error));return
  answer=super().interrupt(u,number,data)
  if number==0x21 and ax==0x4b00 and not self.exec_error:
   if self.after_raw is not None:self.raw=self.after_raw
   if self.child_cwd is not None:self.cwd=self.child_cwd
  return answer
