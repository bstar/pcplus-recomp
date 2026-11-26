#!/usr/bin/env python3
"""Build the BBS hardware candidate package, or its known-good control, in one command.

Every product is rebuilt from the working tree into OUTPUT/work and staged
with package_connection_test.py into OUTPUT/package. No original executable,
install or private configuration is read.

--control rebuilds the qualified capability27 package
(docs/validation/aspect-screen-package.json) and fails unless all 17 staged
files match it byte for byte. The default adds the BBS terminal opt-ins
(--ansi-profiles --dec-graphics --bbs-csi --vt52) to the same parent and the
matching --ansi-profiles settings editor, and stages it for a separate DOS
directory (default C:\\PCPLUSBB) so the known-good install stays the fallback.
See docs/BBS_HARDWARE_CANDIDATE.md.

Run inside the pinned toolchain:
  ./tools/dev --command python3 standalone/build_bbs_candidate.py --output build/<new>
"""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RECIPE=json.loads((ROOT/'standalone/keymap_connection_candidate_recipe.json').read_text())
QUALIFIED=ROOT/'docs/validation/aspect-screen-package.json'
# Parent flags of the qualified screen-parent-v6 (tools/rebuild-asio-checkpoint.py).
PARENT=[*RECIPE['terminal_flags'],'--aspect-get-display','--aspect-get-policy','--compiler-lease-bridge',
 '--aspect-terminal-query','--aspect-hitkey','--aspect-state-builtins','--aspect-screen-commands','--chat-send-mode']
BBS_OPT_INS=['--ansi-profiles','--dec-graphics','--bbs-csi','--vt52']
SETUP=['--custom-irq','--chat-mode','--mouse','--notice-sound']
# screen-child-base-v4 / screen-child-overlay-v4 recipe.
CHILD=dict(parent_render=True,notice_bank=True,notice_sound=True,notice_input=True,notice_help=True,
 help_resource=True,serial_bank=True,register_handoff=True,custom_irq=True,get_display=True,
 get_policy=True,get_vm=True,near_globals=True,compiler_parent_lease=True,overlay_ready=True,
 directory_baud=True,directory_fields=True,directory_proto=True,clock_builtins=True,
 terminal_builtins=True,aspect_hitkey=True,aspect_state_builtins=True,aspect_screen_commands=True,
 **RECIPE['aspect_options'],heap_growth_bytes=256,disk_script_snapshots=True,defer_help_resource=True,
 early_help_model=True,help_parent_snapshot=True)
OVERLAY=['--notice','--program','--screen','--checked-io']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
 p.add_argument('--output',type=Path,required=True,help='New directory under build/')
 p.add_argument('--control',action='store_true',help='Rebuild the qualified package and require an exact match')
 p.add_argument('--dos-directory',help='DOS root directory (default PCPLUSBB, or PCPLUS with --control)')
 p.add_argument('--source-base-commit',help='Recorded source identity (default: git HEAD; --control: the qualified receipt)')
 a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 qualified=json.loads(QUALIFIED.read_text())
 dos=a.dos_directory or ('PCPLUS' if a.control else 'PCPLUSBB')
 base=a.source_base_commit or (qualified['source_base_commit'] if a.control else None)
 work=out/'work';work.mkdir(parents=True);log=out/'build.log'
 def run(*args):
  with log.open('a') as h:
   h.write('\n$ '+' '.join(map(str,args))+'\n');h.flush()
   subprocess.run([sys.executable,*map(str,args)],cwd=ROOT,stdout=h,stderr=h,check=True)
 run('standalone/build_terminal.py',*PARENT,*([] if a.control else BBS_OPT_INS),'--output-dir',work/'terminal')
 run('standalone/build_parent_help_companions.py','--parent',work/'terminal')
 run('-c','import sys;from pathlib import Path;sys.path.insert(0,"standalone");from build_aspect_process import main;main(output=Path(%r),**%r)'%(str(work/'child-base'),CHILD))
 run('standalone/build_aspect_standard_overlay.py','--base',work/'child-base','--output',work/'child',*OVERLAY)
 run('standalone/build_aspect_compiler_dos.py','--get','--output',work/'compiler')
 run('standalone/build_setup.py',*SETUP,*([] if a.control else ['--ansi-profiles']),'--output-dir',work/'setup')
 run('standalone/build_xlt_editor.py','--output-dir',work/'xlt')
 run('standalone/build_keymap_helper.py','--output',work/'keymap')
 stage=['standalone/package_connection_test.py','--output',out/'package','--dos-directory',dos,
  '--terminal',work/'terminal/TERMINAL.EXE','--runner',work/'child/ASPECT.EXE','--compiler',work/'compiler/ASPCOMP.EXE',
  '--setup',work/'setup/PRMEDIT.EXE','--translation',work/'xlt/XLTEDIT.EXE','--keymap-helper',work/'keymap/PCKEYMAP.EXE']
 run(*stage,*(['--source-base-commit',base] if base else []))
 files=json.loads((out/'package/manifest.json').read_text())['files']
 different=sorted(n for n in set(files)|set(qualified['files']) if files.get(n)!=qualified['files'].get(n))
 result=dict(control=a.control,dos_directory=dos,files=files,differs_from_qualified=different,original_inputs=[],
  terminal_flags=PARENT+([] if a.control else BBS_OPT_INS),setup_flags=SETUP+([] if a.control else ['--ansi-profiles']))
 if a.control:
  assert not different,'Known-good package does not reproduce: '+', '.join(different)
  result['qualified_package_reproduced']=True
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(f'PASS control: all {len(files)} files match the qualified package' if a.control else
  'Staged candidate for C:\\'+dos+'; differs from qualified in: '+', '.join(different))
if __name__=='__main__':main()
