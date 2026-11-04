#!/usr/bin/env python3
"""Execute linked startup identity publication and absolute setup preparation."""
import argparse
import hashlib
import json
from pathlib import Path
from check_cwd_xlt_identities import Model

ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
NAMES=['terminal_config_path','terminal_directory_path','terminal_keyboard_path','terminal_actions_path','terminal_translation_path']
LEAVES=[b'TEST.PRM',b'TEST.DIR',b'KEYS.KBD',b'META.KEY',b'INPUT.XLT']

def seed(m):
 for name,leaf in zip(NAMES,LEAVES):m.uc.mem_write(m.symbols[name],leaf.ljust(64,b'\0'))
 m.put('terminal_option_mask',16|64|512|4096|16384)
 for name in ['terminal_macro_active','terminal_program_pending','terminal_program_active']:m.put(name,0)

def paths(m):return [bytes(m.uc.mem_read(m.symbols[n],64)) for n in NAMES]

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 manifest=json.loads(binary.with_name('manifest.json').read_text());assert manifest['experimental_cwd_identities'] and sha(binary)==manifest['binary_sha256']
 for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
 cases=[]
 m=Model(binary);seed(m);assert m.bank('_terminal_cwd_bind_startup',far=True)==0
 expected=[(b'D:\\WORK\\'+leaf).ljust(64,b'\0') for leaf in LEAVES];assert paths(m)==expected
 m.cwd=b'E:\\OTHER';assert m.bank('_terminal_cwd_bind_startup',far=True)==0 and paths(m)==expected
 assert m.bank('_terminal_cwd_setup_command',far=True)==0
 exe=bytes(m.uc.mem_read(m.symbols['program_setup_executable'],64));tail=bytes(m.uc.mem_read(m.symbols['terminal_setup_tail'],68))
 assert exe==b'D:\\APP\\PRMEDIT.EXE'.ljust(64,b'\0') and tail==b' D:\\WORK\\TEST.PRM'.ljust(68,b'\0')
 cases.append(dict(case='five-identities-remain-absolute-and-helper-is-executable-sibling',passed=True))
 for field in ['terminal_macro_active','terminal_program_pending','terminal_program_active']:
  m.put(field,1);assert m.bank('_terminal_cwd_setup_command',far=True)==2
  assert bytes(m.uc.mem_read(m.symbols['program_setup_executable'],64))==exe and bytes(m.uc.mem_read(m.symbols['terminal_setup_tail'],68))==tail
  m.put(field,0);cases.append(dict(case='busy-preserves-command-'+field,passed=True))
 for fault in ['canonical','overlong']:
  m=Model(binary);seed(m);before=paths(m)
  if fault=='canonical':m.faults.add(b'TEST.DIR')
  else:m.cwd=b'D:\\'+b'A'*62
  assert m.bank('_terminal_cwd_bind_startup',far=True)==16 and paths(m)==before
  cases.append(dict(case='atomic-no-publication-'+fault,passed=True))
 m=Model(binary);seed(m);m.put('terminal_option_mask',0)
 m.uc.mem_write(m.symbols['program_setup_executable'],b'Z'*64);m.uc.mem_write(m.symbols['terminal_setup_tail'],b'Z'*68)
 assert m.bank('_terminal_cwd_setup_command',far=True)==1
 assert bytes(m.uc.mem_read(m.symbols['program_setup_executable'],64))==b'Z'*64
 assert bytes(m.uc.mem_read(m.symbols['terminal_setup_tail'],68))==b'Z'*68
 cases.append(dict(case='no-explicit-prm-no-command',passed=True))
 r={'passed':True,'terminal_sha256':sha(binary),'cases':cases,'sources':manifest['sources'],
  'checker_sources':{n:sha(ROOT/n) for n in ['standalone/check_cwd_startup_identities.py','standalone/check_cwd_xlt_identities.py','standalone/check_directory_identity.py','standalone/dos_image.py']},
  'scope':__doc__+' Actual C/assembly/ABI; DOS canonicalization is modeled. No application startup/UART or physical acceptance.'}
 (out/'result.json').write_text(json.dumps(r,indent=2)+'\n');print('PASS startup CWD identities:',len(cases),'cases')

if __name__=='__main__':main()
