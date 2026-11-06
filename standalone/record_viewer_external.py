#!/usr/bin/env python3
"""Bind original external-viewer argv/parameter UI and checked source command-builder evidence."""
import argparse,json,struct
from pathlib import Path
from build_path_session import ROOT,sha
ORIGINAL='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
EXPECTED={'relative':' PAGE.DAT','absolute':' D:\\PAGE.DAT','options':' /Q /X PAGE.DAT','spaces':' D:\\A B.DAT','empty':'','cancel':None,'long':' '+'A'*48}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,action='append',required=True);p.add_argument('--component',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 def bind(path):return dict(path=str(path.resolve().relative_to(ROOT)),sha256=sha(path))
 rows=[];seen=set()
 for source in a.input:
  r=json.loads(source.read_text());name=r['case'];assert name in EXPECTED and name not in seen;seen.add(name)
  for n,h in r['sources'].items():assert sha(ROOT/n)==h,n
  assert r['process_exit']==0 and r['DOS_done'] and r['generated_unchanged'] and r['original_sha256']==ORIGINAL
  folder=source.parent;raw=(folder/'c/EDITVIEW.BIN').read_bytes();magic,count,ticks=struct.unpack_from('<3H',raw);assert len(raw)==28034 and magic==0x4544 and count>=3
  before=raw[10:4010];prompt=raw[4014:8014];after=raw[8018:12018]
  assert before==after and raw[6:10]==raw[8014:8018],'Native terminal restoration'
  assert struct.unpack_from('<H',raw,4010)[0]==0x0c19
  title=(r['command'].rsplit('\\',1)[-1]+' Parameters').encode('ascii')
  assert title in prompt[::2] and prompt[(12*80+7)*2:(12*80+24)*2:2]==b'Enter parameters:'
  assert r['PRM_offset']==0x35d and r['child_tail_text']==EXPECTED[name]
  if name=='cancel':assert r['child_report_bytes']==0 and not (folder/'d/VCHILD.BIN').exists()
  else:
   child=(folder/'d/VCHILD.BIN').read_bytes();assert len(child)==202 and struct.unpack_from('<2H',child)==(0x5645,1)
   tail=child[8:136];assert tail[0]==len(EXPECTED[name]) and tail[1:1+tail[0]]==EXPECTED[name].encode('ascii')
   assert tail[1+tail[0]]==13 and r['child_drive']==2 and r['child_cwd']==''
  rows.append(dict(case=name,report=bind(source),actual_tail=r['child_tail_text'],prompt_cursor=[12,25],exact_terminal_cells=2000,cursor_shape_restored=True,normal_DOS_exit=True,original_unchanged=True,
   captures=[bind(folder/n) for n in ['c/EDITVIEW.BIN','frame-0.bin','frame-1.bin','frame-2.bin','dosbox.conf','d/VTEST.COM']]+([bind(folder/'d/VCHILD.BIN')] if name!='cancel' else [])))
 assert seen==EXPECTED.keys()
 c=json.loads(a.component.read_text());assert c['passed'] and c['checks']==36147 and c['failures']==0 and c['original_inputs']==[]
 for n,h in c['sources'].items():assert sha(ROOT/n)==h,n
 out.mkdir();result=dict(passed=True,original_sha256=ORIGINAL,cases=rows,component=dict(report=bind(a.component),checks=c['checks'],binary_sha256=c['binary_sha256'],segments=c['segments']),
  sources={n:sha(ROOT/n) for n in ['standalone/record_viewer_external.py','standalone/build_path_session.py']},
  scope=__doc__+' Original runtime uses copied private PRM and unmodified original only; source component build has no original inputs. Parameters are opaque48-character text, not a filename-only field. Configured command is64 characters plus NUL at PRM035Dh. Full serviced parent external frontend/handoff, lifecycle errors and physical acceptance remain unimplemented/unverified.')
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS seven original command-tail/UI cases and36147 source-only DOS checks')
if __name__=='__main__':main()
