#!/usr/bin/env python3
"""Link actual DOS C APIs into an assembly-owned DS=SS executable."""
from pathlib import Path
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/config-abi';OUT.mkdir(parents=True,exist_ok=True)
sources=[ROOT/'src/config'/name for name in ['prm_dos.c','prm_replace.c','prm_replace_fs.c']];objects=[]
for source in sources:
 obj=OUT/(source.stem+'.obj');objects.append(obj)
 subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-s','-w4','-we','-i='+str(ROOT/'src/config'),'-fo='+str(obj),str(source)],check=True,cwd=OUT)
host=ROOT/'standalone/config_abi_host.asm';obj=OUT/'host.obj';objects.insert(0,obj)
subprocess.run(['nasm','-f','obj',str(host),'-o',str(obj)],check=True)
subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'config_abi.map'),'name',str(OUT/'ABI.EXE'),'file',','.join(map(str,objects)),'library',str(Path(os.environ['WATCOM'])/'lib286/dos/clibs.lib')],check=True)
sources += [host]+list((ROOT/'src/config').glob('*.h'))
manifest={'kind':'assembly-startup-to-actual-DOS-C-config-ABI','binary_sha256':hashlib.sha256((OUT/'ABI.EXE').read_bytes()).hexdigest(),'sources':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'scope':'Actual unsigned16 AX returns, near-cdecl argument order/cleanup, DS=SS, 8KiB stack, no C startup. Only DOS-handle/string backend subset, not a complete C runtime initialization contract.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('Built ABI.EXE',manifest['binary_sha256'])
