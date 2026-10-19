#!/usr/bin/env python3
"""Link native file handlers to real owned DOS stdio, with test operand boundaries."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/aspect-script-file-backend'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True);objects=[]
 assembly=[('commands','src/aspect/script_file_commands.asm',None),('services','src/aspect/script_file_services.asm',None),('bridge','src/aspect/script_file_bridge.asm',None),('fixture','standalone/script_file_fixture.asm',None),('strcpy','reconstruction/program_exec/strcpy.asm','PROGRAM_EXEC_OMF'),('strlen','reconstruction/program_exec/strlen.asm','PROGRAM_EXEC_OMF')]
 sources=[ROOT/'src/aspect/script_file_runtime.c',ROOT/'src/aspect/script_file_runtime.h',ROOT/'src/aspect/runtime.h',ROOT/'standalone/script_file_fixture.c',ROOT/'standalone/compiler_heap_snapshot.c',ROOT/'standalone/compiler_heap_snapshot.h',ROOT/'reconstruction/uart/encodings.inc',Path(__file__)]
 for name,rel,define in assembly:
  obj=OUT/(name+'.obj');sources.append(ROOT/rel)
  subprocess.run(['nasm','-fobj','-Ireconstruction/uart/',*(['-D'+define] if define else []),rel,'-o',str(obj)],cwd=ROOT,check=True);objects.append(str(obj))
 subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-i='+str(ROOT/'src/aspect'),'-i='+str(ROOT/'standalone'),'-fm=SCRIPTIO.map','-fe=SCRIPTIO.EXE',str(ROOT/'standalone/script_file_fixture.c'),str(ROOT/'src/aspect/script_file_runtime.c'),str(ROOT/'standalone/compiler_heap_snapshot.c'),*objects],cwd=OUT,check=True)
 report=dict(binary_sha256=sha(OUT/'SCRIPTIO.EXE'),sources={str(p.relative_to(ROOT)):sha(p) for p in sources},original_inputs=[],scope='Actual recovered13 file handlers/3helpers and owned DOS stdio; declared test operand/writeback/warning/lowercase boundaries. Real file operations and native prefix effects; not yet full VM/compiler integration.')
 (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('Built native script-file DOS backend',report['binary_sha256'])
if __name__=='__main__':main()
