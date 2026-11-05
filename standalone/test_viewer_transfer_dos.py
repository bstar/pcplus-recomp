#!/usr/bin/env python3
"""Actual Alt-V roundtrip followed by X/Y/ZMODEM or cancel/retry in one DOS process."""
import argparse,concurrent.futures,inspect,json,struct,subprocess,time,types
from pathlib import Path
import test_release_transfers_dos as release
from test_terminal_transfer_dos import Peer
from test_viewer_dialog_dos import page
ROOT=release.ROOT;sha=release.sha
PAYLOAD=b''.join(('L%03d\r\n'%i).encode() for i in range(1,49))

def prepare(out):
 (out/'VIEW.DAT').write_bytes(PAYLOAD)
 subprocess.run(['nasm','-fbin','-DWATCH_KIND=2',str(ROOT/'standalone/viewer_dialog_watch.asm'),'-o',str(out/'VIEWOBS.COM')],check=True)

def adapter():
 source=inspect.getsource(release.run_case)
 replacements={
  "(out / 'TEST.PRM').write_bytes(raw)":"(out / 'TEST.PRM').write_bytes(raw)\n    prepare(out)",
  "+ ['p1500'] + action + ['p300']":"+ ['p1500','a-v','p500'] + list('VIEW.DAT') + ['enter','p1100','escape','p800','g','o'] + action + ['p300']",
  'D:\\\\SNAP B\nADDKEY':'D:\\\\SNAP B\nD:\\\\VIEWOBS T\nADDKEY',
  'D:\\\\SNAP S\nD:\\\\SNAP A':'D:\\\\SNAP S\nD:\\\\VIEWOBS\nD:\\\\SNAP A',
 }
 for old,new in replacements.items():assert source.count(old)==1,(old,source.count(old));source=source.replace(old,new)
 m=types.ModuleType('viewer_transfer_release');m.__dict__.update(release.__dict__);m.prepare=prepare
 exec(compile(source,release.__file__,'exec'),m.__dict__);return m

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--case',action='append');p.add_argument('--jobs',type=int,choices=[1,2],default=1);a=p.parse_args()
 binary=a.terminal.resolve();manifest=json.loads(binary.with_name('manifest.json').read_text());assert manifest['experimental_file_viewer'] and sha(binary)==manifest['binary_sha256']
 names=['standalone/test_viewer_transfer_dos.py','standalone/test_release_transfers_dos.py','standalone/viewer_dialog_watch.asm','standalone/test_viewer_dialog_dos.py','standalone/test_terminal.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/test_terminal_transfer_dos.py','standalone/test_terminal_upload_dos.py','standalone/test_terminal_ymodem_dos.py','standalone/test_terminal_zmodem_dos.py']
 frozen=dict(manifest['sources']);frozen.update({n:sha(ROOT/n) for n in names})
 for n,h in frozen.items():assert sha(ROOT/n)==h,n
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 selected=a.case or ['x-rx-binary','x-tx-binary','y-rx-cancel-retry','y-tx-binary','z-rx-default','z-tx-escape']
 recipes=[r for r in release.recipes() if r['name'] in selected];assert len(recipes)==len(set(selected))
 original=Peer.ready
 def ready(peer):
  original(peer);peer.send(b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n');deadline=time.monotonic()+5
  while time.monotonic()<deadline:
   if b'\x1b[1;16R' in peer.pending:
    at=peer.pending.index(b'\x1b[1;16R');del peer.pending[:at+7]
    peer.log('pre-viewer-CPR');break
   peer.receive()
  else:raise TimeoutError('No pre-viewer CPR')
  # Keep receiver negotiation out of the deliberately unchanged viewer/live
  # frame comparison. A real ordinary key marker follows Escape; it cannot
  # reach this peer while the local file dialog owns keyboard input.
  deadline=time.monotonic()+8
  while time.monotonic()<deadline:
   if b'go' in peer.pending:
    at=peer.pending.index(b'go');del peer.pending[:at+2]
    peer.log('keyboard-after-viewer');return
   peer.receive()
  raise TimeoutError('No post-viewer keyboard marker')
 Peer.ready=ready;m=adapter()
 def run(recipe):
  result=m.run_case(recipe,binary,manifest,out);folder=out/recipe['name'];raw=(folder/'VIEWUI.BIN').read_bytes();words=struct.unpack_from('<9H',raw)
  checks=dict(result['checks'],complete_viewer_observer=len(raw)==12083 and words[:2]==(0x5656,15),exact_live_frame_return=raw[18:4018]==raw[8018:12018],exact_cursor_shape_return=words[3:5]==words[7:9],exact_viewer_page=raw[4018:8018]==page([('L%03d'%i).encode() for i in range(1,25)]),viewer_input_unchanged=(folder/'VIEW.DAT').read_bytes()==PAYLOAD,viewer_filename_not_remote=b'VIEW.DAT' not in (folder/'serial.bin').read_bytes(),startup_path=raw[12018]==3 and raw[12019:].split(b'\0',1)[0]==b'')
  result.update(passed=all(checks.values()),checks=checks,viewer_capture_sha256=sha(folder/'VIEWUI.BIN'),scope=__doc__+' Real DOS8086 COM3/IRQ5,19200/HARD, passive full2000-cell viewer and exact live/cursor return before transfer. Independent protocol peers; no SIP/DCD/physical or stock-server claim.')
  (folder/'viewer-result.json').write_text(json.dumps(result,indent=2)+'\n');print(recipe['name'],'VIEWER PASS' if result['passed'] else {n:v for n,v in checks.items() if not v},flush=True);assert result['passed'];return result
 try:
  with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as pool:cases=list(pool.map(run,recipes))
 finally:Peer.ready=original
 for n,h in frozen.items():assert sha(ROOT/n)==h,n
 (out/'result.json').write_text(json.dumps(dict(passed=True,binary_sha256=sha(binary),cases=cases,sources=frozen,original_inputs=[],scope=__doc__),indent=2)+'\n')
if __name__=='__main__':main()
