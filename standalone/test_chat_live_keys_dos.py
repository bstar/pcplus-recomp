#!/usr/bin/env python3
"""Actual DOS8086 foreground Chat Alt1..Alt0 through module and physical UART."""
import argparse,json,re,shutil,struct
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
from build_path_session import ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('terminal','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    m=json.loads(binary.with_name('manifest.json').read_text());assert m['experimental_chat_foreground_text']
    assert sha(binary)==m['binary_sha256'] and m['chat_loader']['module']['api_version']==(0x105 if m.get('experimental_chat_redisplay') else 0x104)
    sources={**m['sources'],**{n:sha(ROOT/n) for n in ('standalone/test_chat_live_keys_dos.py','standalone/test_connection_dos.py','standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/test_terminal.py','standalone/directory_test_support.py','standalone/build_path_session.py')}}
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    out.mkdir();stage=out/'program';stage.mkdir()
    shutil.copyfile(binary,stage/'TERMINAL.EXE');shutil.copyfile(binary.parent/'PCCHAT.OVL',stage/'PCCHAT.OVL')
    settings=bytearray(prm(port=3,baud=5))
    for off,value in [(0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),
                      (0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x1e4,7)]:
        struct.pack_into('<H',settings,off,value)
    settings[0x1e2]=ord('~')
    fields=[b'ONE^@^^^~END^M',*[('S%02d^M'%n).encode() for n in range(2,10)],b'ZERO^^^M']
    records=b''.join(struct.pack('<H',i%4)+field.ljust(52,b'\0') for i,field in enumerate(fields))
    assert len(records)==540
    expected=b'ONE\0^END\r'+b''.join(('S%02d\r'%n).encode() for n in range(2,10))+b'ZERO^MLOC\r'
    keys='p900 enter p5000 a-o p3500 L p120 O p120 C p120 '+''.join('a-'+str(n)+' p600 ' for n in (1,2,3,4,5,6,7,8,9,0))+'enter p2000 escape p1000 N O R M A L p1400 a-x'
    harness.BINARY=stage/'TERMINAL.EXE';name=out.name+'-ten';capture=ROOT/'build/connection-dos'/name
    assert not capture.exists()
    r=harness.run(name,'success',keys,prm=bytes(settings),com=3,irq=5,cpu='8086',working_drive='d',timeout=45,
        arguments='@TEST.PRM /D:CaseTest:23 /T:D:\\ACTIONS.KEY',files={'ACTIONS.KEY':records},
        online_triggers=[(b'ONE\0^END\r',[(0,b'CHAT-RX\xf0\x1b[6n')]),(b'NORMAL',[(0,b'BACK\x1b[6n')])])
    wire=(capture/'serial.bin').read_bytes();screen=(capture/'SCREEN.BIN').read_bytes()[::2]
    replies=re.findall(rb'\x1b\[\d+;\d+R',wire)
    checks=dict(harness=r['passed'],all_triggers_sent=r['checks']['online_triggers_sent'],
        ten_direct_records_in_order=expected in wire,source_kind_ignored_as_native_TEXT=all(field.split(b'^')[0] in wire for field in fields),
        unfinished_local_line_preserved=b'ZERO^MLOC\r' in wire,normal_input_resumes=b'NORMAL' in wire,
        no_Chat_CPR=len(replies)==2,ordinary_RX_after_return=b'BACK' in screen,
        underlay_restored=b'CHAT-RX' not in screen,
        sources_unchanged=all(sha(ROOT/n)==h for n,h in sources.items()),
        module_unchanged=sha(stage/'PCCHAT.OVL')==m['chat_loader']['module']['binary_sha256'])
    report=dict(passed=all(checks.values()),checks=checks,binary_sha256=sha(binary),module_sha256=sha(stage/'PCCHAT.OVL'),
        expected_TEXT_hex=expected.hex(),sources=sources,capture=str(capture.relative_to(ROOT)),
        scope=__doc__+' Normal parent main, actual BIOS keys, all ten imported54-byte records across kinds0..3 as direct TEXT, copied grammar/wireNUL/triplecarets/configured pause/nonzero native pacing, preserved unfinished local line, incoming raw Chat text without CPR parsing, Escape underlay return and subsequent ordinary CPR. Synthetic modem; no product-state injection, echo-on visual/busy-key/flow-stall/physical/BBS acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    assert report['passed'],checks
    print('PASS all ten foreground direct TEXT keys, kinds0..3, binary/caret/pause/pacing, RX and local-line/normal return')


if __name__=='__main__':main()
