#!/usr/bin/env python3
"""Replay original captured edit keys against the source-built DOS application.

Explicit original-ui evidence is a compatibility-test input, never an application
build input. Compare recorded field/cursor/shape and actual VGA window bytes.
"""
import argparse,hashlib,json,shutil,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
ROOT=harness.ROOT
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def crop(frame,modal=False):
 return b''.join(frame[(r*80+c)*2:(r*80+c)*2+2] for r in range(5,14 if modal else 10) for c in (range(80) if modal else range(1,77)))
def field(frame):return frame[(7*80+13)*2:(7*80+75)*2:2].decode('cp437')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True)
 p.add_argument('--original-ui',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--case',choices=('overwrite-final','limit-final','toggle-final','navigation-final','menu-final','retry','right-final','insert-escape-final','insert-full-final','end-full-final'))
 a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve();reference=a.original_ui.resolve()
 assert out.is_relative_to(ROOT/'build') and not out.exists() and reference.is_relative_to(ROOT/'build')
 evidence=json.loads(reference.read_text());assert evidence['passed'] and evidence['original_sha256']=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
 manifest=json.loads(binary.with_name('manifest.json').read_text());assert manifest['experimental_path_control'] and manifest['binary_sha256']==sha(binary)
 out.mkdir(parents=True);package=out/'package';package.mkdir();shutil.copyfile(binary,package/'TERMINAL.EXE');(package/'TARGET').mkdir()
 observer=out/'EDITOBS.COM';subprocess.run(['nasm','-fbin',str(ROOT/'standalone/path_editor_watch.asm'),'-o',str(observer)],check=True)
 assert observer.stat().st_size<=65280
 settings=bytearray(prm(port=3,baud=5))
 for at,val in ((0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0)):
  struct.pack_into('<H',settings,at,val)
 harness.BINARY=package/'TERMINAL.EXE';cases=[]
 for label,original in evidence['cases'].items():
  if a.case and label!=a.case:continue
  source=reference.parent/label/'c/EDITVIEW.BIN';assert sha(source)==original['video_sha256']
  raw=source.read_bytes();expected=[]
  for item in original['frames']:
   i=item['index'];f=bytearray(raw[10+i*4004:4010+i*4004]);assert len(f)==4000 and hashlib.sha256(f).hexdigest()==item['sha256']
   modal=item['cursor']==[100,200] and item['shape']&0x2000
   if item['cursor'][0]!=7 and not modal:continue
   # Only startup default-drive header C: differs in these owned fixtures.
   assert f[(5*80+18)*2]==ord('C');f[(5*80+18)*2]=ord('D')
   expected.append(dict(field=item['field'],cursor=item['cursor'],shape=item['shape'],pixels=crop(f,modal),modal=bool(modal)))
  assert expected
  keys=original['keys'].split('a-x',1)[0].replace('p750 enter p3250','p900 enter p3500',1)
  keys+='r e a d y enter p1000 a-x'
  assert len('ADDKEY '+keys)<500
  name=out.name+'-'+label;drive=ROOT/'build/connection-dos'/name;assert not drive.exists()
  base=harness.run(name,'success',keys,prm=bytes(settings),arguments='@TEST.PRM /D:CaseTest:23',com=3,irq=5,cpu='8086',working_drive='d',
   files={'EDITOBS.COM':observer.read_bytes()},observer='EDITOBS',timeout=40,
   online_triggers=((b'ready\r',b'\x1b[3;1HAFTER-EDITOR-PARITY\x1b[6n'),))
  actual=(drive/'EDITVIEW.BIN').read_bytes();assert len(actual)==32044
  before_cursor,saved_shape=struct.unpack_from('<2H',actual,32040)
  magic,count,ticks,restored=struct.unpack_from('<4H',actual);frames=[]
  for i in range(count):
   cur,shape=struct.unpack_from('<2H',actual,8+i*4004);f=actual[12+i*4004:4012+i*4004]
   frames.append(dict(cursor=[cur>>8,cur&255],shape=shape,field=field(f),pixels=f))
  checks=dict(base['checks']);checks['passive_observer_restored']=magic==0x5056 and 0<count<=8 and ticks>2 and restored==1
  # Native reference uses saved0607; this parent fixture independently starts
  # with060F. Compare the recovered dynamic formula, without hardcoding either
  # end scanline into production or inferring the saved shape from its output.
  reference_shapes={0x0607:saved_shape&0x1f1f,
   0x0407:((((saved_shape&31)>>1)+1)<<8)|(saved_shape&31),
   0x2607:(saved_shape&0x1f1f)|0x2000}
  at=0;matches=[]
  for index,want in enumerate(expected):
   assert want['shape'] in reference_shapes
   want['shape']=reference_shapes[want['shape']]
   while at<len(frames) and not all(frames[at][k]==want[k] for k in ('field','cursor','shape')):at+=1
   checks['original_edit_stage_'+str(index)]=at<len(frames)
   if at<len(frames):
    checks['original_window_pixels_'+str(index)]=crop(frames[at]['pixels'],want['modal'])==want['pixels'];matches.append(at);at+=1
  if label in ('toggle-final','insert-escape-final','right-final','limit-final','end-full-final','menu-final'):
   checks['Escape_restores_live_cursor_and_shape']=any(f['cursor']==[before_cursor>>8,before_cursor&255] and f['shape']==saved_shape and f['pixels'][:30:2]==b'FIRST BYTE SAFE' for f in frames)
  wire=(drive/'serial.bin').read_bytes();checks['ordinary_input_after_dialog']=wire.count(b'ready\r')==1
  result=dict(case=label,passed=all(checks.values()),checks=checks,original_stages=len(expected),matched_frames=matches,saved_shape=saved_shape,reference_saved_shape=0x0607,
   captured=[{k:v for k,v in f.items() if k!='pixels'} for f in frames],result=str(drive/'result.json'))
  cases.append(result);(out/(label+'.json')).write_text(json.dumps(result,indent=2)+'\n')
  print(label,{k:v for k,v in checks.items() if not v},flush=True);assert result['passed'],result
 sources=('standalone/test_path_editor_parity_dos.py','standalone/path_editor_watch.asm','standalone/test_connection_dos.py','standalone/test_terminal.py','standalone/directory_fixtures.py','standalone/directory_test_support.py','standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py')
 report=dict(passed=True,binary_sha256=sha(binary),cases=cases,original_evidence=dict(path=str(reference.relative_to(ROOT)),sha256=sha(reference)),
  sources={n:sha(ROOT/n) for n in sources},scope=__doc__+' DOSBox-X8086, synthetic serial modem; explicit C-to-D header normalization. Reference saved cursor shape0607 differs from this fixture060F; independently observed saved shape and the original dynamic Insert/hidden formulas determine expected shape. No original executable is executed or supplied to the build; original UI capture is required by this compatibility test. No physical acceptance.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
