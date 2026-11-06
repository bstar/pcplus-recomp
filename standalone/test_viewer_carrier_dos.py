#!/usr/bin/env python3
"""Carrier loss while an actual Alt-V page is owned, close, and same-parent redial."""
import argparse,asyncio,inspect,json,re,struct,subprocess,types
from pathlib import Path
import test_phone_log_carrier_terminal as carrier
from test_viewer_dialog_dos import page
ROOT=carrier.ROOT;sha=carrier.sha
PAYLOAD=b''.join(('L%03d\r\n'%i).encode() for i in range(1,49))

def prepare(binary,out,external=False):
 symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',binary.with_name('terminal.map').read_text(),re.M|re.I)}
 values=dict(ISR_SEGMENT=symbols['uart_receive_interrupt'][0],ISR_OFFSET=symbols['uart_receive_interrupt'][1],DATA_SEGMENT=symbols['process_psp'][0],PROCESS_PSP=symbols['process_psp'][1],CONNECTION_STATE=symbols['connection_state'][1],VIEWER_SEGMENT=symbols['_terminal_external_viewer_state' if external else '_terminal_viewer_dialog_state'][0],VIEWER_STATE=symbols['_terminal_external_viewer_state' if external else '_terminal_viewer_dialog_state'][1],FILE_STATE=symbols['_viewer_file_storage'][1],CONNECTION_STATUS=symbols['connection_status'][1])
 assert symbols['_viewer_file_storage'][0]==values['VIEWER_SEGMENT']
 if external:values['EXTERNAL_VIEWER']=1
 (out/'observer-defines.json').write_text(json.dumps(values,indent=2)+'\n');(out/'VIEW.DAT').write_bytes(PAYLOAD)
 subprocess.run(['nasm','-fbin',*[f'-D{k}={v}' for k,v in values.items()],str(ROOT/'standalone/viewer_carrier_watch.asm'),'-o',str(out/'VCAR.COM')],check=True)

def adapter(external=False):
 source=inspect.getsource(carrier.run_case)
 replacements={
  "out.mkdir(parents=True);binary=parent/'TERMINAL.EXE'":"out.mkdir(parents=True);binary=parent/'TERMINAL.EXE'\n    prepare(binary,out)",
  "keys='p900 enter p6000 a-d p4500 r e a d y p1800 a-x'":"keys='p900 enter p1800 a-v p500 V I E W . D A T enter p6500 p900 a-d p4500 r e a d y p1800 a-x'",
  "await asyncio.sleep(.2)\n                    writer.write(b'\\x1b[')":"await asyncio.sleep(3.3)\n                    writer.write(b'\\x1b[')",
  'D:\\\\PLWATCH T\nADDKEY':'D:\\\\PLWATCH T\nD:\\\\VCAR T\nADDKEY',
  'D:\\\\SNAP S\nD:\\\\PLWATCH':'D:\\\\SNAP S\nD:\\\\VCAR\nD:\\\\PLWATCH',
  "out/'PLWATCH.COM',out/'SLOWLOG.COM',out/'SNAP.COM'":"out/'PLWATCH.COM',out/'SLOWLOG.COM',out/'SNAP.COM',out/'VCAR.COM',out/'VIEW.DAT'",
 }
 for old,new in replacements.items():assert source.count(old)==1,(old,source.count(old));source=source.replace(old,new)
 if external:
  source=source.replace('V I E W . D A T enter p6500','V I E W . D A T p6500')
  source=source.replace("    (out/'TEST.PRM').write_bytes(config);","    config[0x35d:0x39e]=b'D:\\\\VTEST.COM'.ljust(65,b'\\0')\n    (out/'TEST.PRM').write_bytes(config);")
 m=types.ModuleType('viewer_carrier');m.__dict__.update(carrier.__dict__);m.prepare=lambda binary,out:prepare(binary,out,external)
 exec(compile(source,carrier.__file__,'exec'),m.__dict__);return m

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--external-viewer',action='store_true')
 a=p.parse_args();binary=a.terminal.resolve();manifest=json.loads(binary.with_name('manifest.json').read_text());assert manifest['experimental_file_viewer'] and sha(binary)==manifest['binary_sha256']
 names=['standalone/test_viewer_carrier_dos.py','standalone/viewer_carrier_watch.asm','standalone/test_phone_log_carrier_terminal.py','standalone/phone_log_slow_write.asm','standalone/test_phone_log_events_terminal.py','standalone/phone_log_events_watch.asm','lab/bbs/phone_log_evidence.py','standalone/directory_fixtures.py','standalone/directory_test_support.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/test_terminal.py','standalone/test_viewer_dialog_dos.py']
 frozen=dict(manifest['sources']);frozen.update({n:sha(ROOT/n) for n in names})
 for n,h in frozen.items():assert sha(ROOT/n)==h,n
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 if a.external_viewer:assert manifest['experimental_external_viewer']
 result=asyncio.run(adapter(a.external_viewer).run_case(binary.parent,out/'case','viewer-loss',0,0))
 raw=(out/'case/VCSTATE.BIN').read_bytes();words=struct.unpack_from('<16H',raw);wire=(out/'case/connection-1.bin').read_bytes()
 checks=dict(result['checks'],passive_witness_complete=len(raw)==4032 and words[:2]==(0x5658,1),online_viewer_seen=words[3]==1,offline_notice_closed_viewer=words[4]==1 and words[10:12]==(3,0),viewer_released_after_loss=words[5]==1 and words[12:14]==(0xffff,0) and words[15]==3,same_parent_reconnected_after_release=words[6]==1,exact_page_before_carrier_loss=raw[32:]==page([('L%03d'%i).encode() for i in range(1,25)]),viewer_filename_local=b'VIEW.DAT' not in wire,viewer_input_unchanged=(out/'case/VIEW.DAT').read_bytes()==PAYLOAD)
 if a.external_viewer:
  for n in ['offline_notice_closed_viewer','viewer_released_after_loss','exact_page_before_carrier_loss']:del checks[n]
  frame=raw[32:]
  checks.update(offline_closed_external=words[4]==1 and words[10:12]==(0,0),external_cookie_pending_preserved=words[5]==1 and words[12:14]==(0x5658,0),actual_external_prompt=frame[(12*80+7)*2:(12*80+24)*2:2]==b'Enter parameters:' and b'VTEST.COM Parameters' in frame[::2])
 report=dict(passed=all(checks.values()),binary_sha256=sha(binary),external_viewer=a.external_viewer,checks=checks,observer_words=words,carrier=result,sources=frozen,original_inputs=[],scope=(('Carrier loss during external parameters: passive active/pending/cookie state and actual prompt, automatic closure and same-parent redial. No child is queued and no file-handle ownership is claimed. ' if a.external_viewer else __doc__+' Passive IRQ-vector-derived parent identity, connected/disconnected state, actual page before loss, and closed file/reservation afterward. No Escape key is supplied; the ordinary offline notice must release the view before redial. DOSBox modem generates actual virtual DCD from socket abort; no product/serial state injection, SIP/audio/physical or stock-server claim.')))
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print({n:v for n,v in checks.items() if not v},flush=True)
 for n,h in frozen.items():assert sha(ROOT/n)==h,n
 assert report['passed']
if __name__=='__main__':main()
