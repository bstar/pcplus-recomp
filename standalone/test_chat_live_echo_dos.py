#!/usr/bin/env python3
"""DOS8086 normal-main native Chat TEXT echo, pause/RX and queued BIOS keys."""
import argparse,json,re,shutil,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
from build_path_session import ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('terminal','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    m=json.loads(binary.with_name('manifest.json').read_text())
    assert m['experimental_chat_foreground_text'] and sha(binary)==m['binary_sha256']
    names=('standalone/test_chat_live_echo_dos.py','standalone/chat_live_watch.asm',
           'standalone/test_connection_dos.py','standalone/directory_fixtures.py',
           'standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py',
           'standalone/test_terminal.py','standalone/directory_test_support.py','standalone/build_path_session.py')
    sources={**m['sources'],**{n:sha(ROOT/n) for n in names}}
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    out.mkdir();stage=out/'program';stage.mkdir()
    shutil.copyfile(binary,stage/'TERMINAL.EXE');shutil.copyfile(binary.parent/'PCCHAT.OVL',stage/'PCCHAT.OVL')
    observer=out/'LIVEW.COM'
    subprocess.run(['nasm','-fbin',str(ROOT/'standalone/chat_live_watch.asm'),'-o',str(observer)],check=True)
    settings=bytearray(prm(port=3,baud=5))
    for off,value in [(0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),
                      (0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x1e4,0)]:
        struct.pack_into('<H',settings,off,value)
    settings[0x1e2]=ord('~')
    fields=[b'A^@B~C',b'WAIT~FIN^M',b'CANCEL~NEVER^M']+[b'']*7
    records=b''.join(struct.pack('<H',i%4)+field.ljust(52,b'\0') for i,field in enumerate(fields))
    # Alt-E enables native local echo before Chat. X/Enter are queued while
    # slot2 is paused; slot3 is explicitly cancelled during its pause.
    keys=('p900 enter p5000 a-e p500 a-o p2000 a-1 p1800 '
          'a-2 p100 X enter p1500 a-3 p400 escape p1200 N O R M A L p1400 a-x')
    harness.BINARY=stage/'TERMINAL.EXE';name=out.name+'-echo';capture=ROOT/'build/connection-dos'/name
    assert not capture.exists()
    r=harness.run(name,'success',keys,prm=bytes(settings),com=3,irq=5,cpu='8086',working_drive='d',timeout=45,
        arguments='@TEST.PRM /D:CaseTest:23 /T:D:\\ACTIONS.KEY',
        files={'ACTIONS.KEY':records,'LIVEW.COM':observer.read_bytes()},observer='LIVEW',
        online_triggers=[(b'A\0B',[(0,b'RXD')]),(b'NORMAL',[(0,b'BACK\x1b[6n')])])
    wire=(capture/'serial.bin').read_bytes();screen=(capture/'SCREEN.BIN').read_bytes()[::2]
    view=(capture/'LIVEVIEW.BIN').read_bytes();magic,flags,ticks,cursor=struct.unpack_from('<4H',view)
    pause=view[8:4008];echo=view[4008:8008]
    checks=dict(harness=r['passed'],all_triggers_sent=r['checks']['online_triggers_sent'],
        observer=magic==0x4c54 and ticks>0 and len(view)==8008,
        RX_during_pause=bool(flags&1) and pause[3200:3206:2]==b'AB ' and pause[2880:2886:2]==b'RXD',
        native_echo_without_wire_NUL=bool(flags&2) and echo[3200:3206:2]==b'ABC',
        local_pane_cursor_restored=cursor==0x1400,
        wire_and_queued_keys=b'A\0BCWAITFIN\rX\r' in wire,
        escape_cancels_TEXT=b'CANCEL' in wire and b'NEVER' not in wire,
        normal_input_resumes=b'NORMAL' in wire and b'BACK' in screen,
        no_Chat_CPR=len(re.findall(rb'\x1b\[\d+;\d+R',wire))==2,
        underlay_restored=b'RXD' not in screen,
        sources_unchanged=all(sha(ROOT/n)==h for n,h in sources.items()),
        module_unchanged=sha(stage/'PCCHAT.OVL')==m['chat_loader']['module']['binary_sha256'])
    report=dict(passed=all(checks.values()),checks=checks,binary_sha256=sha(binary),
        module_sha256=sha(stage/'PCCHAT.OVL'),sources=sources,capture=str(capture.relative_to(ROOT)),
        observer_flags=flags,observer_ticks=ticks,observer_sha256=sha(observer),
        scope=__doc__+' Actual BIOS keys and physical synthetic UART completion; passive INT1C observer only reads VGA/BDA. Checks both panes during configured pause, native echo skips wireNUL, module cursor restoration, ordinary keys retained through pause, Escape cancellation and normal terminal return. Observer consumes conventional memory; this is separate from unobserved ASPECT capacity checks. No native-parser-busy key injection, hardware flow-control stall, full original controller, BBS or physical acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    assert report['passed'],checks
    print('PASS normal DOS native TEXT echo/RX/pause, queued keys, Escape and return')


if __name__=='__main__':main()
