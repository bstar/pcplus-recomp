#!/usr/bin/env python3
"""Independent bounds/byte-preservation checks for the optional modem experiment."""
import asyncio,hashlib,json
from pathlib import Path
from modem import Modem,serial_packets
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/bbs-lab/packetization'

async def check():
 cases=[]
 async def collect(reader,delay):return [p async for p in serial_packets(reader,delay)]
 # All256 byte values, NUL, XON/XOFF, ANSI, EOF1A and IAC must survive unchanged.
 raw=bytes(range(256))*8+b'\x1b[H\x1b[2~\x00\x1a\xff'
 for delay in (0,30,100):
  r=asyncio.StreamReader();r.feed_data(raw);r.feed_eof()
  packets=await collect(r,delay)
  assert b''.join(packets)==raw
  assert all(0<len(p)<=256 for p in packets) if delay else True
 cases.append('all-byte-binary-preservation-and256-byte-bound')
 r=asyncio.StreamReader();r.feed_data(b'A')
 packets=serial_packets(r,0)
 assert await asyncio.wait_for(anext(packets),.2)==b'A'
 await packets.aclose()
 cases.append('default-first-byte-immediate-without-EOF')
 r=asyncio.StreamReader();r.feed_data(b'\x1b')
 packets=serial_packets(r,30)
 pending=asyncio.create_task(anext(packets))
 await asyncio.sleep(.005);assert not pending.done();r.feed_data(b'[H')
 assert await asyncio.wait_for(pending,.2)==b'\x1b[H'
 r.feed_data(b'\x1b');r.feed_eof()
 assert await asyncio.wait_for(anext(packets),.2)==b'\x1b'
 await packets.aclose()
 cases.append('fragmented-escape-grouped-and-lone-escape-flushed-at-EOF')
 r=asyncio.StreamReader();r.feed_data(b'\x1b');packets=serial_packets(r,30)
 assert await asyncio.wait_for(anext(packets),.2)==b'\x1b'
 await packets.aclose()
 cases.append('standalone-Escape-released-at-deadline-with-connection-open')
 # An interbyte timeout would wait until the producer ends. The first-byte
 # deadline must flush while a stream is still arriving, well below256 bytes.
 r=asyncio.StreamReader();packets=serial_packets(r,30)
 async def trickle():
  for _ in range(100):r.feed_data(b'x');await asyncio.sleep(.01)
  r.feed_eof()
 producer=asyncio.create_task(trickle())
 try:
  first=await asyncio.wait_for(anext(packets),.3)
  assert first and not producer.done() and len(first)<30
 finally:
  producer.cancel();await asyncio.gather(producer,return_exceptions=True);await packets.aclose()
 cases.append('continuous-trickle-first-byte-deadline-prevents-unbounded-delay')
 for invalid in (-1,101):
  try:await anext(serial_packets(asyncio.StreamReader(),invalid))
  except ValueError:pass
  else:raise AssertionError('Invalid delay accepted')
 try:Modem('127.0.0.1',1,OUT,soft=True,packet_delay_ms=30)
 except ValueError:pass
 else:raise AssertionError('Delayed software flow experiment accepted')
 cases.append('invalid-delay-and-software-flow-rejected')
 OUT.mkdir(parents=True,exist_ok=True)
 result={'passed':True,'cases':cases,'modem_source_sha256':hashlib.sha256((ROOT/'lab/bbs/modem.py').read_bytes()).hexdigest(),'scope':'Unit fixtures establish byte preservation, immediate default, bounded packet size and first-byte timeout. They do not establish TCP receive boundaries, actual BBS or physical modem behavior.'}
 (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 for c in cases:print(c,'PASS')
if __name__=='__main__':asyncio.run(check())
