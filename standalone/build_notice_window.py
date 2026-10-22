#!/usr/bin/env python3
"""Build recovered window algorithms and reused display helpers from source."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/notice-window'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    OUT.mkdir(parents=True,exist_ok=True);include='-I'+str(ROOT/'reconstruction/uart')+'/'
    p=ROOT/'reconstruction/notice_window/provenance.json';proof=json.loads(p.read_text());units=[dict(u,name=Path(u['file']).stem,define='NOTICE_WINDOW_OMF') for u in proof['units']];sources=[Path(__file__),p,ROOT/'reconstruction/uart/encodings.inc']
    for group,names in [('program_display',['snapshot','restore','snow_enable','snow_disable']),('program_ui',['cursor','fill','scroll','cell_offset','snow_cell']),('ui_windows',['read_byte'])]:
        path=ROOT/'reconstruction'/group/'provenance.json';data=json.loads(path.read_text());sources.append(path)
        for u in data['units']:
            if Path(u['file']).stem in names:units.append(dict(u,name=group+'-'+Path(u['file']).stem,define='UI_WINDOWS_OMF' if group=='ui_windows' else 'PROGRAM_DISPLAY_OMF'))
    products={}
    for u in units:
        path=ROOT/u['file'];sources.append(path);binary=OUT/(u['name']+'.bin')
        subprocess.run(['nasm','-fbin',include,str(path),'-o',str(binary)],check=True);assert sha(binary)==u['sha256']
        subprocess.run(['nasm','-fobj',include,'-D'+u['define'],str(path),'-o',str(OUT/(u['name']+'.obj'))],check=True)
        products[binary.name]=sha(binary)
    binding=ROOT/'src/ui/notice_window_native.asm';sources.append(binding)
    subprocess.run(['nasm','-fobj',str(binding),'-o',str(OUT/'binding.obj')],check=True)
    owner=ROOT/'src/ui/notice_window.c';host=ROOT/'standalone/notice_window_diagnostic.c'
    sources += [owner,host,ROOT/'src/ui/notice_window.h']
    objects=[str(OUT/(u['name']+'.obj')) for u in units]+[str(OUT/'binding.obj')]
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192','-dNOTICE_WINDOW_DIAGNOSTIC','-i='+str(ROOT/'src/ui'),'-fm=WINDOW.map','-fe=WINDOW.EXE',str(owner),str(host),*objects],cwd=OUT,check=True)
    products['WINDOW.EXE']=sha(OUT/'WINDOW.EXE')
    subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-i='+str(ROOT/'src/ui'),'-fo='+str(OUT/'owner-normal.obj'),str(owner)],cwd=OUT,check=True)
    m=dict(original_inputs=[],owner_normal_compiled=True,recovered_bytes=sum(u['bytes'] for u in proof['units']),reused_bytes=sum(u['bytes'] for u in units[len(proof['units']):]),units=units,products=products,sources={str(path.relative_to(ROOT)):sha(path) for path in sources})
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');print(json.dumps(dict(recovered_bytes=m['recovered_bytes'],reused_bytes=m['reused_bytes'],units=len(units))))
if __name__=='__main__':main()
