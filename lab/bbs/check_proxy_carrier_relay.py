#!/usr/bin/env python3
"""Actual raw sockets preserve all bytes and scope abort to one connection."""
import argparse
import asyncio
import json
from pathlib import Path
from proxy_carrier_relay import carrier_relay
from product_inputs import ROOT,sha


async def run(a):
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
    payload=bytes(range(256))+b'\xff\xfd\x18\xff\xfa\x1f\x00P\x00\x18\xff\xf0\x1b[18t'
    received=[];owners=set();ready=asyncio.Queue();accepted=0
    tail=bytes(range(256))*16
    async def peer(reader,writer):
        nonlocal accepted
        accepted+=1;index=accepted
        task=asyncio.current_task();owners.add(task)
        try:
            writer.write(payload);await writer.drain();await ready.put(True)
            value=await reader.readexactly(len(payload));received.append(value)
            if index==3:
                writer.write(tail);await writer.drain()
            else:await reader.read()
        finally:writer.close();owners.discard(task)
    server=await asyncio.start_server(peer,'127.0.0.1',0)
    try:
        async with carrier_relay(server.sockets[0].getsockname()[1]) as (port,sessions):
            for index in range(3):
                reader,writer=await asyncio.open_connection('127.0.0.1',port)
                await asyncio.wait_for(ready.get(),3)
                assert await asyncio.wait_for(reader.readexactly(len(payload)),3)==payload
                # Deliberately send neither Telnet nor CSI responses: relay
                # must not manufacture them while upstream is silent.
                try:
                    value=await asyncio.wait_for(reader.read(1),.05)
                    raise AssertionError(('Unexpected relay bytes',value))
                except asyncio.TimeoutError:pass
                writer.write(payload);await writer.drain()
                deadline=asyncio.get_running_loop().time()+3
                while len(received)<=index and asyncio.get_running_loop().time()<deadline:await asyncio.sleep(.001)
                assert received[index]==payload
                if index==0:
                    sessions[0].interrupt();assert await asyncio.wait_for(reader.read(),3)==b''
                elif index==1:writer.close();await writer.wait_closed()
                else:
                    assert await asyncio.wait_for(reader.readexactly(len(tail)),5)==tail
                    assert await asyncio.wait_for(reader.read(),3)==b''
                    writer.close();await writer.wait_closed()
                deadline=asyncio.get_running_loop().time()+3
                while not sessions[index].done and asyncio.get_running_loop().time()<deadline:await asyncio.sleep(.001)
                assert sessions[index].done and not sessions[index].errors
            assert len(sessions)==3 and sessions[0].interrupted and all(not s.interrupted for s in sessions[1:])
            assert all(s.display==s.wire==s.keyboard==payload for s in sessions[:2])
            assert sessions[2].keyboard==payload and sessions[2].display==sessions[2].wire==payload+tail
            for s in sessions:s.save(out/('connection-'+str(s.index)))
        assert not owners
    finally:
        server.close()
        if hasattr(server,'close_clients'):server.close_clients()
        await asyncio.wait_for(server.wait_closed(),3)
    result=dict(passed=True,connections=3,every_byte_both_directions=True,no_codec_or_fabricated_reply=True,
        orderly_remote_EOF_drained_bytes=len(tail),
        scoped_abort=True,cleaned_owners=True,sources={n:sha(ROOT/n) for n in ['lab/bbs/proxy_carrier_relay.py','lab/bbs/check_proxy_carrier_relay.py']},
        scope=__doc__+' Loopback socket evidence only; no DOS/modem or physical DCD acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS raw carrier relay:3 sessions,all bytes,no generated replies,scoped abort,orderly EOF')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    raise SystemExit(asyncio.run(run(p.parse_args())))
