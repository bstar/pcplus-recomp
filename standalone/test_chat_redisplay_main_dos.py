#!/usr/bin/env python3
"""Normal main/real keyboard/synthetic UART Chat Redisplay suspend and resume."""
import argparse,json,re,shutil,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
from build_path_session import ROOT,sha

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('terminal','output'):p.add_argument('--'+n,type=Path,required=True)
 a=p.parse_args();binary,out=a.terminal.resolve(),a.output.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists()
 m=json.loads(binary.with_name('manifest.json').read_text());assert m['experimental_chat_redisplay'] and sha(binary)==m['binary_sha256']
 names=('standalone/test_chat_redisplay_main_dos.py','standalone/chat_redisplay_watch.asm','standalone/test_connection_dos.py','standalone/directory_fixtures.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/test_terminal.py','standalone/directory_test_support.py','standalone/build_path_session.py')
 sources={**m['sources'],**{n:sha(ROOT/n) for n in names}}
 for n,h in sources.items():assert sha(ROOT/n)==h,n
 listing=binary.with_name('terminal.map').read_text()
 syms={n:(int(seg,16),int(off,16)) for seg,off,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 ds=int(re.search(r'^DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I)[1],16)
 constants={'FROZEN_DELTA':syms['redisplay_snapshot'][0]-ds,'LIVE_DELTA':syms['redisplay_live'][0]-ds,'LIVE_OFF':syms['redisplay_live'][1]}
 for label,n in [('OWNER_OFF','_redisplay_active'),('VIEW_OFF','_chat_view_active')]:
  seg,off=syms[n];assert seg==ds;constants[label]=off
 out.mkdir();stage=out/'program';stage.mkdir()
 shutil.copyfile(binary,stage/'TERMINAL.EXE');shutil.copyfile(binary.parent/'PCCHAT.OVL',stage/'PCCHAT.OVL')
 observer=out/'VIEWW.COM';subprocess.run(['nasm','-fbin',*['-D'+k+'='+str(v) for k,v in constants.items()],str(ROOT/'standalone/chat_redisplay_watch.asm'),'-o',str(observer)],check=True)
 settings=bytearray(prm(port=3,baud=5))
 for off,value in [(0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x1e4,0)]:struct.pack_into('<H',settings,off,value)
 keys='p900 enter p5000 a-o p1800 A B a-f6 p12000 home p900 escape p1500 enter p1800 escape p1000 N O R M A L p1400 a-x'
 harness.BINARY=stage/'TERMINAL.EXE';name=out.name+'-main';capture=ROOT/'build/connection-dos'/name;assert not capture.exists()
 r=harness.run(name,'success',keys,prm=bytes(settings),com=3,irq=5,cpu='8086',working_drive='d',timeout=50,arguments='@TEST.PRM /D:CaseTest:23',files={'VIEWW.COM':observer.read_bytes()},observer='VIEWW',banner=b'\x1b[2J\x1b[H'+b'HISTORY\r\n'*40+b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0c',online_updates=[(9,b'RXLIVE\xf0\x1b[6n')],online_triggers=[(b'NORMAL',[(0,b'BACK\x1b[6n')])])
 words=struct.unpack('<8H',(capture/'CHATVIEW.BIN').read_bytes());wire=(capture/'serial.bin').read_bytes();screen=(capture/'SCREEN.BIN').read_bytes()[::2]
 replies=re.findall(rb'\x1b\[(\d+);(\d+)R',wire)
 checks=dict(harness=r['passed'],observer_identity=words[0]==0x5657,viewer_seen=bool(words[1]&1) and words[2]>0,remote_empty_when_viewer_opened=bool(words[1]&16),raw_RX_and_local_input_while_viewing=bool(words[1]&2) and words[3]>0,resumed_Chat_retains_both_panes=bool(words[1]&4) and words[4]>0,local_line_transmitted_once=wire.count(b'AB\r')==1,Chat_navigation_not_transmitted=b'AB\rNORMAL' in wire,Chat_escape_sequence_not_interpreted=len(replies)==2,normal_parser_restored=b'BACK' in screen and b'Chat Mode' not in screen,sources_unchanged=all(sha(ROOT/n)==h for n,h in sources.items()),module_unchanged=sha(stage/'PCCHAT.OVL')==m['chat_loader']['module']['binary_sha256'])
 report=dict(passed=all(checks.values()),checks=checks,observer_words=words,constants=constants,sources=sources,binary_sha256=sha(binary),module_sha256=sha(stage/'PCCHAT.OVL'),capture=str(capture.relative_to(ROOT)),scope=__doc__+' Passive INT16 observer confirms an initially empty remote pane, later raw CP437 RX in the hidden live Chat frame while viewer owns the screen, retained AB input and visible resumed panes. No product state writes. No physical modem/SIP/audio acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(checks,indent=2));assert report['passed']

if __name__=='__main__':main()
