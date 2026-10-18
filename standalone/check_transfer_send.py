#!/usr/bin/env python3
"""Exact sender/unwind/CRC with declared memory FILE/UART/UI fixtures."""
import argparse,binascii,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_SP,UC_X86_REG_IP
from dos_image import DosImage
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/transfer-send'
STATE=json.loads((ROOT/'reconstruction/transfer_send/provenance.json').read_text())['state']
CHECK=['send_block_size','send_block_number','send_buffer_used','send_blocks_counted','send_error_count','send_total_low','send_total_high','send_session_low','send_session_high']
class Send(DosImage):
 def __init__(self):super().__init__(OUT/'SEND.EXE',OUT/'transfer_send.map')
 def run(self,c):
  payload=c.get('data',b'ABC');script=c.get('script',[0x15,6,6]);self.uc.mem_write(self.symbols['fixture_file'],payload)
  self.uc.mem_write(self.symbols['fixture_script'],struct.pack('<'+'H'*len(script),*script))
  for name,value in [('fixture_file_length',len(payload)),('fixture_script_count',len(script)),('fixture_carrier',c.get('carrier',1)),('fixture_cancel',c.get('cancel',0)),('fixture_open_error',c.get('open_error',0)),('fixture_read_error',c.get('read_error',0)),('send_buffer_pointer',self.offset('send_payload_buffer')),('send_protocol',c.get('protocol',4)),('send_streaming_mode',c.get('stream',0)),('send_queued_count',c.get('queued',0)),('send_file_size_low',len(payload)),('send_file_size_high',0)]:self.put(name,value)
  answer=self.call('transfer_send_session',[self.offset('fixture_filename')],limit=3000000)
  return {'answer':answer,'wire':bytes(self.uc.mem_read(self.symbols['fixture_wire'],self.get('fixture_wire_count'))).hex(),'states':{n:self.get(n) for n in CHECK},'status':self.get('fixture_status'),'closed':self.get('fixture_close_count'),'timed_reads':self.get('fixture_timed_calls')}

def vectors():
 out=[]
 for length in [0,1,127,128,129,896,897,1023,1024,1025,2048,10000]:
  for protocol in [2,4]:
   for negotiation in [0x15,0x43,0x47]:
    out.append((f'normal-{length}-{protocol}-{negotiation}',dict(data=bytes(i%256 for i in range(length)),protocol=protocol,script=[negotiation]+[6]*100)))
 out += [('block-NAK-then-ACK',dict(script=[0x15,0x15,6,6])),('block-15-failed',dict(script=[0x43]+[0xffff]*15)),('EOT-NAK-then-ACK',dict(script=[0x15,6,0x15,6])),('EOT-10-failed',dict(script=[0x15,6]+[0xffff]*10)),('negotiation-150-timeouts',dict(script=[])),('negotiation-junk-15',dict(script=[0x33]*15)),('double-CAN',dict(script=[0x18,0x18])),('local-Escape',dict(cancel=1)),('carrier-loss',dict(carrier=0)),('open-error',dict(open_error=1)),('read-error',dict(read_error=1)),('delegate-U',dict(script=[0x55])),('delegate-W',dict(script=[0x57])),('delegate13',dict(protocol=13)),('metadata3-failure',dict(protocol=3)),('metadata5-failure',dict(protocol=5)),('streaming',dict(stream=1,script=[0x47,6])),('streaming-control-poll',dict(stream=1,queued=1,script=[0x47,0x55,6])),('EOT-double-CAN',dict(script=[0x15,6,0x18,0x18])),('block-double-CAN',dict(script=[0x15,0x18,0x18])),('single-CAN-consumes-next-byte',dict(script=[0x18,0x33,0x15,6,6]))]
 return out

