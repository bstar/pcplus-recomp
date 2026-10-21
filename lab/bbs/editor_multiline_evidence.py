"""Bind multiline BIOS preparation to the independent stock TCP reference."""
import json,re,sqlite3
from pathlib import Path
from synthmodem_vm_control import ROOT,sha

STEPS=('seed30','up','home','insert-H','delete','end','down','backspace','split-newline','tail','page-up','page-up-top-visible','page-up-start','page-down','page-down-late','page-down-end','final-insert-mode')
MODES={'complete-final-screen','text-only-blocks-exit','cursor-only-blocks-exit','prerequisite-watchdog','final-screen-watchdog'}

def message_count():
 from enigma import SOURCE
 with sqlite3.connect(f'file:{SOURCE}/db/message.sqlite3?mode=ro',uri=True) as db:
  return db.execute('SELECT COUNT(*) FROM message').fetchone()[0]


def load(path):
 path=Path(path).resolve();assert path.is_relative_to(ROOT/'build')
 proof=json.loads(path.read_text());assert proof['passed'] and proof['body_key_count']==288
 assert proof['default_helper_binary_exact'] and proof['burst_helper_binary_exact']
 assert sha(path.parent/'MULTILINE.COM')==proof['production_helper_sha256']
 assert {c['mode'] for c in proof['cases']}==MODES
 assert all(v for c in proof['cases'] for v in c['checks'].values())
 for n,h in proof['inputs'].items():assert sha(ROOT/n)==h,n
 for case in proof['cases']:
  for n,h in case['captures_sha256'].items():assert sha(path.parent/case['mode']/n)==h,n
 refpath=ROOT/proof['reference'];assert refpath.is_relative_to(ROOT/'docs/validation')
 ref=json.loads(refpath.read_text());assert ref['passed'] and ref['actual_TCP_editor_reference_accepted'] and all(ref['checks'].values()) and len(ref['checks'])==25
 for group in ('inputs','server_inputs'):
  for n,h in ref[group].items():assert sha(ROOT/n)==h,n
 for n,h in ref['captures_sha256'].items():assert sha(ROOT/ref['cohort']/n)==h,n
 selected=[s for s in ref['steps'] if s['name'] in STEPS];assert [s['name'] for s in selected]==list(STEPS)
 expected=b''.join(bytes.fromhex(s['sent_hex']) for s in selected)
 assert expected.hex()==proof['expected_serial_hex']
 positions=[tuple(p) for s in selected for p in s['positions']];assert len(positions)==318
 seed=[]
 for row in range(1,31):
  seed.extend(('INS',row,col) for col in range(2,10))
  if row<30:seed.extend([('INS',row+1,1)]*2)
 assert len(seed)==298 and positions[:298]==seed
 return proof,ref,expected,positions


def check(display,online,screen,proof_path):
 proof,ref,expected,wanted=load(proof_path)
 clean=re.sub(rb'\x1b\[[0-?]*[ -/]*[@-~]',b'',display).decode('cp437')
 at=clean.find('KEYTEST');body=clean[at:] if at>=0 else ''
 matches=list(re.finditer(r'(INS|OVR) (\d{2}),(\d{2})',body))
 positions=[(m[1],int(m[2]),int(m[3])) for m in matches]
 start=online.find(b'L01:ABCD');keys=online[start:] if start>=0 else b''
 # Newline emits two position reports. Position310 is the completed TAIL
 # immediately before six page operations, before the final mode change.
 redraw=body[matches[310].end():] if len(matches)>310 else ''
 last='\n'.join(screen[i*160:i*160+160:2].decode('cp437') for i in range(25)) if len(screen)==4000 else ''
 checks=dict(multiline_subject_observed=at>=0,multiline_exact_BIOS_to_serial_body=start>=0 and keys==expected,
  multiline_all318_cursor_effects_match_TCP=positions==wanted,
  multiline_seed30_hard_lines=positions[:298]==wanted[:298] and len(positions)>=298,
  multiline_cross_line_edit_effects=positions[298:311]==wanted[298:311] and len(positions)>=311,
  multiline_page_start_and_end=positions[311:317]==wanted[311:317] and len(positions)==318,
  multiline_edited_line29_redisplayed='H29:ABCD' in redraw,
  multiline_shortened_line30_redisplayed='L30:ABC' in redraw and 'L30:ABCD' not in redraw,
  multiline_tail_redisplayed='TAIL' in redraw,
  multiline_unique_final_mode=positions[-1:]==[('OVR',31,5)],
  multiline_actual_DOS_tail_and_cursor_visible='TAIL' in last and 'OVR 31,05' in last)
 evidence=dict(positions=positions,expected_body_hex=expected.hex(),actual_DOS_body_hex=keys.hex(),body_keys=288,
  reference=proof['reference'],reference_source_commit=ref['source_commit'],key_spacing_BIOS_ticks=3,final_screen_guard=True,
  scope='Thirty seeded hard lines, real cross-line edits and newline31, three PageUp/three PageDown operations against the independently checked80x25/14-line TCP reference. Every cursor/mode response, exact authored body and edited-text redisplay are required; final DOS video must show TAIL and OVR31,05. Unsaved connection exit only; not arbitrary geometry, timing/pressure or physical hardware.')
 return checks,evidence
