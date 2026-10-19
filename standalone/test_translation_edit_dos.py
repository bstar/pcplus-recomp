#!/usr/bin/env python3
"""Production XLTEDIT child, saved mapping and confirmed live adoption in DOS."""
import argparse,hashlib,json,struct
from pathlib import Path
from check_setup_model import image
from check_directory_live import word
from test_setup_startup_dos import run,OUT,ROOT,BINARY
from test_translation_reload_dos import actions
IDENTITY=bytes(range(256))

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);p.add_argument('--sha256',required=True);p.add_argument('--case',action='append',default=[]);a=p.parse_args()
 assert a.label and all(c.isalnum() or c in '-_' for c in a.label)
 assert hashlib.sha256(BINARY.read_bytes()).hexdigest()==a.sha256
 editor=(ROOT/'build/xlt-editor/XLTEDIT.EXE').read_bytes();mapping=bytearray(IDENTITY);mapping[76]=88;mapping=bytes(mapping)
 rows=[]
 for kind in ['accept','decline','cancel','fallback','explicit','cwd','menu','missing-child']:
  if a.case and kind not in a.case:continue
  name='xlt-edit-'+a.label+'-'+kind;assert not (OUT/name).exists(),'Fresh label required'
  source='CFG/PCPLUS.XLT' if kind=='fallback' else 'CUSTOM.XLT' if kind=='explicit' else 'PCPLUS.XLT'
  files={source:IDENTITY};expected_files={};env={'PCPLUS':'D:\\CFG'} if kind=='fallback' else None
  arguments='@TEST.PRM'+(' /X:CUSTOM.XLT' if kind=='explicit' else '')
  if kind!='missing-child':files['XLTEDIT.EXE']=editor
  prefix='p2000 '
  if kind=='cwd':
   files['TEST.KEY']=actions(b'CD D:\\OTHER',(b'CD >D:\\CWD.TXT',))
   files['OTHER/PCPLUS.XLT']=bytes(reversed(IDENTITY));arguments+=' /T:TEST.KEY'
   files['CWD.TXT']=b'';expected_files['CWD.TXT']=b'D:\\OTHER\r\n'
   prefix+='a-1 p1500 space p500 a-2 p1500 space p500 '
  prefix+=('a-z right right right t' if kind=='menu' else 'a-f8')+' p1500 '
  if kind=='missing-child':keys=prefix+'space p800 r e a d y'
  else:
   edit='g home del 7 6 enter enter home del del 8 8 enter '
   keys=prefix+edit+('escape y' if kind=='cancel' else 'f1 escape')+' p600 '+('n' if kind=='decline' else 'y')+' p800 r e a d y'
   if kind!='cancel':expected_files[source]=mapping
  result,raw=run(name,keys=keys,arguments=arguments,payload=word(image(),0x1e0,1),files=files,expected_files=expected_files,
   environment=env,post_echo=True)
  folder=OUT/name;wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes()
  applied=kind in ['accept','fallback','explicit','cwd','menu']
  expected=b' XIVE' if applied else b' LIVE'
  result['checks'].update(exact_active_mapping_after_return=screen[22:32:2]==expected,
   selected_table_saved_or_retained=(folder/source).read_bytes()==(mapping if kind not in ['cancel','missing-child'] else IDENTITY),
   local_editor_keys_not_on_wire=all(x not in wire for x in [b'XLTEDIT',b'PCPLUS.XLT',b'\x1b[H',b'76',b'88']),
   no_recovery_remnants=not list(folder.rglob('XLTEDIT.BAK')) and not list(folder.rglob('XLTEDIT.$$$')))
  if kind=='cwd':result['checks']['CWD_independently_recorded']=(folder/'CWD.TXT').read_bytes()==b'D:\\OTHER\r\n'
  result['passed']=all(result['checks'].values());result['binary_sha256']=a.sha256;result['editor_sha256']=hashlib.sha256(editor).hexdigest()
  result['expected_post_receive']=expected.decode();result['table_source']=source
  (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed'],result
  rows.append(result);print(kind,'passed',flush=True)
 dest=ROOT/'build/translation-edit-dos'/a.label;dest.mkdir(parents=True,exist_ok=True)
 sources=['standalone/test_translation_edit_dos.py','standalone/test_setup_startup_dos.py','src/translation/editor_main.c','src/translation/editor_document.c','src/translation/editor_document.h','src/terminal/translation_edit.asm','src/terminal/program_actions.asm','src/config/resource_path.c']
 report=dict(passed=all(r['passed'] for r in rows),binary_sha256=a.sha256,editor_sha256=hashlib.sha256(editor).hexdigest(),cases=rows,
  sources={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sources},
  scope='Actual DOS production terminal and XLTEDIT, direct EXEC sibling selection, BIOS keys, checked file replacement, confirmed input mapping and independent UART/vector/video observations. Owned synthetic media only; no physical modem or complete application claim.')
 (dest/'checks.json').write_text(json.dumps(report,indent=2)+'\n');print('DOS live table editor passed',len(rows))
if __name__=='__main__':main()
