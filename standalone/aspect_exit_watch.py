"""Passive DOS exit telemetry for the exact attached ASPECT lease."""
import re,struct,subprocess
from pathlib import Path
from build_path_session import ROOT,sha

FIELDS=['exit','ds','ss','error','opcode','raw_status','cleanup_error','external_calls',
        'external_scope','display_owned','program_busy','process_busy','header']

def symbols(path):
    return {n:(int(s,16),int(o,16)) for s,o,n in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',path.read_text(),re.M|re.I)}

def build(parent,runner,out):
    p=symbols(parent.with_name('terminal.map'));c=symbols(runner.with_name('ASPECT.map'))
    fields=dict(CHILD_ERROR='_runtime_error',CHILD_OPCODE='_runtime_last_opcode',
        CHILD_RAW='_runtime_external_raw_status',CHILD_CLEANUP='_runtime_external_cleanup_error',
        CHILD_CALLS='_runtime_external_calls',CHILD_SCOPE='_runtime_external_scope_storage',
        CHILD_DISPLAY='_native_display_owned',CHILD_BUSY='_native_program_busy',
        CHILD_PROCESS='_native_process_busy',CHILD_HEADER='_runtime_header')
    assert all(c[n][0]==c['_runtime_error'][0] for n in fields.values())
    values={name:c[symbol][1] for name,symbol in fields.items()}
    values.update(PARENT_DATA_SEG=p['terminal_program_kind'][0],
        PARENT_RENDER_SEG=p['render_child_ds'][0],PARENT_CHILD_DS=p['render_child_ds'][1])
    source=ROOT/'standalone/aspect_exit_watch.asm'
    subprocess.run(['nasm','-fbin',*[f'-D{k}={v}' for k,v in values.items()],str(source),'-o',str(out)],check=True)
    return {str(source.relative_to(ROOT)):sha(source),'standalone/aspect_exit_watch.py':sha(Path(__file__))}

def read(path):
    raw=path.read_bytes();assert len(raw)==218
    magic,version,count,launches,segment=struct.unpack_from('<5H',raw)
    assert magic==0xae51 and version==2 and count<=8
    return dict(launches=launches,resident_segment=segment,exits=[dict(zip(FIELDS,struct.unpack_from('<13H',raw,10+i*26))) for i in range(count)])
