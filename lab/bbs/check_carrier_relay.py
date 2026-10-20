#!/usr/bin/env python3
"""Actual socket checks for binary Telnet bridging and interrupted-owner cleanup."""
import argparse,asyncio,hashlib,json,re,time
from pathlib import Path
from carrier_relay import carrier_relay
from modem import Telnet
ROOT=Path(__file__).resolve().parents[2]


async def run(args):
    assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    out=ROOT/'build/bbs-lab/carrier-relay'/args.label;out.mkdir(parents=True,exist_ok=False)
    received=[];ready=asyncio.Queue();owners=set()
    payload=bytes(range(256));request=b'\x1b[6n';answer=b'\x1b[4;5R'
    async def peer(reader,writer):
        owner=asyncio.current_task();owners.add(owner);index=len(received);received.append(bytearray())
        try:
            writer.write(b'\xff\xfd\x18'+Telnet.encode(payload)+request);await writer.drain()
            block=await asyncio.wait_for(reader.readexactly(3),3);assert block==b'\xff\xfb\x18'
            try:
                value=await asyncio.wait_for(reader.read(1),.05)
                raise AssertionError(('Bridge fabricated a terminal response',value))
            except asyncio.TimeoutError:await ready.put(index)
            value=await asyncio.wait_for(reader.readexactly(len(answer)),3);assert value==answer
            value=await asyncio.wait_for(reader.readexactly(257),3);assert value==Telnet.encode(payload)
            received[index].extend(value)
            # Incomplete Telnet state must not leak into the next connection.
            writer.write(b'\xff\xfa\x18');await writer.drain()
            await reader.read()
        finally:writer.close();owners.discard(owner)
    server=await asyncio.start_server(peer,'127.0.0.1',0);checks={};started=time.monotonic()
    try:
        async with carrier_relay(server.sockets[0].getsockname()[1]) as (port,sessions):
            for index in range(2):
                reader,writer=await asyncio.open_connection('127.0.0.1',port)
                shown=await asyncio.wait_for(reader.readexactly(len(payload)+len(request)),3)
                assert shown==payload+request and await asyncio.wait_for(ready.get(),3)==index
                writer.write(answer+payload);await writer.drain()
                while len(received[index])!=257:await asyncio.sleep(.001)
                if index==0:
                    sessions[0].interrupt();assert await asyncio.wait_for(reader.read(),3)==b''
                else:writer.close();await writer.wait_closed()
                deadline=time.monotonic()+3
                while not sessions[index].done and time.monotonic()<deadline:await asyncio.sleep(.001)
                assert sessions[index].done
            checks=dict(two_fresh_Telnet_sessions=len(sessions)==2 and all(not s.errors for s in sessions),
                every_binary_byte_both_directions=all(s.display==payload+request and s.keyboard==answer+payload for s in sessions),
                no_fabricated_terminal_reply=all(bytes(v)==Telnet.encode(payload) for v in received),
                interruption_is_scoped=sessions[0].interrupted and not sessions[1].interrupted,
                cleanup_completes=all(s.done for s in sessions))
        assert not owners
    finally:
        server.close()
        if hasattr(server,'close_clients'):server.close_clients()
        await asyncio.wait_for(server.wait_closed(),3)
    report=dict(passed=all(checks.values()),checks=checks,seconds=time.monotonic()-started,
        sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('lab/bbs/carrier_relay.py','lab/bbs/modem.py','lab/bbs/check_carrier_relay.py')},
        scope='Real loopback socket unit peers, all256 bytes, fresh negotiation and partial-Telnet isolation, terminal-response silence, scoped abort and task cleanup. No DOS or vendor BBS claim.')
    (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True)
    raise SystemExit(asyncio.run(run(p.parse_args())))
