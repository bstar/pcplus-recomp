"""Test-only DOSBox modem bridge; each call owns a real SIP/audio frontend.

DOSBox supplies Hayes/DCD. The existing DSP frontend supplies audio transport.
Only its local AT response prefix is consumed here; online bytes are unmodified.
Stopping the owned frontend tears down SIP/audio before its EOF drops emulated
DCD. This tests bridge-process failure, not analog waveform-loss detection.
"""
import asyncio,json,signal,time
from contextlib import asynccontextmanager
from pathlib import Path

PREFIX=b'\r\nOK\r\n\r\nCONNECT 1200\r\n'

async def train(reader,writer):
    writer.write(b'ATZ\r');await writer.drain()
    assert await asyncio.wait_for(reader.readexactly(6),10)==b'\r\nOK\r\n'
    writer.write(b'ATD1\r');await writer.drain()
    assert await asyncio.wait_for(reader.readexactly(16),45)==b'\r\nCONNECT 1200\r\n'

class Call:
    def __init__(self,index,out):
        self.index=index;self.out=out;self.process=None;self.done=False
        self.interrupted=False;self.errors=[];self.events=[]
        self.up=bytearray();self.down=bytearray();self.front=None
    def event(self,name,**fields):
        self.events.append(dict(event=name,monotonic_ns=str(time.monotonic_ns()),**fields))
    def interrupt(self):
        assert self.process and self.process.returncode is None and not self.interrupted
        self.interrupted=True;self.event('owned-frontend-SIGTERM')
        self.process.send_signal(signal.SIGTERM)
    def save(self):
        (self.out/'adapter-up.bin').write_bytes(self.up)
        (self.out/'adapter-down.bin').write_bytes(self.down)
        (self.out/'adapter.json').write_text(json.dumps(dict(index=self.index,done=self.done,
            interrupted=self.interrupted,errors=self.errors,events=self.events,
            frontend_exit=self.process.returncode if self.process else None),indent=2)+'\n')

@asynccontextmanager
async def audio_carrier_adapter(root,runtime,out):
    root=Path(root);calls=[];owners=set()
    async def accept(reader,serial):
        owner=asyncio.current_task();owners.add(owner)
        folder=out/f'call-{len(calls)+1}';folder.mkdir()
        call=Call(len(calls)+1,folder);calls.append(call);tasks=[]
        try:
            call.event('DOSBox-TCP-connected')
            with (folder/'node.log').open('wb') as log:
                call.process=await asyncio.create_subprocess_exec('node',str(root/'lab/bbs/synthmodem_audio_serial.js'),
                    str(runtime),str(folder),'--carrier','--key-framing',stdout=log,stderr=log)
                deadline=time.monotonic()+60
                while not (folder/'serial-port.json').exists():
                    assert call.process.returncode is None and time.monotonic()<deadline,'Frontend readiness'
                    await asyncio.sleep(.05)
                port=json.loads((folder/'serial-port.json').read_text())['port']
                upstream,call.front=await asyncio.open_connection('127.0.0.1',port)
                await train(upstream,call.front);call.event('both-DSP-CONNECT')
                async def up():
                    while data:=await reader.read(4096):
                        call.front.write(data);await call.front.drain();call.up.extend(data)
                    call.event('DOSBox-TCP-EOF')
                async def down():
                    while data:=await upstream.read(4096):
                        serial.write(data);await serial.drain();call.down.extend(data)
                    call.event('frontend-EOF')
                tasks=[asyncio.create_task(up()),asyncio.create_task(down())]
                done,_=await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
                for task in done:task.result()
        except Exception as error:
            call.errors.append(repr(error));call.event('adapter-error',error=repr(error))
        finally:
            for task in tasks:
                if not task.done():task.cancel()
            await asyncio.gather(*tasks,return_exceptions=True)
            # On interrupted calls EOF must originate from actual frontend
            # shutdown. Never close this socket directly to simulate a loss.
            serial.close();await serial.wait_closed();call.event('DOSBox-TCP-closed')
            if call.front:call.front.close();await call.front.wait_closed()
            if call.process and call.process.returncode is None:
                try:await asyncio.wait_for(call.process.wait(),15)
                except asyncio.TimeoutError:
                    call.errors.append('Frontend did not exit after serial close')
                    call.process.send_signal(signal.SIGTERM)
                    try:await asyncio.wait_for(call.process.wait(),15)
                    except asyncio.TimeoutError:call.process.kill();await call.process.wait()
            call.done=True;call.save();owners.discard(owner)
    server=await asyncio.start_server(accept,'127.0.0.1',0)
    try:yield server.sockets[0].getsockname()[1],calls
    finally:
        server.close()
        for owner in list(owners):owner.cancel()
        await asyncio.gather(*list(owners),return_exceptions=True)
        await server.wait_closed()
