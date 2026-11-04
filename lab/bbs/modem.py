#!/usr/bin/env python3
"""Private loopback Hayes/Telnet modem model for DOS compatibility tests.

Only modem-layer negotiation is answered here. ANSI/device/cursor requests pass
unchanged to the actual DOS terminal; this proxy never fabricates those replies.
"""
import asyncio,json,time
from pathlib import Path
IAC,SB,SE,WILL,WONT,DO,DONT=255,250,240,251,252,253,254

async def serial_packets(reader,delay_ms=0):
 """Optional byte-transparent experiment: first-byte deadline, at most256 bytes.

 This groups writes, not TCP receive events. It never recognizes ANSI or alters
 bytes. The default preserves immediate forwarding and its stock-server failures.
 """
 if not 0<=delay_ms<=100:raise ValueError('Packet delay must be0..100 milliseconds')
 if not delay_ms:
  while data:=await reader.read(4096):yield data
  return
 loop=asyncio.get_running_loop()
 while first:=await reader.read(256):
  packet=bytearray(first);deadline=loop.time()+delay_ms/1000;eof=False
  while len(packet)<256:
   remaining=deadline-loop.time()
   if remaining<=0:break
   try:part=await asyncio.wait_for(reader.read(256-len(packet)),remaining)
   except asyncio.TimeoutError:break
   if not part:eof=True;break
   packet.extend(part)
  yield bytes(packet)
  if eof:return

class Telnet:
 def __init__(self,baud=38400):
  self.baud=baud;self.pending=bytearray();self.local=set();self.remote=set();self.refused_local=set();self.refused_remote=set();self.events=[]
 def feed(self,data):
  self.pending.extend(data);out=bytearray();reply=bytearray();i=0
  while i<len(self.pending):
   if self.pending[i]!=IAC:out.append(self.pending[i]);i+=1;continue
   if i+1>=len(self.pending):break
   command=self.pending[i+1]
   if command==IAC:out.append(IAC);i+=2;continue
   if command in (DO,DONT,WILL,WONT):
    if i+2>=len(self.pending):break
    option=self.pending[i+2];self.events.append({'command':command,'option':option})
    if command==DO:
     if option in (0,3,24,31,32):
      if option not in self.local:
       self.local.add(option);reply.extend([IAC,WILL,option])
       if option==31:reply.extend(bytes([IAC,SB,31,0,80,0,25,IAC,SE]))
     elif option not in self.refused_local:self.refused_local.add(option);reply.extend([IAC,WONT,option])
    elif command==WILL:
     if option in (0,1,3):
      if option not in self.remote:self.remote.add(option);reply.extend([IAC,DO,option])
     elif option not in self.refused_remote:self.refused_remote.add(option);reply.extend([IAC,DONT,option])
    elif command==DONT:
     if option in self.local:self.local.remove(option);reply.extend([IAC,WONT,option])
    elif command==WONT:
     if option in self.remote:self.remote.remove(option);reply.extend([IAC,DONT,option])
    i+=3;continue
   if command==SB:
    j=i+2;payload=bytearray();complete=False
    while j<len(self.pending):
     if self.pending[j]==IAC:
      if j+1>=len(self.pending):break
      if self.pending[j+1]==SE:j+=2;complete=True;break
      if self.pending[j+1]==IAC:payload.append(IAC);j+=2;continue
     payload.append(self.pending[j]);j+=1
    if not complete:break
    self.events.append({'subnegotiation':payload.hex()})
    if bytes(payload)==b'\x18\x01':reply.extend(bytes([IAC,SB,24,0])+b'ANSI-BBS'+bytes([IAC,SE]))
    elif bytes(payload)==b'\x20\x01':reply.extend(bytes([IAC,SB,32,0])+f'{self.baud},{self.baud}'.encode('ascii')+bytes([IAC,SE]))
    i=j;continue
   # Two-byte Telnet commands are modem control, not terminal display bytes.
   self.events.append({'command':command});i+=2
  del self.pending[:i]
  if len(self.pending)>16384:raise ValueError('Oversized Telnet subnegotiation')
  return bytes(out),bytes(reply)
 @staticmethod
 def encode(data):return data.replace(b'\xff',b'\xff\xff')

class GuardedHangup:
 """Optional fixture model for the configured guarded +++/ATH sequence.

 It is not a complete Hayes escape/command interpreter. Without both quiet
 guards, all bytes pass unchanged. Partial candidates are bounded and flushed.
 """
 def __init__(self,guard,now):
  if not .1<=guard<=2:raise ValueError('Fixture guard must be .1..2 seconds')
  self.guard=guard;self.last=now;self.pending=bytearray()
 def expire(self,now):
  limit=self.guard if len(self.pending)<3 else 2
  if self.pending and now-self.last>=limit:
   data=bytes(self.pending);self.pending.clear();self.last=now;return data
  return b''
 def feed(self,data,now):
  output=bytearray(self.expire(now));matched=False
  for byte in data:
   quiet=now-self.last
   if not self.pending:
    if byte==43 and quiet>=self.guard:self.pending.append(byte)
    else:output.append(byte)
   else:
    n=len(self.pending);expected=b'+++ATH\r'[n]
    valid=byte==expected and (n!=3 or quiet>=self.guard)
    if valid:
     self.pending.append(byte)
     if len(self.pending)==7:self.pending.clear();matched=True
    else:output.extend(self.pending);output.append(byte);self.pending.clear()
   self.last=now
  return bytes(output),matched

