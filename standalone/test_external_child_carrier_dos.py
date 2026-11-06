#!/usr/bin/env python3
"""Drop real virtual DCD during an external text/graphics child, then redial."""
import argparse,asyncio,inspect,json,re,struct,subprocess,types
from pathlib import Path
import test_phone_log_carrier_terminal as carrier
ROOT=carrier.ROOT;sha=carrier.sha

def adapter(graphics,binary,tool='viewer'):
 source=inspect.getsource(carrier.run_case)
 def replace(old,new):
  nonlocal source
  assert source.count(old)==1,(old,source.count(old));source=source.replace(old,new,1)
 replace("out.mkdir(parents=True);binary=parent/'TERMINAL.EXE'","out.mkdir(parents=True);binary=parent/'TERMINAL.EXE'\n    prepare(out)")
 replace("keys='p900 enter p6000 a-d p4500 r e a d y p1800 a-x'","keys='p900 enter p2500 a-v p900 enter p8000 a-d p4500 r e a d y p1800 a-x'")
 replace("await asyncio.sleep(.2)\n                    writer.write(b'\\x1b[')","await asyncio.sleep(4.5)\n                    writer.write(b'\\x1b[')")
 replace("    (out/'TEST.PRM').write_bytes(config);","    config[0x35d:0x39e]=b'D:\\\\VLOSS.COM'.ljust(65,b'\\0')\n    (out/'TEST.PRM').write_bytes(config);")
 if tool=='editor':
  source=source.replace('a-v p900','a-a p900').replace('config[0x35d:0x39e]','config[0x39e:0x3df]')
 replace("out/'PLWATCH.COM',out/'SLOWLOG.COM',out/'SNAP.COM'","out/'PLWATCH.COM',out/'SLOWLOG.COM',out/'SNAP.COM',out/'VLOSS.COM',out/'VACT.COM'")
 replace('D:\\\\PLWATCH T\nADDKEY','D:\\\\PLWATCH T\nD:\\\\VACT T\nADDKEY')
 replace('D:\\\\SNAP S\nD:\\\\PLWATCH','D:\\\\SNAP S\nD:\\\\VACT\nD:\\\\PLWATCH')
 def prepare(out):
  subprocess.run(['nasm','-fbin',*(['-DGRAPHICS_CHILD'] if graphics else []),str(ROOT/'standalone/external_carrier_child.asm'),'-o',str(out/'VLOSS.COM')],check=True)
  symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',binary.with_name('terminal.map').read_text(),re.M|re.I)}
  values=dict(ISR_SEGMENT=symbols['uart_receive_interrupt'][0],ISR_OFFSET=symbols['uart_receive_interrupt'][1],DATA_SEGMENT=symbols['process_psp'][0],PROCESS_PSP=symbols['process_psp'][1],CONNECTION_STATE=symbols['connection_state'][1],PROGRAM_ACTIVE=symbols['terminal_program_active'][1],PROGRAM_PENDING=symbols['terminal_program_pending'][1],EXTERNAL_SEGMENT=symbols['_terminal_external_viewer_state'][0],EXTERNAL_STATE=symbols['_terminal_external_viewer_state'][1])
  subprocess.run(['nasm','-fbin',*[f'-D{k}={v}' for k,v in values.items()],str(ROOT/'standalone/external_carrier_watch.asm'),'-o',str(out/'VACT.COM')],check=True)
 m=types.ModuleType('external_child_carrier');m.__dict__.update(carrier.__dict__);m.prepare=prepare
 exec(compile(source,carrier.__file__,'exec'),m.__dict__);return m

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--tool',choices=['viewer','editor'],default='viewer')
 p.add_argument('--case',choices=['text','graphics']);a=p.parse_args();binary=a.terminal.resolve();m=json.loads(binary.with_name('manifest.json').read_text());assert m['experimental_external_viewer'] and sha(binary)==m['binary_sha256']
 if a.tool=='editor':assert m['experimental_external_editor']
 names=['standalone/test_external_child_carrier_dos.py','standalone/external_carrier_child.asm','standalone/external_carrier_watch.asm','standalone/test_phone_log_carrier_terminal.py','standalone/phone_log_slow_write.asm','standalone/test_phone_log_events_terminal.py','standalone/phone_log_events_watch.asm','lab/bbs/phone_log_evidence.py','standalone/directory_fixtures.py','standalone/directory_test_support.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/test_terminal.py']
 frozen=dict(m['sources']);frozen.update({n:sha(ROOT/n) for n in names})
 for n,h in frozen.items():assert sha(ROOT/n)==h,n
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True);rows=[]
 for name in ['text','graphics']:
  if a.case and a.case!=name:continue
  r=asyncio.run(adapter(name=='graphics',binary,a.tool).run_case(binary.parent,out/name,name,0,0));raw=(out/name/'VLOSS.BIN').read_bytes();words=struct.unpack('<14H',raw)
  checks=dict(r['checks'],owned_child_report=words[:2]==(0xc156,1),child_IRQs_enabled=bool(words[2]&0x200) and bool(words[10]&0x200),actual_child_DCD_high_then_low=words[6:8]==(1,1) and bool(words[3]&0x80) and not(words[11]&0x80),DTR_preserved_RTS_paused=words[4]&3==1 and words[12]&3==1,UART_IER_quiet=words[5]==words[13]==0,child_wait_bounded=0<words[8]<162)
  live=(out/name/'VACT.BIN').read_bytes();state=struct.unpack_from('<16H',live);frame=live[32:]
  checks.update(live_second_connection_witness=len(live)==4032 and state[:2]==(0xca56,1) and state[3]==1 and state[5]==6,foreground_owners_released=state[6:11]==(0,0,0x5658,0,0),live_text_geometry_restored=state[11:13]==(0x5003,25) and state[15]==16,live_redial_display=frame[::2].startswith(b'FIRST BYTE SAFE') and frame[160:178:2]==b'REDIAL OK' and frame[320:330:2]==b'KEYOK')
  row=dict(live_words=state,live_capture_sha256=sha(out/name/'VACT.BIN'),case=name,passed=all(checks.values()),checks=checks,child_words=words,child_report_sha256=sha(out/name/'VLOSS.BIN'),carrier=r);rows.append(row);print(name,{n:v for n,v in checks.items() if not v},flush=True)
 for n,h in frozen.items():assert sha(ROOT/n)==h,n
 result=dict(passed=all(r['passed'] for r in rows),external_command_tool=a.tool,binary_sha256=sha(binary),cases=rows,sources=frozen,original_inputs=[],scope=__doc__+' Built-in DOSBox modem and socket closure create actual virtual carrier changes. Owned child only reads UART MSR/MCR/IER, BIOS ticks and flags, optionally switches mode13h, and records them; no parent/serial-state injection. A read-only IRQ-derived timer witness captures live KEYOK on the second connection before parent exit, verifies mode3/25rows/font16 and cleared PROGRAM/external owners. Parent must recover UART/graphics, notice carrier loss and complete another dial/log/accounting cycle. Physical CTS, SIP/audio/DSP/analog and arbitrary external children remain unverified.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed'],'See result.json'
if __name__=='__main__':main()
