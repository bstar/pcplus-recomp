#!/usr/bin/env python3
"""Production DOS COPY/DEL via PROGRAM, then explicit live table reload."""
import argparse,hashlib,json,struct
from pathlib import Path
from check_directory_live import word
from check_setup_model import image
from test_setup_startup_dos import run,OUT,ROOT,BINARY

def actions(command,extra=()):
 assert 0<len(command)<52
 raw=bytearray(540)
 for i in range(10):struct.pack_into('<H',raw,i*54,3)
 for i,text in enumerate((command,*extra)):
  assert i<10 and 0<len(text)<52
  struct.pack_into('<H',raw,i*54,1);raw[i*54+2:i*54+2+len(text)]=text
 return bytes(raw)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);p.add_argument('--sha256',required=True);p.add_argument('--case',choices=['accept','decline','short','missing','explicit','fallback','cwd','early-answer','menu','identity','sevenbit']);a=p.parse_args()
 assert a.label and all(c.isalnum() or c in '-_' for c in a.label)
 digest=hashlib.sha256(BINARY.read_bytes()).hexdigest();assert digest==a.sha256
 mapping=bytearray(range(256));mapping[ord('L')]=ord('X');mapping=bytes(mapping)
 results=[]
 for kind in ([a.case] if a.case else ['accept','decline','short','missing','explicit','fallback','cwd','early-answer','menu','identity','sevenbit']):
  name='xlt-reload-'+a.label+'-'+kind;assert not (OUT/name).exists(),'Use a fresh label'
  target='CUSTOM.XLT' if kind=='explicit' else 'CFG/PCPLUS.XLT' if kind=='fallback' else 'PCPLUS.XLT'
  table=bytes(255) if kind=='short' else mapping
  files={target:bytes(range(256)),'NEW.XLT':table};expected_files={}
  mode=0 if kind=='identity' else 2 if kind=='sevenbit' else 1
  arguments='@TEST.PRM'+(' SOFT' if kind=='early-answer' else '');environment={'PCPLUS':'D:\\CFG'} if kind=='fallback' else None
  if kind=='explicit':arguments+=' /X:CUSTOM.XLT'
  if kind in ('identity','sevenbit'):
   keys='p2000 a-f9 p500 r e a d y'
  else:
   dos_target=('D:\\'+target.replace('/','\\')).encode()
   command=b'DEL '+dos_target if kind=='missing' else b'COPY /B /Y D:\\NEW.XLT '+dos_target
   extra=(b'CD D:\\OTHER',b'CD >D:\\CWD.TXT') if kind=='cwd' else ()
   files['TEST.KEY']=actions(command,extra);arguments+=' /T:TEST.KEY'
   if kind=='cwd':
    other=bytearray(range(256));other[ord('L')]=ord('Z')
    files['OTHER/PCPLUS.XLT']=bytes(other);files['CWD.TXT']=b''
    expected_files['CWD.TXT']=b'D:\\OTHER\r\n'
   expected_files[target]=None if kind=='missing' else table
   selection='a-z p300 right p200 right p200 right p200 r' if kind=='menu' else 'a-f9'
   answer='n' if kind=='decline' else 'space' if kind in ('short','missing') else 'y'
   change_cwd='a-2 p1500 space p500 a-3 p1500 space p500 ' if kind=='cwd' else ''
   keys='p2000 a-1 p1500 space p500 '+change_cwd+selection+' p500 '+answer+' p500 r e a d y'
   if kind=='early-answer':keys='p2000 a-1 p1500 space p500 ! p500 a-f9 p100 y p2000 r e a d y'
  proof,raw=run(name,keys=keys,arguments=arguments,payload=word(image(),0x1e0,mode),
   post_echo=True,rate_mask=1,line_mask=1,files=files,expected_files=expected_files,environment=environment,pause_after_input=b'!' if kind=='early-answer' else None)
  expected=b' XIVE' if kind in ('accept','explicit','fallback','cwd','early-answer','menu') else b' LIVE'
  folder=OUT/name;screen=(folder/'SCREEN.BIN').read_bytes();wire=(folder/'serial.bin').read_bytes()
  proof['checks'].update(post_reload_input_proves_active_table=screen[22:32:2]==expected,
   exact_saved_PRM_unchanged=raw==word(image(),0x1e0,mode),
   local_reload_and_program_commands_not_transmitted=b'COPY' not in wire and b'PCPLUS.XLT' not in wire and b'CUSTOM.XLT' not in wire and b'\x1b[C' not in wire)
  if kind=='early-answer':
   proof['checks']['early_answer_not_leaked_and_paused_reply_drained']=wire.count(b'\x1b[0n')>=2 and b'ready' in wire and b'y' not in wire[:wire.index(b'ready')]
  proof['passed']=all(proof['checks'].values());assert proof['passed'],proof
  proof.update(expected_post_receive=expected.decode('ascii'),table_source=target,
   expected_file_mutations={k:None if v is None else hashlib.sha256(v).hexdigest() for k,v in expected_files.items()})
  (folder/'result.json').write_text(json.dumps(proof,indent=2)+'\n');results.append(proof)
 result=dict(passed=True,binary_sha256=digest,cases=results,sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in
  ['standalone/test_translation_reload_dos.py','standalone/test_setup_startup_dos.py','standalone/check_setup_model.py','standalone/test_terminal.py',
   'src/terminal/translation_reload.asm','src/terminal/program_actions.asm','src/translation/xlt_live.c','src/translation/xlt_live.h']},
  scope='Actual DOS production PROGRAM/COMMAND COPY or DEL changes owned table files, then AltF9 or menu reload confirms/declines/acknowledges failure. Exact file mutations, unchanged sources/PRM, independent UART/PIC/vector/divisor samples, post-return input transform and real cursor reply. No test child, original executable, BBS or physical modem claim.')
 dest=ROOT/'build/translation-reload-dos'/a.label;dest.mkdir(parents=True,exist_ok=False)
 (dest/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print('DOS table reload passed',len(results),digest)
if __name__=='__main__':main()
