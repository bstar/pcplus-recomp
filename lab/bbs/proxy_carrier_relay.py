"""Raw serial-side relay; DOSBox's built-in modem alone owns Hayes/DCD.

SynthModem upstream alone owns Telnet. No codec, Hayes reply or terminal reply
is generated here. Deliberate socket abort causes the modem's carrier loss.
"""
import asyncio
from contextlib import asynccontextmanager
import json
import time


class Session:
    def __init__(self,index,serial,peer):
        self.index=index;self.serial=serial;self.peer=peer
        self.display=bytearray();self.keyboard=bytearray();self.wire=bytearray();self.trace=[]
        self.start=time.monotonic();self.interrupted=False;self.interrupted_at=None;self.done=False;self.errors=[]
    def observe(self,direction,data):
        target=self.display if direction=='bbs' else self.keyboard
        self.trace.append(dict(direction=direction,offset=len(target),size=len(data),seconds=time.monotonic()-self.start))
        target.extend(data)
    def interrupt(self):
        assert not self.done and not self.interrupted
        self.interrupted=True;self.interrupted_at=time.monotonic()-self.start
        self.serial.transport.abort();self.peer.transport.abort()
    def save(self,out):
        out.mkdir(parents=True,exist_ok=False)
        for name,data in [('display.bin',self.display),('serial-received.bin',self.keyboard),('upstream.bin',self.wire)]:
            (out/name).write_bytes(data)
        (out/'trace.json').write_text(json.dumps(self.trace,indent=2)+'\n')
        (out/'session.json').write_text(json.dumps(dict(index=self.index,interrupted=self.interrupted,
            interrupted_at=self.interrupted_at,done=self.done,errors=self.errors,raw=True,
            scope=__doc__),indent=2)+'\n')


@asynccontextmanager
async def carrier_relay(remote_port):
    assert 1024<=remote_port<=65535
    sessions=[];owners=set()
    async def accept(reader,serial):
        owner=asyncio.current_task();owners.add(owner);peer=None;pumps=[];session=None
        try:
            upstream,peer=await asyncio.open_connection('127.0.0.1',remote_port)
            session=Session(len(sessions)+1,serial,peer);sessions.append(session)
            async def up():
                while data:=await reader.read(1024):
                    session.observe('dos',data);peer.write(data);await peer.drain()
            async def down():
                while data:=await upstream.read(1024):
                    session.wire.extend(data)
                    for at in range(0,len(data),32):
                        block=data[at:at+32];serial.write(block);await serial.drain()
                        session.observe('bbs',block)
                        await asyncio.sleep(len(block)*10/19200)
            pumps=[asyncio.create_task(up()),asyncio.create_task(down())]
            finished,_=await asyncio.wait(pumps,return_when=asyncio.FIRST_COMPLETED)
            for task in finished:
                error=task.exception()
                if error and not session.interrupted:session.errors.append(type(error).__name__)
        except (OSError,ConnectionError) as error:
            if session and not session.interrupted:session.errors.append(type(error).__name__)
        finally:
            for task in pumps:
                if not task.done():task.cancel()
            await asyncio.gather(*pumps,return_exceptions=True)
            serial.close()
            if peer:peer.close()
            if session:session.done=True
            owners.discard(owner)
    server=await asyncio.start_server(accept,'127.0.0.1',0)
    try:yield server.sockets[0].getsockname()[1],sessions
    finally:
        server.close()
        if hasattr(server,'close_clients'):server.close_clients()
        for owner in list(owners):owner.cancel()
        await asyncio.gather(*list(owners),return_exceptions=True)
        await asyncio.wait_for(server.wait_closed(),3)
