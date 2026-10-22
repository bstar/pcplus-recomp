#!/usr/bin/env python3
"""Build native notice controller and reused clock/string without original inputs."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/program-notice'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    OUT.mkdir(parents=True,exist_ok=True);include='-I'+str(ROOT/'reconstruction/uart')+'/'
    proof=ROOT/'reconstruction/program_notice/provenance.json';p=json.loads(proof.read_text())
    sources=[Path(__file__),proof,ROOT/'reconstruction/uart/encodings.inc'];products={}
    units=[('core','reconstruction/program_notice/core.asm','PROGRAM_NOTICE_OMF',{},p['sha256']),('strlen','reconstruction/program_exec/strlen.asm','PROGRAM_EXEC_OMF',{},'feaf2f2cbbdb93b3dcb85e3c8584eaf239cb48d619549f99e746423641c62a9d'),('seconds','reconstruction/transfer_uart/clock.asm','TRANSFER_UART_OMF',{'TRANSFER_UART_REGION':'0'},'5291a203c0c84b71b85b0a50febcd985e2070c672d8ba557d95e652b87140d74'),('clock','reconstruction/transfer_uart/clock.asm',None,{'TRANSFER_UART_REGION':'1'},'c677c642aab995664be684bbcd61ded5f3be8491c1d7a89e8167fb50b53680d0')]
    for name,path,define,flags,digest in units:
        source=ROOT/path;sources.append(source);binary=OUT/(name+'.bin')
        subprocess.run(['nasm','-fbin',include,*['-D'+k+'='+v for k,v in flags.items()],str(source),'-o',str(binary)],check=True);assert sha(binary)==digest
        products[binary.name]=digest
        if define:subprocess.run(['nasm','-fobj',include,'-D'+define,str(source),'-o',str(OUT/(name+'.obj'))],check=True)
    host=ROOT/'standalone/program_notice_diagnostic.asm';sources.append(host)
    subprocess.run(['nasm','-fobj',str(host),'-o',str(OUT/'host.obj')],check=True)
    subprocess.run(['wlink','system','dos','option','quiet','option','map='+str(OUT/'NOTICE.map'),'name',str(OUT/'NOTICE.EXE'),'file',','.join(str(OUT/(name+'.obj')) for name in ('host','core','strlen','seconds'))],check=True)
    products['NOTICE.EXE']=sha(OUT/'NOTICE.EXE')
    report=dict(original_inputs=[],recovered_bytes=190,reused_bytes=71,products=products,sources={str(p.relative_to(ROOT)):sha(p) for p in sources})
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('Built exact notice controller:190 recovered +71 reused bytes')
if __name__=='__main__':main()
