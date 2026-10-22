#!/usr/bin/env python3
"""Independently decode nullmodem control framing and audit actual DOS CTS stalls."""
import argparse,json,shutil,struct
from pathlib import Path
from audit_aspect_abort_carrier import ROOT,sha,read
ESC=b'\x1b'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('run','emulator-source','cohort','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();run=a.run.resolve();source=a.emulator_source.resolve();cohort=a.cohort.resolve();output=a.output.resolve()
    assert all(x.is_relative_to(ROOT/'build') for x in (run,source,cohort)) and not cohort.exists()
    assert output.is_relative_to(ROOT/'docs/validation') and not output.exists()
    r=read(run/'checks.json');assert r['passed'] and {x['case'] for x in r['cases']}=={'hard','both'}
    for name,digest in r['inputs'].items():assert sha(ROOT/name)==sha(run/'inputs'/name)==digest,name
    provenance=read(source/'sources.json')
    for name,row in provenance.items():assert sha(source/name)==row['sha256']
    # Match the pinned Nix derivation, not a moving upstream branch.
    assert provenance['nullmodem.cpp']['url']=='https://raw.githubusercontent.com/joncampbell123/dosbox-x/dosbox-x-v2026.07.02/src/hardware/serialport/nullmodem.cpp'
    assert provenance['package.nix']['url']=='https://raw.githubusercontent.com/NixOS/nixpkgs/f13ff45afd1bb73e640eaa08a7066dbed07e3238/pkgs/by-name/do/dosbox-x/package.nix'
    assert 'version = "2026.07.02"' in (source/'package.nix').read_text()
    executable=Path(shutil.which('dosbox-x')).resolve();assert '-dosbox-x-2026.07.02/' in str(executable)
    wrapped=executable.with_name('.dosbox-x-wrapped');assert wrapped.is_file()
    results={}
    for row in r['cases']:
        assert row['passed'] and all(row['checks'].values());case=run/row['case'];soft=row['case']=='both'
        for name,digest in row['captures'].items():assert sha(case/name)==digest,name
        assert sha(case/'TERMINAL.EXE')==r['parent_sha256'] and sha(case/'ASPECT.EXE')==r['runner_sha256']
        cfg=(case/'dosbox.conf').read_text();assert 'transparent:0 rxdelay:200 txdelay:1' in cfg and 'cputype=8086' in cfg
        assert struct.unpack_from('<2H',(case/'TEST.PRM').read_bytes(),0x198)==(int(soft),1)
        before=(case/'BEFORE.BIN').read_bytes();assert len(before)==42 and before==(case/'AFTER.BIN').read_bytes()
        raw=(case/'RENDER.BIN').read_bytes();head=struct.unpack_from('<7H',raw)
        assert head[:4]==(0x524e,1,1,1) and head[6]==0
        assert raw[14:34]==raw[34:54] and raw[54:470]==raw[470:886]
        paused,returned,parent_paused,hardware=struct.unpack('<4H',raw[-8:])
        assert paused==parent_paused==0 and returned>18 and hardware>12
        assert (case/'CTS.OK').read_bytes()==b'RESUMED'
        events=read(case/'peer-events.json');assert all(x['time']<=y['time'] for x,y in zip(events,events[1:]))
        ready=[e for e in events if e['kind']=='cts-ready'];low=[e for e in events if e['kind']=='cts-low-go'];high=[e for e in events if e['kind']=='cts-high']
        assert len(ready)==len(low)==len(high)==1
        assert bytes.fromhex(ready[0]['hex'])==bytes.fromhex(high[0]['hex'])==b'\xff\x03'
        assert bytes.fromhex(low[0]['hex'])==b'\xff\x02GO'
        assert ready[0]['time']<low[0]['time'] and 1.2<=high[0]['time']-low[0]['time']<1.8
        decoded=bytearray();status=[];escape=False;transport=bytearray()
        for e in events:
            if e['kind']=='transport-receive':
                block=bytes.fromhex(e['hex']);transport.extend(block)
                for byte in block:
                    if escape:
                        escape=False
                        if byte==255:decoded.append(byte)
                        else:assert byte<=3;status.append(byte)
                    elif byte==255:escape=True
                    else:decoded.append(byte)
            if e['kind']=='receive' and low[0]['time']<e['time']<high[0]['time']:
                assert bytes.fromhex(e['hex'])==b''
        assert not escape and status and status==[int(e['hex'],16) for e in events if e['kind']=='modem-status']
        wire=(case/'serial.bin').read_bytes();assert bytes(decoded)==wire
        assert wire==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive')
        control=b'\x13\x11' if soft else b''
        expected=b'ATZ\rATDCaseTest:23\r'+control+ESC+b'[1;16R'+ESC+b'[?62;2cKEYREADY'+b'0123456789ABCDEF'*128+control+b'ready'+ESC+b'[1;24R+++ATH\r'
        assert wire==expected and (case/'PASS.TXT').is_file() and not (case/'FAIL.TXT').exists()
        results[row['case']]=dict(passed=True,payload_bytes=2048,wire_bytes=len(wire),transport_bytes=len(transport),modem_status_frames=len(status),
                                 CTS_low_seconds=high[0]['time']-low[0]['time'],software_paused_ticks=0,hardware_owner_ticks=hardware,wire_sha256=sha(case/'serial.bin'))
    cohort.mkdir()
    for item in (run,source,Path(__file__)):
        target=cohort/item.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
        if item.is_dir():shutil.copytree(item,target)
        else:shutil.copy2(item,target)
    files={str(f.relative_to(cohort)):sha(f) for f in cohort.rglob('*') if f.is_file()}
    (cohort/'files.json').write_text(json.dumps(files,indent=2)+'\n')
    result=dict(passed=True,actual_emulated_CTS_accepted=True,physical_hardware_accepted=False,full_application_accepted=False,
                parent_sha256=r['parent_sha256'],runner_sha256=r['runner_sha256'],cases=results,
                emulator=dict(version='2026.07.02',wrapper=str(executable),wrapper_sha256=sha(executable),binary_sha256=sha(wrapped),sources=provenance),
                cohort=str(cohort.relative_to(ROOT)),frozen_files=len(files),files_manifest_sha256=sha(cohort/'files.json'),auditor_sha256=sha(Path(__file__)),
                scope='Two actual8086 DOS HARD/BOTH sessions. Owned peer drives CTS low/high through the pinned emulator nontransparent nullmodem FF/status framing. Independent decoding separates transport status from actual UART bytes; no data crosses while CTS is low, no XOFF is sent and child software-pause stays zero. Exact2048-byte payload, manual parent/query return, native child exit and hardware/JFT/file-owner restoration pass.',
                remaining=['Longer CTS stalls, timeout/cancel handback, RTS receive throttling, sustained RX pressure, carrier reconnect and physical ISA UART/modem timing remain open.'])
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,cases=results)))


if __name__=='__main__':main()
