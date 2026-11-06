#!/usr/bin/env python3
"""External graphics child, real partial Y/ZMODEM transfer, carrier loss and redial."""
import argparse,asyncio,inspect,json,struct,subprocess,types
from pathlib import Path
import test_phone_log_carrier_terminal as carrier
ROOT=carrier.ROOT;sha=carrier.sha

def adapter(tool='viewer'):
 source=inspect.getsource(carrier.run_case)
 def replace(old,new):
  nonlocal source
  assert source.count(old)==1,(old,source.count(old));source=source.replace(old,new,1)
 replace("out.mkdir(parents=True);binary=parent/'TERMINAL.EXE'","out.mkdir(parents=True);binary=parent/'TERMINAL.EXE'\n    prepare(out)")
 replace("keys='p900 enter p2500 '+('a-s' if upload else 'a-r')","keys='p900 enter p2500 a-v p700 enter p2000 '+('a-s' if upload else 'a-r')")
 replace("    (out/'TEST.PRM').write_bytes(config);","    config[0x35d:0x39e]=b'D:\\\\VTEST.COM'.ljust(65,b'\\0')\n    (out/'TEST.PRM').write_bytes(config);")
 if tool=='editor':
  source=source.replace('a-v p700','a-a p700').replace('config[0x35d:0x39e]','config[0x39e:0x3df]')
 replace("out/'PLWATCH.COM',out/'SLOWLOG.COM',out/'SNAP.COM'","out/'PLWATCH.COM',out/'SLOWLOG.COM',out/'SNAP.COM',out/'VTEST.COM'")
 # The extra viewer adds2.7 seconds to the existing bounded transfer recipe.
 replace('32 if aspect else 28 if transfer else 23','38')
 def prepare(out):
  text=(ROOT/'standalone/viewer_external_child.asm').read_text();needle=' mov ax,4c00h';assert text.count(needle)==1
  text=text.replace(needle,' mov ax,13h\n int 10h\n'+needle);(out/'child.asm').write_text(text)
  subprocess.run(['nasm','-fbin',str(out/'child.asm'),'-o',str(out/'VTEST.COM')],check=True)
 m=types.ModuleType('external_before_transfer_loss');m.__dict__.update(carrier.__dict__);m.prepare=prepare
 exec(compile(source,carrier.__file__,'exec'),m.__dict__);return m

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ['terminal','output']:p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--tool',choices=['viewer','editor'],default='viewer')
 a=p.parse_args();binary=a.terminal.resolve();m=json.loads(binary.with_name('manifest.json').read_text());assert m['experimental_external_viewer'] and sha(binary)==m['binary_sha256']
 if a.tool=='editor':assert m['experimental_external_editor']
 names=['standalone/test_external_before_transfer_carrier.py','standalone/viewer_external_child.asm','standalone/test_phone_log_carrier_terminal.py','standalone/batch_carrier_peer.py','standalone/check_zmodem_wire.py','standalone/phone_log_slow_write.asm','standalone/test_phone_log_events_terminal.py','standalone/phone_log_events_watch.asm','lab/bbs/phone_log_evidence.py','standalone/directory_fixtures.py','standalone/directory_test_support.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py','standalone/test_terminal.py']
 frozen=dict(m['sources']);frozen.update({n:sha(ROOT/n) for n in names})
 for n,h in frozen.items():assert sha(ROOT/n)==h,n
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True);rows=[]
 for name,transfer in [('ymodem-receive-retained',dict(protocol=1,upload=False,partial=True,retained=True)),('zmodem-upload-partial',dict(protocol=2,upload=True,partial=True,retained=False))]:
  r=asyncio.run(adapter(a.tool).run_case(binary.parent,out/name,name,0,0,transfer=transfer));child=(out/name/'VCHILD.BIN').read_bytes()
  checks=dict(r['checks'],actual_external_child=len(child)==202 and struct.unpack_from('<2H',child)==(0x5645,1),empty_parameters=child[8]==0,child_CWD=len(child)==202 and struct.unpack_from('<H',child,136)[0]==3 and child[138]==0)
  row=dict(case=name,passed=all(checks.values()),checks=checks,child_report_sha256=sha(out/name/'VCHILD.BIN'),carrier=r);rows.append(row);print(name,{n:v for n,v in checks.items() if not v},flush=True)
 for n,h in frozen.items():assert sha(ROOT/n)==h,n
 result=dict(passed=all(r['passed'] for r in rows),external_command_tool=a.tool,binary_sha256=sha(binary),cases=rows,sources=frozen,original_inputs=[],scope=__doc__+' Owned child records actual PSP/CWD then leaves mode13h. Independent peers require real CRC-checked transfer progress before socket abort changes virtual DCD. Parent must clean partial files/owners, preserve a completed YMODEM file, log/account two sessions and accept fresh input after redial. No parent-state injection, SIP/audio, physical CTS or arbitrary-program acceptance.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed'],'See result.json'
if __name__=='__main__':main()
