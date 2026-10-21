#!/usr/bin/env python3
"""Check command-prefix isolation without replacing an audio acceptance run."""
import argparse,asyncio,json
from pathlib import Path
from audio_carrier_adapter import train
from audio_synchronet import ROOT,sha

async def run(out):
    cases=[]
    for mode in ('fragmented-prefix','invalid-reset-result','short-connect-result'):
        observed=[];done=asyncio.Event();errors=[]
        async def accept(reader,writer):
            try:
                observed.append((await reader.readuntil(b'\r')).decode())
                for c in (b'\r\nNO\r\n' if mode=='invalid-reset-result' else b'\r\nOK\r\n'):
                    writer.write(bytes([c]));await writer.drain();await asyncio.sleep(.001)
                if mode!='invalid-reset-result':
                    observed.append((await reader.readuntil(b'\r')).decode())
                    writer.write(b'\r\nCON' if mode=='short-connect-result' else b'\r\nCONNECT 1200\r\n'+bytes(range(256)))
                    await writer.drain()
            except Exception as error:errors.append(repr(error))
            finally:writer.close();await writer.wait_closed();done.set()
        server=await asyncio.start_server(accept,'127.0.0.1',0)
        reader,writer=await asyncio.open_connection('127.0.0.1',server.sockets[0].getsockname()[1])
        rejected=False;online=None
        try:await train(reader,writer)
        except (AssertionError,asyncio.IncompleteReadError):rejected=True
        if not rejected:online=await reader.readexactly(256)
        writer.close();await writer.wait_closed();await asyncio.wait_for(done.wait(),3)
        server.close();await server.wait_closed()
        checks=dict(result_correct=rejected==(mode!='fragmented-prefix'),
            exact_commands=observed==(['ATZ\r'] if mode=='invalid-reset-result' else ['ATZ\r','ATD1\r']),
            all_online_bytes_preserved=online==bytes(range(256)) if not rejected else online is None,
            no_peer_errors=not errors)
        cases.append(dict(mode=mode,passed=all(checks.values()),checks=checks))
    result=dict(passed=all(c['passed'] for c in cases),cases=cases,
        inputs={n:sha(ROOT/n) for n in ('lab/bbs/check_audio_carrier_adapter.py','lab/bbs/audio_carrier_adapter.py')},
        scope='Loopback fixture unit check only: strict fragmented synthetic AT response consumption, rejection of invalid/short results and preservation of all 256 online byte values. No DSP, DOS, SIP or physical acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['passed']

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    out=p.parse_args().output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    asyncio.run(run(out))
