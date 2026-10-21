#!/usr/bin/env python3
"""Pinned owned Synchronet inputs and fresh read-only reference navigation."""
import argparse,configparser,hashlib,json,re,subprocess,tarfile
from pathlib import Path
from synchronet import ROOT,LAB,RUNTIME,PORT,COMMIT,ARTIFACTS,Peer


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def server_pid():
 text=subprocess.check_output(['ss','-ltnp',f'( sport = :{PORT} )'],text=True)
 pids=set(map(int,re.findall(r'pid=(\d+)',text)));assert len(pids)==1,text
 pid=pids.pop();cmd=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
 assert cmd[0].endswith(b'sbbs') and str(RUNTIME/'ctrl').encode() in cmd
 assert f'127.0.0.1:{PORT}' in text and f'0.0.0.0:{PORT}' not in text
 return pid


def snapshot():
 pid=server_pid()
 for n,h in ARTIFACTS.items():assert sha(LAB/n)==h,n
 with tarfile.open(LAB/'sbbs_dev.tgz') as archive:
  members=[m for m in archive.getmembers() if m.isfile() and Path(m.name).name=='sbbs'];assert len(members)==1
  assert hashlib.sha256(archive.extractfile(members[0]).read()).hexdigest()==sha(RUNTIME/'exec/sbbs')
 files=[]
 for directory in ('ctrl','exec','text','mods'):
  files += [p for p in (RUNTIME/directory).rglob('*') if p.is_file() and (directory!='ctrl' or (p.suffix=='.ini' and p.name!='dsts.ini'))]
 inputs={str(p.relative_to(RUNTIME)):sha(p) for p in sorted(files)}
 libraries={}
 for line in Path(f'/proc/{pid}/maps').read_text().splitlines():
  leaf=line.split()[-1]
  if leaf.startswith('/') and '.so' in Path(leaf).name and Path(leaf).is_file():libraries[leaf]=sha(leaf)
 return {'pid':pid,'port':PORT,'source_commit':COMMIT,'binary_sha256':sha(RUNTIME/'exec/sbbs'),
  'server_inputs':inputs,'server_libraries':libraries,'archives':ARTIFACTS}


def message_bodies():
 return {str(p.relative_to(RUNTIME)):sha(p) for p in sorted((RUNTIME/'data/subs').glob('*.sdt'))}


def statistics():
 # Official getstats.c/logon.cpp classify ctrl/dsts.ini as daily runtime data.
 p=configparser.ConfigParser();p.read_string('[Global]\n'+(RUNTIME/'ctrl/dsts.ini').read_text())
 return {section:dict(p[section]) for section in p.sections()}


def reference(out):
 out=out.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
 before=snapshot();bodies=message_bodies();stats=statistics();steps=[];checks={};failure=None
 with Peer() as peer:
  def phase(label,data,needle):
   peer.text.clear();peer.scan_from=0
   if data:peer.send(data,label)
   peer.wait(needle,30);peer.pump(.3)
   (out/(label+'.bin')).write_bytes(peer.text);(out/(label+'.txt')).write_text(peer.clean)
   steps.append(label);return peer.clean
  try:
   phase('login',b'','Login:');phase('password',b'LABUSER\r','Password:')
   phase('welcome',b'LABPASS42\r','[Hit a key]')
   phase('bulletins',b' ','Enter number of bulletin or [Quit]')
   text=phase('statistics',b'1\r','Enter number of bulletin or [Quit]');checks['read_only_bulletin']='System Totals:' in text
   phase('scan',b'Q','Search all groups for new messages?');phase('pause',b'n\r','[Hit a key]')
   phase('main',b' ','Read/Post Messages')
   phase('files',b'T','List Files in dir');phase('return',b'Q','Read/Post Messages')
   text=phase('messages',b'R','No messages have been posted on ');checks['owned_empty_message_area']='Local General' in text or 'Local Notices' in text
   phase('final',b'Q','Read/Post Messages');checks['complete_reference_route']=True
   checks['no_unrecognized_command']='Unrecognized command' not in Peer.cleaned(peer.history)
  except Exception as error:
   failure=repr(error);checks['complete_reference_route']=False
  finally:
   (out/'server-wire.bin').write_bytes(peer.rx);(out/'client-wire.bin').write_bytes(peer.tx)
   (out/'transcript.txt').write_text(Peer.cleaned(peer.history))
   (out/'events.json').write_text(json.dumps(peer.events,indent=2)+'\n')
 after=snapshot();checks['pinned_server_inputs_preserved']=before==after
 checks['message_bodies_preserved']=message_bodies()==bodies
 after_stats=statistics()
 checks['no_message_mail_or_transfer_writes']=all(stats['Total'][key]==after_stats['Total'][key] for key in ('uploads','uploadb','dnloads','dnloadb','posts','email','feedback'))
 result={'passed':all(checks.values()),'checks':checks,'error':failure,'steps':steps,'server':before,
  'message_bodies':bodies,'statistics_before':stats,'statistics_after':after_stats,'reference_inputs':{str(Path(__file__).relative_to(ROOT)):sha(__file__),'lab/bbs/synchronet.py':sha(ROOT/'lab/bbs/synchronet.py')},
  'scope':'Fresh loopback reference client: synthetic login, bulletin1, file section, return, read empty owned local message area, final main menu. Official archived server ELF verified; code/config/menu/library and message-body bytes preserved. Reference supplies declared fixed CPR and ANSI Telnet negotiation; not native DOS or SIP/audio/physical acceptance.'}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'checks':checks,'error':failure,'steps':steps}));assert result['passed']

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reference-output',type=Path,required=True);a=p.parse_args();reference(a.reference_output)
