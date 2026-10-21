#!/usr/bin/env python3
"""Check successive passive wire captures, all byte values and EOF cleanup."""
import argparse,asyncio,json
from pathlib import Path
from audio_reconnect_bbs_relay import relay
from audio_synchronet import ROOT,sha

async def run(out):
    payload=bytes(range(256));owners=set()
    async def echo(reader,writer):
        owner=asyncio.current_task();owners.add(owner)
        try:
            body=await reader.readexactly(256)
            for at in range(0,len(body),17):writer.write(body[at:at+17]);await writer.drain()
            await reader.read()
        finally:writer.close();await writer.wait_closed();owners.discard(owner)
    peer=await asyncio.start_server(echo,'127.0.0.1',0)
    checks={}
    try:
        async with relay(peer.sockets[0].getsockname()[1],out) as (port,sessions):
            for i in (1,2):
                reader,writer=await asyncio.open_connection('127.0.0.1',port)
                for byte in payload:writer.write(bytes([byte]));await writer.drain()
                checks[f'exact_echo_{i}']=await reader.readexactly(256)==payload
                writer.close();await writer.wait_closed()
                for _ in range(100):
                    if len(sessions)==i and sessions[-1]['done']:break
                    await asyncio.sleep(.01)
                checks[f'closed_{i}']=len(sessions)==i and sessions[-1]['done']
            checks['exact_raw_captures']=all(s['input']==s['output']==payload and not s['errors'] for s in sessions)
        for _ in range(100):
            if not owners:break
            await asyncio.sleep(.01)
        checks['peer_tasks_retired']=not owners
    finally:peer.close();await peer.wait_closed()
    result=dict(passed=all(checks.values()),checks=checks,
        inputs={n:sha(ROOT/n) for n in ('lab/bbs/check_audio_reconnect_relay.py','lab/bbs/audio_reconnect_bbs_relay.py')},
        captures_sha256={str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file()},
        scope='Two loopback byte-echo connections through the passive capture relay. All 256 bytes each direction, exact saved raw streams, EOF and task retirement. No BBS replies, DSP, SIP or DOS compatibility claim.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    out=p.parse_args().output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    asyncio.run(run(out))
