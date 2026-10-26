#!/usr/bin/env python3
"""Observe reference/refusal/browser/help in actual DOS8086 on COM3/IRQ5."""
import argparse,hashlib,json,struct,subprocess,zlib
from pathlib import Path
import test_connection_dos as driver
from modem_fixtures import fixture


def png(path,screen,font):
    # Actual captured VGA 8x16 glyphs, including the mode3 ninth line column.
    palette=[(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),
             (170,85,0),(170,170,170),(85,85,85),(85,85,255),(85,255,85),
             (85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]
    rows=[]
    for y in range(400):
        row=bytearray([0])
        for x in range(80):
            index=((y//16)*80+x)*2;ch,attr=screen[index:index+2]
            bits=font[ch*16+y%16]
            for bit in range(9):
                on=bool(bits&(128>>bit)) if bit<8 else 0xc0<=ch<=0xdf and bits&1
                row.extend(palette[attr&15 if on else (attr>>4)&7])
        rows.append(row)
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',720,400,8,2,0,0,0))+
                     chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b''))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--label',required=True)
    a=p.parse_args();root=driver.ROOT;binary=a.terminal.resolve();manifest=json.loads((binary.parent/'manifest.json').read_text())
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert manifest['experimental_original_reference'] and manifest.get('experimental_custom_irq') and manifest.get('special_edition')
    assert sha(binary)==manifest['binary_sha256'] and a.label and all(c.isalnum() or c in '-_' for c in a.label)
    for name,digest in manifest['sources'].items():assert sha(root/name)==digest,name
    out=root/'build/reference-dos'/a.label;out.mkdir(parents=True,exist_ok=False)
    case='reference-'+a.label;runout=root/'build/connection-dos'/case;assert not runout.exists()
    observer=out/'REFW.COM';subprocess.run(['nasm','-fbin',str(root/'standalone/reference_watch.asm'),'-o',str(observer)],check=True)
    raw=bytearray(fixture(timeout=5));struct.pack_into('<2H',raw,0,2,5)
    struct.pack_into('<H',raw,0x178,0x3e8);struct.pack_into('<H',raw,0x188,5);struct.pack_into('<HH',raw,0x4e4,8,4)
    driver.BINARY=binary
    keys='p900 enter p3500 a-z p700 a-d p800 escape p500 a-z p400 right down down f1 p500 escape p400 ` p600 escape p400 r e a d y p500 a-x'
    result=driver.run(case,'success',keys,prm=bytes(raw),com=3,irq=5,cpu='8086',
        working_drive='d',files={'REFW.COM':observer.read_bytes()},observer='REFW',
        online_updates=[(4.6,b'\x1b[5;1HWHILE REFERENCE\x1b[6n')])
    capture=(runout/'REFVIEW.BIN').read_bytes();font=(runout/'VGA16.BIN').read_bytes()
    assert len(capture)==12006 and len(font)==4096
    magic,flags,ticks=struct.unpack_from('<3H',capture);reference=capture[6:4006];refusal=capture[4006:8006];browser=capture[8006:12006]
    native=json.loads((root/'reconstruction/command_reference/provenance.json').read_text())
    wire=(runout/'serial.bin').read_bytes();final=(runout/'SCREEN.BIN').read_bytes()
    checks=dict(base_harness=result['passed'],independent_reference_capture=magic==0x5246 and flags&1!=0 and ticks>20,
        all_39_commands_visible=all(x['name'].encode() in reference[::2] for x in native['labels']),
        direct_AltD_refusal_observed=flags&2!=0 and b'Not available in this build:' in refusal[::2],
        source_help_observed=flags&8!=0,backtick_browser_observed=flags&4!=0 and b'Receive files' in browser[::2],
        no_hidden_redial=result['commands']==['ATZ','ATDCaseTest:23'],
        background_cursor_reply=b'\x1b[5;16R' in wire,post_reference_keyboard=b'ready' in wire,
        UI_keys_not_forwarded=b'\x1b[C' not in wire and b'\x1b[B' not in wire and b'`' not in wire,
        updated_live_video_restored=final[640:670:2]==b'WHILE REFERENCE',captured_ROM_font_nonempty=any(font))
    for name,frame in [('reference',reference),('refusal',refusal),('browser',browser)]:
        (out/(name+'.bin')).write_bytes(frame);png(out/(name+'.png'),frame,font)
    report=dict(passed=all(checks.values()),checks=checks,binary_sha256=sha(binary),serial=dict(com=3,irq=5,baud=19200),
        cpu='8086',observer_flags=flags,observer_ticks=ticks,keyboard=keys,
        inputs={str(p.relative_to(root)):sha(p) for p in [Path(__file__).resolve(),root/'standalone/reference_watch.asm',
          root/'standalone/test_connection_dos.py',root/'standalone/modem_fixtures.py',root/'reconstruction/command_reference/provenance.json']},
        artifacts={str(p.relative_to(root)):sha(p) for p in [runout/'REFVIEW.BIN',runout/'VGA16.BIN',runout/'serial.bin',runout/'BEFORE.BIN',runout/'AFTER.BIN',runout/'SCREEN.BIN']},
        scope=__doc__+' Passive timer reads video only; no UART/keyboard/product writes. Synthetic modem peer, no physical DCD/CTS/audio or original-runtime equivalence. PNG uses captured ROM glyphs and standard VGA palette.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
