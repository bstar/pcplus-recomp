#!/usr/bin/env python3
"""Independent Telnet protocol checks; this does not substitute for vendor BBS tests.

Byte expectations follow RFC854/1091/1073. A local socket unit peer additionally
proves the modem passes terminal queries through and awaits actual serial replies.
"""
import asyncio,hashlib,json,random
from pathlib import Path
from modem import Telnet,Modem
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/bbs-lab/protocol'

def aggregate(parts):
 codec=Telnet();display=bytearray();reply=bytearray()
 for part in parts:
  shown,sent=codec.feed(part);display.extend(shown);reply.extend(sent)
 assert not codec.pending,'Complete input left buffered bytes'
 return bytes(display),bytes(reply),codec

async def socket_passthrough(baud=38400,packet_delay_ms=0):
 # This peer is explicitly a protocol unit fixture, never a claimed vendor BBS.
 no_answer=asyncio.Event();peer_done=asyncio.Future()
 query=b'\x1b[6n';answer=b'\x1b[4;5R'
 async def peer(reader,writer):
  try:
   for part in [b'\xff',b'\xfd',b'\x18']:writer.write(part);await writer.drain();await asyncio.sleep(.001)
   assert await reader.readexactly(3)==b'\xff\xfb\x18'
   writer.write(query);await writer.drain()
   try:
    data=await asyncio.wait_for(reader.read(1),.1)
    raise AssertionError(('Modem fabricated terminal query reply',data))
   except asyncio.TimeoutError:no_answer.set()
   assert await reader.readexactly(len(answer))==answer
   writer.write(b'\x80\xff\xff\x1b[c');await writer.drain()
   assert await reader.readexactly(2)==b'\xff\xff'
   peer_done.set_result(True)
  except Exception as error:
   if not peer_done.done():peer_done.set_exception(error)
  finally:writer.close();await writer.wait_closed()
 bbs=await asyncio.start_server(peer,'127.0.0.1',0)
 modem=Modem('127.0.0.1',bbs.sockets[0].getsockname()[1],OUT/f'socket-{baud}-packet{packet_delay_ms}',soft=False,baud=baud,packet_delay_ms=packet_delay_ms)
 serial=await asyncio.start_server(modem.accept,'127.0.0.1',0)
 reader,writer=await asyncio.open_connection('127.0.0.1',serial.sockets[0].getsockname()[1])
 try:
  writer.write(b'ATD\r');await writer.drain()
  greeting=await asyncio.wait_for(reader.readuntil(f'CONNECT {baud}\r\n'.encode('ascii')),3)
  assert greeting.startswith(b'ATD\r')
  assert await asyncio.wait_for(reader.readexactly(len(query)),3)==query
  await asyncio.wait_for(no_answer.wait(),3)
  writer.write(answer);await writer.drain()
  assert await asyncio.wait_for(reader.readexactly(5),3)==b'\x80\xff\x1b[c'
  writer.write(b'\xff');await writer.drain()
  assert await asyncio.wait_for(peer_done,3)
 finally:
  writer.close();await writer.wait_closed();serial.close();await serial.wait_closed();bbs.close();await bbs.wait_closed()
  await asyncio.wait_for(modem.done.wait(),3);modem.save()
 assert modem.display==query+b'\x80\xff\x1b[c'
 assert answer in modem.wire_out

