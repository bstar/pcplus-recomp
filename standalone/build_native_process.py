#!/usr/bin/env python3
"""Build the native DOS process layer without original artifacts or trap stubs."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/native-process'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    proof=json.loads((ROOT/'reconstruction/program_exec/provenance.json').read_text())
    names=['environment_tail','spawn_extension','exec','scratch','get_ds','getenv',
           'strcpy','strlen','strchr','strncmp','error_exec','map_error','error_lookup',
           'spawnv','spawn_search','system','access','error_access','strrchr',
           'strcmpi','strcat','path_component']
    include='-I'+str(ROOT/'reconstruction/uart')+'/'
    objects=[];units=[];sources=[]
    for name in names:
        p=ROOT/'reconstruction/program_exec'/ (name+'.asm');sources.append(p)
        unit=next(u for u in proof['units'] if u['file']==str(p.relative_to(ROOT)))
        binary=OUT/(name+'.bin')
        subprocess.run(['nasm','-fbin',include,str(p),'-o',str(binary)],check=True)
        assert sha(binary)==unit['sha256'] and binary.stat().st_size==unit['bytes']
        units.append(unit)
        obj=OUT/(name+'.obj');objects.append(str(obj))
        renames=[]
        if name=='spawn_extension':renames=['-Dprogram_spawn_extension=native_spawn_extension_recovered']
        if name=='access':renames=['-Dprogram_access=native_access_recovered']
        subprocess.run(['nasm','-fobj',include,'-DPROGRAM_EXEC_OMF',*renames,
            '-Dprogram_fallback_environment=_runtime_arena',
            '-Dprogram_environ=_native_environment',str(p),'-o',str(obj)],check=True)
    for name in ['src/process/native_process_state.asm']:
        p=ROOT/name;sources.append(p);obj=OUT/(p.stem+'.obj');objects.append(str(obj))
        subprocess.run(['nasm','-fobj','-DNATIVE_PROCESS_DIAGNOSTIC',str(p),'-o',str(obj)],check=True)
    c_sources=[ROOT/'src/process/native_process.c',ROOT/'standalone/native_process_diagnostic.c']
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',
        '-DNATIVE_PROCESS_DIAGNOSTIC','-i='+str(ROOT/'src/process'),
        '-fm=NATIVE.map','-fe=NATIVE.EXE',*[str(p) for p in c_sources],*objects],cwd=OUT,check=True)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',
        '-DNATIVE_PROCESS_DIAGNOSTIC','-DNATIVE_NAMESPACE','-i='+str(ROOT/'src/process'),
        '-i='+str(ROOT/'standalone'),'-fm=NAMES.map','-fe=NAMES.EXE',
        *[str(p) for p in c_sources],*objects],cwd=OUT,check=True)
    child=ROOT/'standalone/native_process_child.asm';sources+=c_sources+[child,Path(__file__),ROOT/'src/process/native_process.h',ROOT/'reconstruction/program_exec/provenance.json',ROOT/'reconstruction/uart/encodings.inc']
    children={}
    sources.append(ROOT/'standalone/native_namespace_cases.inc')
    for name,define in [('CHILD',None),('DIVIDE','CHILD_DIVIDE'),('VECT','CHILD_VECTORS'),('RESIDENT','CHILD_TSR'),('EMPTY','CHILD_EMPTY'),('FLAGS','CHILD_FLAGS')]:
        path=OUT/(name+'.COM')
        subprocess.run(['nasm','-fbin',*(['-D'+define] if define else []),str(child),'-o',str(path)],check=True)
        children[path.name]=sha(path)
    for code in (17,21,22):
        path=OUT/f'E{code}.COM'
        subprocess.run(['nasm','-fbin','-DCHILD_EXIT='+str(code),str(child),'-o',str(path)],check=True)
        children[path.name]=sha(path)
    exe=ROOT/'standalone/native_process_exe_child.c';sources.append(exe)
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k2048',
        '-fe=CHILD.EXE',str(exe)],cwd=OUT,check=True)
    children['CHILD.EXE']=sha(OUT/'CHILD.EXE')
    report=dict(passed=True,original_inputs=[],native_bytes=sum(u['bytes'] for u in units),units=units,
        executable_sha256=sha(OUT/'NATIVE.EXE'),namespace_sha256=sha(OUT/'NAMES.EXE'),children=children,
        sources={str(p.relative_to(ROOT)):sha(p) for p in sources},
        scope='Real native environment/tail/EXEC with maintained CRT bindings. Diagnostic only; no runtime publication or UI/UART controller.')
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Built native process layer:',report['native_bytes'],'exact bytes; real heap bindings, no trap stubs.')


if __name__=='__main__':main()