def main():
 p=argparse.ArgumentParser();p.add_argument('--original',type=Path);a=p.parse_args();rows=[]
 for name,c in vectors():
  got=Send().run(c);wire=bytes.fromhex(got['wire']);rows.append((name,c,got))
  if name.startswith('normal-'):
   assert got['answer']==1 and wire[-1:]==b'\x04' and got['closed']==2,(name,got)
   pos=0;number=1;rest=c['data'];size=1024 if c['protocol']==2 and len(rest)>=1024 else 128;crc=c['script'][0]!=0x15
   while rest:
    chunk=rest[:size].ljust(size,b'\x1a');rest=rest[size:]
    trailer=binascii.crc_hqx(chunk,0).to_bytes(2,'big') if crc else bytes([sum(chunk)&255])
    expected=bytes([2 if size==1024 else 1,number&255,(~number)&255])+chunk+trailer
    assert wire[pos:pos+len(expected)]==expected,name;pos+=len(expected);number+=1
    if c['protocol']!=4 and len(rest)<897:size=128
   assert wire[pos:]==b'\x04',name
  elif name=='block-15-failed':assert got['answer']==0 and got['states']['send_error_count']==15 and got['states']['send_blocks_counted']==1 and got['status']==0 and len(wire)==15*133
  elif name=='EOT-10-failed':assert got['answer']==0 and wire[-10:]==b'\x04'*10 and got['timed_reads']==12
  elif name=='negotiation-150-timeouts':assert got['answer']==0 and got['timed_reads']==150 and got['status']==0 and not wire
  elif name=='negotiation-junk-15':assert got['answer']==0 and got['timed_reads']==15 and not wire
  elif name in ('double-CAN','local-Escape','EOT-double-CAN','block-double-CAN'):
   assert got['answer']==0 and got['status']==11 and (not wire if name in ('double-CAN','local-Escape') else bool(wire))
   if name=='EOT-double-CAN':assert got['closed']==3

  elif name=='carrier-loss':assert got['answer']==0 and got['status']==15 and not wire
  elif name=='open-error':assert got['answer']==0 and got['status']==13 and got['closed']==0
  elif name=='read-error':assert got['answer']==0 and got['status']==4 and not wire
  elif name.startswith('delegate'):assert got['answer']==0 and not wire
  elif name.startswith('metadata'):assert got['answer']==0 and got['status']==10 and not wire
  else:assert got['answer']==1,(name,got)
 if a.original:
  from check_directory_dial_original import Original,DATA,EXPECTED
  image=a.original.read_bytes();assert hashlib.sha256(image).hexdigest()==EXPECTED
  overlays=[o for o in json.loads((ROOT/'analysis/pcplus-overlays/manifest.json').read_text())['overlays'] if o['id']==21]
  class Native(Original):
   def __init__(self,c):
    super().__init__(image,overlays);self.c=c;self.script=list(c.get('script',[0x15,6,6]));self.data=c.get('data',b'ABC');self.position=0;self.wire=bytearray();self.closed=0;self.status=0;self.timed_reads=0
    self.uc.mem_write(DATA+0x39fc,image[153936+0x39fc:153936+0x3bfc]);self.uc.mem_write(DATA+0x6000,b'OWNED.BIN\0');self.uc.mem_write(DATA+0xceea,b'\0')
    for at,value in [(0x39c0,0x5000),(0x3996,c.get('protocol',4)),(0xcdcc,c.get('stream',0)),(0x9006,len(self.data)),(0x9008,0),(0x8e20,c.get('queued',0)),(0xcd80,0),(0xcd8a,0),(0x8ffa,0),(0x8ffc,0),(0xcb2c,0),(0xcb2e,0)]:self.put(at,value)
   def hook(self,u,at,size,_):
    if at==self.stop:u.emu_stop();return
    services={0xd656,0xefb0,0xd08f,0x841a,0xe498,0x3ea4,0x6bf0,0xee10,0xaad9,0x3f4b,0x4861,0xd083,0xd0a7,0xabca,0x8318,0xe5da,0xe762,0xf0d4,0x845a,0xab0b,0xab92,0xe322,0xaa65,0x5ca0}
    address=at-0x10000
    if address not in services:return
    sp=u.reg_read(UC_X86_REG_SP);ret=struct.unpack('<H',u.mem_read(DATA+sp,2))[0];args=struct.unpack('<4H',u.mem_read(DATA+sp+2,8));cleanup=0;answer=0
    if address in (0xaad9,0xaa65,0x5ca0):
     if address==0xaad9:self.timed_reads+=1;cleanup=2
     answer=self.script.pop(0) if self.script else 0xffff
    elif address==0x841a:answer=0 if self.c.get('open_error') else 1
    elif address==0x845a:
     answer=0xffff if self.c.get('read_error') else min(len(self.data)-self.position,args[2]);
     if answer!=0xffff:u.mem_write(DATA+args[0],self.data[self.position:self.position+answer]);self.position+=answer
    elif address==0x8318:self.closed+=1
    elif address==0xe498:self.status=args[0]
    elif address==0x3f4b:answer=self.c.get('cancel',0)
    elif address==0x4861:answer=self.c.get('carrier',1)
    elif address==0x3ea4:answer=0x6000
    elif address==0x6bf0:cleanup=6
    elif address==0xab0b:self.wire.append(args[0]&255);cleanup=2
    elif address==0xab92:self.wire.extend(u.mem_read(DATA+args[1],args[0]));cleanup=4
    u.reg_write(UC_X86_REG_AX,answer);u.reg_write(UC_X86_REG_SP,sp+2+cleanup);u.reg_write(UC_X86_REG_IP,ret)
  for name,c,want in rows:
   m=Native(c);m.call(0xde58,[0x6000]);got={'answer':m.uc.reg_read(UC_X86_REG_AX),'wire':bytes(m.wire).hex(),'states':{n:m.get(int(at,16)) for at,n in STATE.items() if n in CHECK},'status':m.status,'closed':m.closed,'timed_reads':m.timed_reads}
   assert got==want,(name,got,want)
 proof={'passed':True,'binary_sha256':hashlib.sha256((OUT/'SEND.EXE').read_bytes()).hexdigest(),'inputs':len(rows),'original_comparisons':len(rows) if a.original else 0,'scope':'Exact session/cancel/setjmp/longjmp/CRC instructions with explicit synthetic FILE/UART/time/UI/alternateprotocol boundaries. No actual files, serialdevice or complete application.'};(OUT/'checks.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
