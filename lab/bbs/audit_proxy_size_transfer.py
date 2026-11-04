#!/usr/bin/env python3
"""Independently bind size-probed real-BBS ZMODEM bytes, geometry and storage.

Synthetic Hayes/staged proxy/owned stock helper; no SIP/DSP/physical acceptance.
"""
import argparse
import json
import struct
import subprocess
from pathlib import Path

from product_inputs import ROOT, sha
from audit_size_probe_screen import telnet
from audit_zmodem import audit_batch, audit_controls
from test_transfer_dos import timestamp, offset_after


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--label', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    wrapper = ROOT/'build/bbs-lab'/(a.label+'-transfer')
    capture = ROOT/'build/bbs-lab/results/enigma'/a.label
    bridge = ROOT/'build/bbs-lab'/(a.label+'-proxy')
    out = a.output.resolve()
    assert out.is_relative_to(ROOT/'build')
    out.mkdir(parents=True,exist_ok=False)
    report = json.loads((wrapper/'result.json').read_text())
    base = json.loads((capture/'result.json').read_text())
    assert report['passed'] and base['passed'] and base['standard_completion'] and not base['errors']
    assert all(report['checks'].values()) and all(base['checks'].values())
    for group in ('product_inputs','server_inputs'):
        for name,digest in report[group].items():
            assert sha(ROOT/name)==digest,name
    raw = (capture/'TEST.PRM').read_bytes()
    hidden,selector,physical,mode = [struct.unpack_from('<H',raw,at)[0] for at in (0x1c2,0x1c8,0x1ca,0x4ec)]
    assert hidden in (0,1) and physical in (25,28,43,50) and (selector,mode)==(2,0)
    logical = physical-(not hidden)
    assert report['display_layout']==base['display_layout']==dict(physical_rows=physical,logical_rows=logical,status_hidden=hidden)
    geometry = struct.unpack('<4H',(capture/'GEOM.BIN').read_bytes())
    assert (geometry[0],geometry[1],geometry[2],geometry[3]>>8)==(physical,14 if physical==28 else 8 if physical in (43,50) else 16,0x5003,0)
    utility = out/'GEOM.COM'
    subprocess.run(['nasm','-fbin',str(ROOT/'standalone/display_startup_geometry.asm'),'-o',str(utility)],check=True)
    assert sha(utility)==sha(capture/'GEOM.COM')
    serial_in = (bridge/'1-serial-input.bin').read_bytes()
    serial_out = (bridge/'1-serial-output.bin').read_bytes()
    client,subs,options = telnet((bridge/'1-telnet-input.bin').read_bytes())
    server,server_subs,server_options = telnet((bridge/'1-telnet-output.bin').read_bytes())
    sizes = [struct.unpack('>HH',sub[1:]) for sub in subs if sub[0]==31 and len(sub)==5]
    assert sizes==[(80,logical)]
    # Remove only the actual menu-owner prefix, never scan binary payload for
    # size-looking sequences: such sequences deliberately occur in the file.
    owned_prefix = b'loc\r\x1b'+f'[8;{logical};80t'.encode()
    assert serial_in.startswith(owned_prefix)
    assert client==serial_in[len(owned_prefix):]
    assert serial_out.endswith(server)
    assert serial_in==(capture/'bbs-sent.bin').read_bytes()
    assert serial_out==(capture/'display.bin').read_bytes()
    fixture = report['fixture']
    name = fixture['name']
    source = wrapper/name if report['mode']=='upload' else ROOT/'build/bbs-lab/enigma/source/file_base/pcplus_transfer'/name
    payload = source.read_bytes()
    assert len(payload)==fixture['bytes'] and sha(source)==fixture['sha256']
    protocol = json.loads((capture/'protocol.json').read_text())
    trace = json.loads((capture/'trace.json').read_text())
    direction = 'dos' if report['mode']=='upload' else 'bbs'
    stream = (capture/'serial-received.bin').read_bytes() if direction=='dos' else serial_out
    checked = audit_batch(stream,{name:payload},protocol['start'])
    assert (checked['start'],checked['end'])==(protocol['start'],protocol['end'])
    # The existing producer already binds post-menu time and opposite controls;
    # re-run those controls at its recorded post-menu bound independently.
    command=json.loads((wrapper/'command.json').read_text())
    post_input=bytes.fromhex(command[command.index('--post-input-hex')+1])
    end_time=timestamp(trace,direction,checked['end']-1)
    keyboard=(capture/'serial-received.bin').read_bytes()
    cut=offset_after(trace,'dos',end_time) or len(keyboard)
    post_at=keyboard.find(post_input,cut)
    assert post_at>=0
    post_time=timestamp(trace,'dos',post_at)
    opposite=keyboard if direction=='bbs' else serial_out
    controls=audit_controls(checked,opposite,trace,direction,post_time,False)
    assert controls==protocol['controls'] and checked['finish']
    if report['mode']=='download':
        destination = capture/'RECV'/name
    else:
        official = json.loads((capture/'server-audit.stdout').read_text())
        assert official['passed'] and len(official['entries'])==1
        entry = official['entries'][0]
        destination = Path(entry['filePath']).resolve()
        assert destination.is_relative_to(ROOT/'build/bbs-lab/enigma/source/file_base/pcplus_transfer')
        assert entry['fileName']==name and entry['areaTag']=='pcplus_transfer'
        assert entry['fileSha256']==sha(source) and int(entry['meta']['byte_size'])==len(payload)
    assert destination.read_bytes()==payload
    assert len((capture/'SCREEN.BIN').read_bytes())==8000
    before = (capture/'BEFORE.BIN').read_bytes()
    assert len(before)==42 and before==(capture/'AFTER.BIN').read_bytes()
    assert not list(capture.rglob('PCRX.$$$'))
    files = [wrapper/'result.json',wrapper/'command.json',capture/'serial-received.bin',
             capture/'server-session-audit.json',capture/'server-session.jsonl',capture/'modem.json',
             bridge/'ready.json',bridge/'1-closed.json',capture/'result.json',capture/'protocol.json',capture/'trace.json',
             capture/'TEST.PRM',capture/'GEOM.BIN',capture/'GEOM.COM',capture/'SCREEN.BIN',
             capture/'BEFORE.BIN',capture/'AFTER.BIN',capture/'bbs-sent.bin',capture/'display.bin',
             bridge/'1-serial-input.bin',bridge/'1-serial-output.bin',bridge/'1-telnet-input.bin',
             bridge/'1-telnet-output.bin',source,destination]
    if report['mode']=='upload':files += [capture/'server-audit.stdout',capture/'server-audit.stderr']
    result = dict(passed=True,label=a.label,mode=report['mode'],terminal_sha256=report['terminal_sha256'],
        physical_rows=physical,logical_rows=logical,status_hidden=hidden,NAWS=sizes,
        payload_bytes=len(payload),payload_sha256=sha(source),all256_values=set(payload)==set(range(256)),
        payload_size_lookalikes=payload.count(b'\x1b[8;50;80t'),
        client_application_bytes=len(client),server_application_bytes=len(server),
        exact_proxy_streams=True,only_owned_menu_prefix_consumed=True,exact_destination=True,
        captures={str(path.relative_to(ROOT)):sha(path) for path in files},
        sources={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__))},scope=__doc__+
        ' Raw Telnet decoder preserves exact application bytes after one owned prefix, including binary size lookalikes. Re-runs independent sender CRC/length/ZEOF/ZFIN/OO audit; Re-runs opposite controls at the observed actual post-menu input bound; producer also validates real menu output. Actual BIOS and destination/official FileEntry identity bound. No cancellation/carrier/reconnect acceptance.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS size-proxy',report['mode'],len(payload),'bytes;',physical,'physical rows')


if __name__=='__main__':
    main()
