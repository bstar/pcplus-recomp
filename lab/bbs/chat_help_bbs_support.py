"""Source Chat/PCHELP modal return inside the stock unsaved editor."""
import json,re,struct,subprocess
from pathlib import Path
from product_inputs import ROOT,sha

SOURCES=['lab/bbs/chat_help_bbs_support.py','standalone/chat_help_bbs_watch.asm']

def inputs(binary):
 binary=binary.resolve();package=json.loads(binary.with_name('package.json').read_text())
 assert package['passed'] and package['mapped_contexts']==[3,41]
 assert package['products']['TERMINAL.EXE']==sha(binary)
 for name,digest in package['sources'].items():assert sha(ROOT/name)==digest,name
 for name,digest in package['products'].items():assert sha(binary.parent/name)==digest,name
 return [ROOT/n for n in SOURCES]+[ROOT/n for n in package['sources']]+[binary.parent/n for n in package['products']]+[binary.with_name('package.json')]

def prepare(folder,binary):
 folder=Path(folder);folder.mkdir(parents=True,exist_ok=False);binary=binary.resolve()
 inputs(binary)
 m=json.loads(binary.with_name('manifest.json').read_text());assert m['experimental_chat_help']
 listing=binary.with_name('terminal.map').read_text();symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
 ds=int(re.search(r'^DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I)[1],16)
 constants=dict(FROZEN_DELTA=symbols['redisplay_snapshot'][0]-ds,CHAT_API_VERSION=m['chat_loader']['module']['api_version'])
 for label,n in [('OWNER_OFF','_redisplay_active'),('PARSER_OFF','terminal_parser_active'),('WAIT_OFF','terminal_ansi_wait_active'),('ACTIVE_OFF','terminal_program_active'),('KIND_OFF','terminal_program_kind')]:
  seg,off=symbols[n];assert seg==ds;constants[label]=off
 observer=folder/'BBHELP.COM';subprocess.run(['nasm','-fbin',*['-D'+n+'='+str(v) for n,v in constants.items()],str(ROOT/SOURCES[1]),'-o',str(observer)],check=True)
 proof=dict(constants=constants,observer=str(observer.relative_to(ROOT)),observer_sha256=sha(observer),products=json.loads(binary.with_name('package.json').read_text())['products'])
 (folder/'observer.json').write_text(json.dumps(proof,indent=2)+'\n');return observer,proof

def audit(output,proof):
 output=Path(output);capture=output/'BBHELP.BIN';raw=capture.read_bytes() if capture.exists() else b'';words=struct.unpack_from('<26H',raw) if len(raw)==20052 else None
 frames=[raw[52+i*4000:52+(i+1)*4000] for i in range(5)]
 before,chat,helper,returned,after=frames;wire=(output/'serial-received.bin').read_bytes();post=wire.split(b'KEYTEST\r',1)[1] if b'KEYTEST\r' in wire else None
 checks=dict(observer_complete=words is not None and words[:3]==(0x4845,4,1),actual25_rows=words is not None and words[5]==25,
  exact_editor_logical_frame=before[:3840]==after[:3840],exact_Chat_frame=chat==returned,
  editor_cursor_shape=words is not None and words[6]==words[10] and words[11]==words[15],Chat_cursor_shape=words is not None and words[7]==words[9] and words[12]==words[14],
  actual_context3=helper[2:20:2]==b'Chat Mode',unfinished_input_retained=chat[3200:3202:2]==b'X' and returned[3200:3202:2]==b'X',
  Help_PROGRAM_state=words is not None and words[16:21]==(2,0,0,1,11),returned_Chat_state=words is not None and words[21:24]==(2,0,0),mode_restored=words is not None and words[24:26]==(0x5003,0x5003),
  actual_editor_before_after=b'KEYTEST' in before[::2] and b'KEYTEST' in after[::2],local_keys_never_reached_BBS=post is not None and b'X' not in post and b'\0' not in post,subsequent_editor_input=post is not None and b'ABCDE' in post and b'UNSAVED' in post,
  observer_unchanged=sha(ROOT/proof['observer'])==proof['observer_sha256'])
 report=dict(passed=all(checks.values()),checks=checks,observer_words=words,proof=proof,capture_sha256=sha(capture) if capture.exists() else None,sources={n:sha(ROOT/n) for n in SOURCES},scope='Actual stock Enigma unsaved editor, local Chat X/Alt-Z source helper/Chat return, then discard local X and return to the unchanged editor. BIOS hook reads actual before-frame at Chat constructor; passive timer reads four later VGA/BDA frames and parent state. Exact24 logical editor rows and full25-row Chat frames, cursors/shapes; native bottom status row excluded from editor equality because elapsed time may change. Subsequent editor semantics/independent screen reference checked by outer harness. Editor idle during Help; no claim of BBS traffic arriving inside child, physical/SIP/audio or all-layout acceptance.')
 (output/'chat-help-audit.json').write_text(json.dumps(report,indent=2)+'\n');return report