def main():
 OUT.mkdir(parents=True,exist_ok=True);cases=[]
 def check(name,fn):fn();cases.append({'case':name,'passed':True});print(name,'passed',flush=True)
 def fragmented():
  wire=(b'hello\xff\xfb\x01\x1b[6n\xff\xfd\x18\xff\xfa\x18\x01\xff\xf0'
        b'\x80\xff\xff\xff\xfd\x1f\xff\xfb\x03\xff\xfd\x63\xff\xfb\x2a'
        b'\x1b[>0c\xff\xfd\x20\xff\xfa\x20\x01\xff\xf0end')
  expected_display=b'hello\x1b[6n\x80\xff\x1b[>0cend'
  expected_reply=(b'\xff\xfd\x01\xff\xfb\x18\xff\xfa\x18\x00ANSI-BBS\xff\xf0'
        b'\xff\xfb\x1f\xff\xfa\x1f\x00\x50\x00\x19\xff\xf0\xff\xfd\x03'
        b'\xff\xfc\x63\xff\xfe\x2a\xff\xfb\x20\xff\xfa\x20\x0038400,38400\xff\xf0')
  partitions=[[wire],[bytes([v]) for v in wire]]
  partitions += [[wire[:split],wire[split:]] for split in range(1,len(wire))]
  rng=random.Random(854)
  for _ in range(64):
   parts=[];position=0
   while position<len(wire):
    size=rng.randint(1,11);parts.append(wire[position:position+size]);position+=size
   partitions.append(parts)
  for parts in partitions:
   display,reply,_=aggregate(parts);assert display==expected_display and reply==expected_reply
 check('IAC-options-subnegotiation-at-every-split-and-random-fragmentation',fragmented)
 def changes():
  codec=Telnet()
  for data,want in [(b'\xff\xfd\x18',b'\xff\xfb\x18'),(b'\xff\xfd\x18',b''),
    (b'\xff\xfe\x18',b'\xff\xfc\x18'),(b'\xff\xfe\x18',b''),(b'\xff\xfd\x18',b'\xff\xfb\x18'),
    (b'\xff\xfb\x01',b'\xff\xfd\x01'),(b'\xff\xfb\x01',b''),
    (b'\xff\xfc\x01',b'\xff\xfe\x01'),(b'\xff\xfb\x01',b'\xff\xfd\x01'),
    (b'\xff\xfd\xe9',b'\xff\xfc\xe9'),(b'\xff\xfb\xea',b'\xff\xfe\xea')]:
   assert codec.feed(data)==(b'',want),(data,want)
 check('negotiation-withdrawal-reenable-no-loops-and-unsupported-refusal',changes)
 def subnegotiation():
  wire=b'a\xff\xfa\x63x\xff\xffy\xff\xf0b\xff\xf1c\xff\xf9d'
  display,reply,codec=aggregate([bytes([v]) for v in wire])
  assert display==b'abcd' and reply==b''
  assert {'subnegotiation':'6378ff79'} in codec.events
  codec=Telnet();assert codec.feed(b'\xff\xfa\x18\x01\xff')==(b'',b'')
  assert codec.feed(b'\xf0')==(b'',b'\xff\xfa\x18\x00ANSI-BBS\xff\xf0')
  try:Telnet().feed(b'\xff\xfa\x18'+b'x'*16384)
  except ValueError:pass
  else:raise AssertionError('Unterminated oversized subnegotiation was not bounded')
 check('escaped-IAC-in-subnegotiation-control-stripping-and-incomplete-frame-bound',subnegotiation)
 def binary_ansi():
  raw=bytes(range(256));encoded=raw[:-1]+b'\xff\xff'
  assert Telnet.encode(raw)==encoded
  assert aggregate([bytes([v]) for v in encoded])[:2]==(raw,b'')
  terminal=(b'\x1b[6n\x1b[5n\x1b[c\x1b[>0c\x1bZ\x1b[25;80R'
            b'\x1b[?62;2c\x1b[>1;10;0c\x1b[?25l\x1b[?1h\r\n\0\x80\xdb')
  assert aggregate([bytes([v]) for v in terminal])[:2]==(terminal,b'')
  assert Telnet.encode(terminal)==terminal
 check('all-byte-IAC-escaping-and-ANSI-CPR-DA-passthrough-without-replies',binary_ansi)
 check('loopback-Hayes-Telnet-socket-awaits-real-serial-CPR-and-escapes-FF',lambda:asyncio.run(socket_passthrough()))
 def baud():
  codec=Telnet(19200)
  assert codec.feed(b'\xff\xfd\x20')==(b'',b'\xff\xfb\x20')
  assert codec.feed(b'\xff\xfa\x20\x01\xff\xf0')==(b'',b'\xff\xfa\x20\x0019200,19200\xff\xf0')
  asyncio.run(socket_passthrough(19200))
 check('selected-baud-in-modem-CONNECT-and-Telnet-TSPEED',baud)
 check('explicit30ms-buffer-still-awaits-DOS-CPR-and-preserves-binary-Telnet',lambda:asyncio.run(socket_passthrough(19200,30)))
 result={'passed':True,'cases':cases,'modem_source_sha256':hashlib.sha256((ROOT/'lab/bbs/modem.py').read_bytes()).hexdigest(),
  'references':['https://www.rfc-editor.org/rfc/rfc854','https://www.rfc-editor.org/rfc/rfc1091','https://www.rfc-editor.org/rfc/rfc1073'],
  'scope':'Protocol unit checks and isolated socket fixture only; actual vendor BBS/DOS compatibility evidence is separate. ANSI requests/replies are not fabricated by the modem.'}
 (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
