"""Passive loopback wire capture for successive real audio/BBS connections."""
import asyncio,json,time
from contextlib import asynccontextmanager

@asynccontextmanager
async def relay(port,out):
    sessions=[];owners=set()
    async def accept(reader,client):
        owner=asyncio.current_task();owners.add(owner);peer=None;tasks=[]
        row=dict(input=bytearray(),output=bytearray(),trace=[],errors=[],done=False)
        sessions.append(row)
        try:
            upstream,peer=await asyncio.open_connection('127.0.0.1',port)
            async def pump(source,target,key,direction):
                while data:=await source.read(4096):
                    ns=time.monotonic_ns();row['trace'].append(dict(direction=direction,
                        offset=len(row[key]),count=len(data),monotonic_ns=str(ns)))
                    row[key].extend(data);target.write(data);await target.drain()
            tasks=[asyncio.create_task(pump(reader,peer,'input','to_bbs')),
                   asyncio.create_task(pump(upstream,client,'output','from_bbs'))]
            done,_=await asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED)
            for task in done:task.result()
        except Exception as error:row['errors'].append(repr(error))
        finally:
            for task in tasks:
                if not task.done():task.cancel()
            await asyncio.gather(*tasks,return_exceptions=True)
            client.close()
            if peer:peer.close()
            row['done']=True;owners.discard(owner)
    server=await asyncio.start_server(accept,'127.0.0.1',0)
    try:yield server.sockets[0].getsockname()[1],sessions
    finally:
        server.close()
        for owner in list(owners):owner.cancel()
        await asyncio.gather(*list(owners),return_exceptions=True)
        await server.wait_closed()
        for i,row in enumerate(sessions,1):
            folder=out/f'bbs-{i}';folder.mkdir()
            (folder/'input.bin').write_bytes(row['input']);(folder/'output.bin').write_bytes(row['output'])
            (folder/'relay.json').write_text(json.dumps({k:v for k,v in row.items() if k not in ('input','output')},indent=2)+'\n')
