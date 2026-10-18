#!/usr/bin/env python3
"""Actual source-only DOS sender through real DOSBox-X UART; loopback only."""
import asyncio,hashlib,json,os,subprocess
from pathlib import Path
from test_terminal import SAMPLER
ROOT=Path(__file__).resolve().parents[1]
async def main():
 output=ROOT/'build/modem-send-dos';output.mkdir(parents=True,exist_ok=True);binary=ROOT/'build/modem-send/MODEMSND.EXE';digest=hashlib.sha256(binary.read_bytes()).hexdigest()
 for name in ('PASS.TXT','FAIL.TXT','BEFORE.BIN','AFTER.BIN'):(output/name).unlink(missing_ok=True)
 (output/'sampler.asm').write_text(SAMPLER);subprocess.run(['nasm','-fbin',str(output/'sampler.asm'),'-o',str(output/'SNAP.COM')],check=True)
 wire=bytearray();connected=asyncio.Event();finished=asyncio.Event()
 async def peer(reader,writer):
  connected.set()
  try:
   while data:=await reader.read(4096):wire.extend(data)
  finally:writer.close();await writer.wait_closed();finished.set()
 server=await asyncio.start_server(peer,'127.0.0.1',0);port=server.sockets[0].getsockname()[1]
 config=f'''[sdl]
output=surface
[cpu]
core=normal
cputype=386
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=nullmodem server:127.0.0.1 port:{port} transparent:1 rxdelay:200 txdelay:1
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
@echo off
mount c "{binary.parent}"
mount d "{output}"
c:
D:\\SNAP B
MODEMSND
if errorlevel 1 goto failed
echo PASS>D:\\PASS.TXT
goto done
:failed
echo FAIL>D:\\FAIL.TXT
:done
D:\\SNAP A
exit
''';(output/'dosbox.conf').write_text(config)
 with (output/'dosbox.log').open('w') as log:
  process=await asyncio.create_subprocess_exec('dosbox-x','-fastlaunch','-nogui','-conf',str(output/'dosbox.conf'),cwd=output,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log)
  try:code=await asyncio.wait_for(process.wait(),15)
  except asyncio.TimeoutError:process.terminate();await process.wait();code=-1
 server.close();await server.wait_closed()
 if connected.is_set():
  try:await asyncio.wait_for(finished.wait(),2)
  except asyncio.TimeoutError:pass
 before=(output/'BEFORE.BIN').read_bytes() if (output/'BEFORE.BIN').exists() else b'';after=(output/'AFTER.BIN').read_bytes() if (output/'AFTER.BIN').exists() else b''
 (output/'wire.bin').write_bytes(wire);checks={'normal_dos_exit':code==0 and (output/'PASS.TXT').exists() and not (output/'FAIL.TXT').exists(),'real_serial_connection':connected.is_set(),'exact_binary_wire':bytes(wire)==b'ATX\0\r^','hardware_restored':len(before)==42 and before==after,'binary_unchanged':hashlib.sha256(binary.read_bytes()).hexdigest()==digest}
 result={'passed':all(checks.values()),'checks':checks,'binary_sha256':digest,'wire_hex':wire.hex(),'scope':'Actual original sender+expansion+delay routines and recovered UART in DOSBox-X COM1/38400/8N1/no flow. Loopback captures six output bytes including NUL; sampler checks vectors/UART/PIC restoration. Diagnostic BIOS echo and synthetic calibrated-loop values, not physical modem timing.'};(output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(asyncio.run(main()))