class Modem:
 def __init__(self,host,port,output,*,soft=False,baud=38400,raw=False,packet_delay_ms=0,guarded_hangup_seconds=None):
  assert host in ('127.0.0.1','localhost','::1'),'Lab endpoints must be loopback'
  if not 0<=packet_delay_ms<=100:raise ValueError('Packet delay must be0..100 milliseconds')
  if soft and packet_delay_ms:raise ValueError('Buffering experiment requires NONE/HARD; software flow remains immediate')
  self.packet_delay_ms=packet_delay_ms
  self.host,self.port,self.output=host,port,Path(output);self.soft,self.baud,self.raw=soft,baud,raw
  self.output.mkdir(parents=True,exist_ok=True);self.ready=asyncio.Event();self.done=asyncio.Event();self.events=[];self.codec=Telnet(baud)
  self.display=bytearray();self.keyboard=bytearray();self.wire_in=bytearray();self.wire_out=bytearray();self.serial_out=bytearray()
  self.pause=asyncio.Event();self.pause.set();self.start=time.monotonic();self.connected=False
  self.hangup_guard=GuardedHangup(guarded_hangup_seconds,self.start) if guarded_hangup_seconds is not None else None
 def event(self,kind,**values):self.events.append({'seconds':round(time.monotonic()-self.start,3),'kind':kind,**values})
 async def accept(self,reader,writer):
  if self.connected:writer.close();return
  self.connected=True;self.event('serial-connected');self.ready.set();line=bytearray();up_reader=up_writer=None;task=None;guard_task=None
  async def forward(data):
   forward=bytearray()
   for value in data:
    if self.soft and value in (17,19):
     self.pause.set() if value==17 else self.pause.clear();self.event('serial-flow',value=value)
    else:forward.append(value)
   if forward and up_writer is not None:
    packet=bytes(forward) if self.raw else self.codec.encode(bytes(forward))
    if self.packet_delay_ms:self.event('buffered-serial-write',wire_offset=len(self.wire_out),wire_bytes=len(packet),serial_bytes=len(forward))
    self.wire_out.extend(packet);up_writer.write(packet);await up_writer.drain()
  async def expire_guard():
   while True:
    await asyncio.sleep(.01)
    if up_writer is not None:await forward(self.hangup_guard.expire(time.monotonic()))
  if self.hangup_guard:guard_task=asyncio.create_task(expire_guard())
  try:
   async for data in serial_packets(reader,self.packet_delay_ms):
    self.keyboard.extend(data)
    if up_writer is None:
     for value in data:
      writer.write(bytes([value]))
      if value in (10,13):
       command=bytes(line).strip().upper();line.clear()
       if not command:continue
       self.event('modem-command',command=command.decode('ascii','replace'))
       if command.startswith(b'ATD'):
        up_reader,up_writer=await asyncio.open_connection(self.host,self.port)
        writer.write(f'\r\nCONNECT {self.baud}\r\n'.encode('ascii'));await writer.drain();self.event('bbs-connected')
        task=asyncio.create_task(self.downstream(up_reader,up_writer,writer))
        if self.hangup_guard:self.hangup_guard.last=time.monotonic();self.hangup_guard.pending.clear()
       elif command in (b'AT',b'ATZ',b'ATE1',b'ATE0'):writer.write(b'\r\nOK\r\n')
       else:writer.write(b'\r\nERROR\r\n')
      else:line.append(value)
     await writer.drain()
    else:
     matched=False
     if self.hangup_guard:data,matched=self.hangup_guard.feed(data,time.monotonic())
     await forward(data)
     if matched:
      self.event('guarded-hangup',guard_seconds=self.hangup_guard.guard)
      if task:task.cancel();await asyncio.gather(task,return_exceptions=True);task=None
      up_writer.close();up_writer=None
      writer.write(b'\r\nOK\r\n');await writer.drain()
   self.event('serial-eof')
  except (OSError,ConnectionError,asyncio.IncompleteReadError) as error:self.event('error',message=str(error))
  finally:
   if guard_task:guard_task.cancel();await asyncio.gather(guard_task,return_exceptions=True)
   if task:task.cancel();await asyncio.gather(task,return_exceptions=True)
   if up_writer:up_writer.close()
   writer.close();self.done.set();self.save()
 async def downstream(self,reader,upstream,serial):
  while data:=await reader.read(2048):
   self.wire_in.extend(data)
   display,reply=(data,b'') if self.raw else self.codec.feed(data)
   if reply:self.wire_out.extend(reply);upstream.write(reply);await upstream.drain()
   self.display.extend(display)
   for start in range(0,len(display),32):
    await self.pause.wait();block=display[start:start+32]
    self.serial_out.extend(block);serial.write(block);await serial.drain()
    await asyncio.sleep(len(block)*10/self.baud)
  self.event('bbs-eof')
 def save(self):
  for name,data in [('bbs-wire.bin',self.wire_in),('bbs-sent.bin',self.wire_out),('display.bin',self.display),('serial-received.bin',self.keyboard),('serial-sent.bin',self.serial_out)]:
   (self.output/name).write_bytes(data)
  (self.output/'modem.json').write_text(json.dumps({'events':self.events,'telnet':self.codec.events,'flow_mode':'software' if self.soft else 'none','raw':self.raw,'baud':self.baud,'guarded_hangup_seconds':self.hangup_guard.guard if self.hangup_guard else None,'packet_delay_ms':self.packet_delay_ms,'packet_limit_bytes':256 if self.packet_delay_ms else None,'limitations':['Test modem model, not physical Wi-Fi modem firmware.','Telnet belongs to the explicit raw upstream when selected; all ANSI replies come from actual DOS.','ATD connects only configured loopback test BBS.','Optional guarded +++/ATH model matches the declared fixture guard; it is not a complete Hayes interpreter.','Optional buffering groups serial bytes without parsing them; TCP receive boundaries remain uncontrolled.']},indent=2)+'\n')
