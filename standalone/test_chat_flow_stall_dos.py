#!/usr/bin/env python3
"""Actual DOS8086 Chat TEXT XOFF stall, concurrent RX and XON recovery."""
import argparse,json,re,shutil,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
from build_path_session import ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('terminal','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--cancel-queued',action='store_true',help='Cancel stalled TEXT with X ahead of Escape')
    a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    m=json.loads(binary.with_name('manifest.json').read_text());assert m['experimental_chat_foreground_text'] and sha(binary)==m['binary_sha256']
    names=('standalone/test_chat_flow_stall_dos.py','standalone/chat_flow_watch.asm','standalone/test_connection_dos.py',
           'standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py',
           'standalone/test_terminal.py','standalone/directory_test_support.py','standalone/build_path_session.py')
    sources={**m['sources'],**{n:sha(ROOT/n) for n in names}}
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    listing=binary.with_name('terminal.map').read_text()
    symbols={n:(int(seg,16),int(off,16)) for seg,off,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
    ds=int(re.search(r'^DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I)[1],16)
    constants={'FROZEN_DELTA':symbols['redisplay_snapshot'][0]-ds}
    for label,name in [('OWNER_OFF','_redisplay_active'),('PAUSED_OFF','uart_tx_paused'),('DEFERRED_OFF','terminal_deferred_count')]:
        seg,off=symbols[name];assert seg==ds;constants[label]=off
    out.mkdir();stage=out/'program';stage.mkdir()
    shutil.copyfile(binary,stage/'TERMINAL.EXE');shutil.copyfile(binary.parent/'PCCHAT.OVL',stage/'PCCHAT.OVL')
    observer=out/'FLOWW.COM'
    subprocess.run(['nasm','-fbin',*(['-DCHAT_FLOW_CANCEL'] if a.cancel_queued else []),*['-D'+k+'='+str(v) for k,v in constants.items()],str(ROOT/'standalone/chat_flow_watch.asm'),'-o',str(observer)],check=True)
    settings=bytearray(prm(port=3,baud=5,soft=1,hard=0))
    for off,value in [(0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),
                      (0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x1e4,0)]:struct.pack_into('<H',settings,off,value)
    settings[0x1e2]=ord('~')
    records=struct.pack('<H',2)+b'GO~TAIL^M'.ljust(52,b'\0')+bytes(54*9)
    keys='p900 enter p5000 a-o p1800 a-1 p2200 escape p800 N O R M A L p1000 a-x'
    if a.cancel_queued:keys='p900 enter p5000 a-o p1800 a-1 p750 X p100 escape p1600 N O R M A L p1000 a-x'
    harness.BINARY=stage/'TERMINAL.EXE';name=out.name+'-flow';capture=ROOT/'build/connection-dos'/name;assert not capture.exists()
    r=harness.run(name,'success',keys,prm=bytes(settings),com=3,irq=5,cpu='8086',working_drive='d',timeout=40,
        arguments='@TEST.PRM /D:CaseTest:23 /T:D:\\ACTIONS.KEY',files={'ACTIONS.KEY':records,'FLOWW.COM':observer.read_bytes()},observer='FLOWW',
        online_triggers=[(b'GO',[(0,b'\x13'),(.15,b'RXD'),(1.2,b'\x11')]),(b'NORMAL',[(0,b'BACK\x1b[6n')])])
    wire=(capture/'serial.bin').read_bytes();screen=(capture/'SCREEN.BIN').read_bytes()[::2]
    words=struct.unpack('<8H',(capture/'FLOWVIEW.BIN').read_bytes());flags=words[1]
    checks=dict(harness=r['passed'],observer=words[0]==0x4657,
        real_XOFF_and_pending_T=bool(flags&1) and words[2]>0,
        RX_visible_while_TX_stalled=bool(flags&2) and words[3]>0,
        TEXT_completion_or_retirement=bool(flags&4) and words[4]>0,
        exact_wire_order=(b'GONORMAL' if a.cancel_queued else b'GOTAIL\rNORMAL') in wire,
        ordinary_return=b'BACK' in screen and b'RXD' not in screen,
        sources_unchanged=all(sha(ROOT/n)==h for n,h in sources.items()),
        module_unchanged=sha(stage/'PCCHAT.OVL')==m['chat_loader']['module']['binary_sha256'])
    if a.cancel_queued:
        checks.update(queued_X_retained=words[5]>=1,retired_FIFO_empty=words[6]==0,
                      abandoned_TEXT_and_typeahead_discarded=b'TAIL' not in wire and b'GOX' not in wire)
    report=dict(passed=all(checks.values()),checks=checks,observer_words=words,observer_constants=constants,
        binary_sha256=sha(binary),module_sha256=sha(stage/'PCCHAT.OVL'),sources=sources,capture=str(capture.relative_to(ROOT)),cancel_queued=a.cancel_queued,
        scope=__doc__+' Ordinary main and actual synthetic UART XOFF/XON. Passive INT16 observer confirms parent DS=SS/exact API, owner2/TEXT active, physical UART pause, pending T transmit and remote RXD cells during that stall. Normal case checks XON completion; optional cancellation puts X ahead of Escape before XON and checks retired owner/TEXT, empty FIFO and no abandoned X/TAIL on wire. No product state writes or manufactured flow flags. No physical CTS/RTS, sustained saturation, printer/logging fault or hardware acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed'],checks
    print('PASS DOS XOFF TEXT stall: concurrent RX, physical XON resume and normal return')


if __name__=='__main__':main()
