"""Build and verify a passive inner PROGRAM screen/cursor witness."""
import json,re,struct,subprocess
from pathlib import Path
from build_path_session import ROOT,sha

def symbols(path):
    return {n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',path.read_text(),re.M|re.I)}

def build(parent,runner,out,irq):
    p=symbols(parent.with_name('terminal.map'));c=symbols(runner.with_name('ASPECT.map'))
    assert p['uart_receive_interrupt'][1]!=c['uart_receive_interrupt'][1],'Observer needs distinct IRQ entry offsets'
    values=dict(IRQ_VECTOR=(irq+8)*4,PARENT_ISR_SEG=p['uart_receive_interrupt'][0],
        PARENT_ISR_OFFSET=p['uart_receive_interrupt'][1],PARENT_RENDER_SEG=p['render_child_ds'][0],
        PARENT_CHILD_DS=p['render_child_ds'][1],CHILD_ISR_SEG=c['uart_receive_interrupt'][0],
        CHILD_ISR_OFFSET=c['uart_receive_interrupt'][1],CHILD_DATA_SEG=c['_runtime_error'][0])
    source=ROOT/'standalone/snapshot_screen_watch.asm'
    subprocess.run(['nasm','-fbin',*[f'-D{k}={v}' for k,v in values.items()],str(source),'-o',str(out)],check=True)
    return {str(source.relative_to(ROOT)):sha(source),'standalone/snapshot_screen_watch.py':sha(Path(__file__))}

def verify(path):
    raw=path.read_bytes();assert len(raw)==8+4*4016
    magic,version,count,segment=struct.unpack_from('<4H',raw)
    assert magic==0x5357 and version==1 and count==4 and segment>=0xa000
    names=['sequence','mode','columns','rows','font_height','cursor','cursor_shape','page']
    frames=[];pairs=[]
    for i in range(4):
        record=raw[8+i*4016:8+(i+1)*4016];fields=dict(zip(names,struct.unpack_from('<8H',record)))
        assert fields['sequence']==i and fields['mode']in(3,7) and fields['columns']==80 and fields['rows']==25 and fields['page']==0
        frames.append(record);pairs.append(fields)
    assert frames[0][2:]==frames[1][2:] and frames[2][2:]==frames[3][2:],'Inner screen/BIOS state differs'
    return dict(passed=True,resident_segment=segment,captures=pairs,identical_inner_screen_bytes=8000,
        raw_sha256=sha(path),scope='Two inner pre/post PROGRAM pairs, each4000 screen bytes plus BIOS mode/geometry/cursor/shape/page, captured on owned file-open requests before outer ASPECT return. No injected replies or drawing.')
