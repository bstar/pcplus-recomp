#!/usr/bin/env python3
"""Normal DOS8086 main, real BIOS keys and UART Chat/ordinary RX ownership."""
import argparse,json,re,shutil,struct,sys
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
from build_path_session import ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('terminal','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--pending-prefix',action='store_true',help='Hold an incomplete auto-download invitation before Alt-O; it must flush into the saved underlay')
    a=p.parse_args();binary,out=a.terminal.resolve(),a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    m=json.loads(binary.with_name('manifest.json').read_text());assert m['experimental_chat_frontend']
    assert sha(binary)==m['binary_sha256']
    names=['standalone/test_chat_main_dos.py','standalone/test_connection_dos.py',
           'standalone/directory_fixtures.py','standalone/modem_fixtures.py',
           'standalone/terminal_config_fixtures.py','standalone/test_terminal.py',
           'standalone/directory_test_support.py','standalone/build_path_session.py']
    sources={**m['sources'],**{n:sha(ROOT/n) for n in names}}
    assert all(sha(ROOT/n)==h for n,h in sources.items())
    out.mkdir();stage=out/'program';stage.mkdir()
    shutil.copyfile(binary,stage/'TERMINAL.EXE');shutil.copyfile(binary.parent/'PCCHAT.OVL',stage/'PCCHAT.OVL')
    name=out.name+'-main';assert re.fullmatch('[A-Za-z0-9_-]+',name)
    capture=ROOT/'build/connection-dos'/name;assert not capture.exists()
    settings=bytearray(prm(port=3,baud=5))
    for off,value in [(0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),
                      (0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0)]:
        struct.pack_into('<H',settings,off,value)
    harness.BINARY=stage/'TERMINAL.EXE'
    keys='p900 enter p5000 a-o p1500 C p120 H p120 A p120 T p120 P p120 I p120 N p120 G p120 enter p2500 escape p1000 N p120 O p120 R p120 M p120 A p120 L p1200 a-x'
    triggers=[(b'CHATPING\r',[(0,b'CHAT-REMOTE\xf0\x1b[6n')]),(b'NORMAL',[(0,b'BACK\x1b[6n')])]
    if a.pending_prefix:
        struct.pack_into('<H',settings,0x42c,1)
        keys=keys.replace('p5000 a-o','p5000 A R M p200 a-o',1)
        triggers.insert(0,(b'ARM',[(0,b'*')]))
    r=harness.run(name,'success',keys,prm=bytes(settings),com=3,irq=5,cpu='8086',
        working_drive='d',timeout=30,
        online_triggers=triggers)
    wire=(capture/'serial.bin').read_bytes();screen=(capture/'SCREEN.BIN').read_bytes()[::2]
    replies=re.findall(rb'\x1b\[\d+;\d+R',wire)
    checks=dict(harness=r['passed'],all_real_peer_triggers=r['checks']['online_triggers_sent'],
        exact_two_CPR=len(replies)==2,chat_buffer_submitted=b'CHATPING\r' in wire,
        ordinary_keys_resume=b'NORMAL' in wire,chat_underlay_restored=b'CHAT-REMOTE' not in screen,
        ordinary_RX_after_chat=b'BACK' in screen,
        unchanged_sources=all(sha(ROOT/n)==h for n,h in sources.items()),
        unchanged_module=sha(stage/'PCCHAT.OVL')==m['chat_loader']['module']['binary_sha256'])
    if a.pending_prefix:checks['held_invitation_restored_in_underlay']=b'FIRST BYTE SAFE*BACK' in screen
    report=dict(passed=all(checks.values()),checks=checks,binary_sha256=sha(binary),
                pending_prefix=a.pending_prefix,
                sources=sources,CPR_replies=[x.hex() for x in replies],
                capture=str(capture.relative_to(ROOT)),capture_files={str(q.relative_to(ROOT)):sha(q) for q in capture.rglob('*') if q.is_file()},
                scope=__doc__+' Actual Alt-O, buffered Chat line over UART triggers raw incoming text/CPR; Chat must not parse/reply to that CPR. Escape restores the underlay; normal typed keys trigger the next actual CPR reply. Ordinary startup supplies first CPR. Full main/normal exit/hardware/settings checks; synthetic modem, no passive TSR, no original executable. No Help/direct TEXT, notice/trap/carrier, BBS or physical acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    assert report['passed'],checks
    print('PASS normal DOS8086 Chat entry, BIOS typing, UART RX ownership and ordinary return')


if __name__=='__main__':main()
