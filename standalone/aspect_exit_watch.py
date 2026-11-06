"""Passive DOS exit telemetry for the exact attached ASPECT lease."""
import re,struct,subprocess
from pathlib import Path
from build_path_session import ROOT,sha

FIELDS=['exit','ds','ss','error','opcode','raw_status','cleanup_error','external_calls',
        'external_scope','display_owned','program_busy','process_busy','header']

def symbols(path):
    return {n:(int(s,16),int(o,16)) for s,o,n in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',path.read_text(),re.M|re.I)}

def build(parent,runner,out,wait=False):
    p=symbols(parent.with_name('terminal.map'));c=symbols(runner.with_name('ASPECT.map'))
    fields=dict(CHILD_ERROR='_runtime_error',CHILD_OPCODE='_runtime_last_opcode',
        CHILD_RAW='_runtime_external_raw_status',CHILD_CLEANUP='_runtime_external_cleanup_error',
        CHILD_CALLS='_runtime_external_calls',CHILD_SCOPE='_runtime_external_scope_storage',
        CHILD_DISPLAY='_native_display_owned',CHILD_BUSY='_native_program_busy',
        CHILD_PROCESS='_native_process_busy',CHILD_HEADER='_runtime_header',
        CHILD_NEAR='_native_near_calls',CHILD_FAR='_native_far_calls',
        CHILD_BACKUP='_native_backup_extent',CHILD_ERRNO='_native_crt_error',CHILD_DOSERR='_native_dos_error')
    assert all(c[n][0]==c['_runtime_error'][0] for n in fields.values())
    values={name:c[symbol][1] for name,symbol in fields.items()}
    values.update(PARENT_DATA_SEG=p['terminal_program_kind'][0],
        PARENT_RENDER_SEG=p['render_child_ds'][0],PARENT_CHILD_DS=p['render_child_ds'][1])
    if wait:
        values.update(WAIT_WATCH=1,PARENT_PROGRAM=p['render_program_owned'][1],
            PARENT_SNAPSHOT=p['render_snapshot_owned'][1],
            CHILD_WAITING=c['_native_program_waiting'][1],
            CHILD_SERIAL=c['_aspect_serial_active'][1],
            CHILD_DETACHED=c['_aspect_process_serial_detached'][1])
        assert all(c[n][0]==c['_runtime_error'][0] for n in
                   ['_native_program_waiting','_aspect_serial_active','_aspect_process_serial_detached'])
    if '_runtime_external_result_probe' in c:
        assert c['_runtime_external_result_probe'][0]==c['_runtime_error'][0]
        values['CHILD_RESULT']=c['_runtime_external_result_probe'][1]
    source=ROOT/'standalone/aspect_exit_watch.asm'
    subprocess.run(['nasm','-fbin',*[f'-D{k}={v}' for k,v in values.items()],str(source),'-o',str(out)],check=True)
    return {str(source.relative_to(ROOT)):sha(source),'standalone/aspect_exit_watch.py':sha(Path(__file__))}

def read_wait(path):
    raw=path.read_bytes();assert len(raw)==6+8*20
    magic,version,count=struct.unpack_from('<3H',raw)
    assert magic==0x5716 and version==1 and count<=8
    fields=['ds','ss','parent_program','parent_snapshot','waiting','display_owned',
            'program_busy','serial_active','serial_detached','key']
    return [dict(zip(fields,struct.unpack_from('<10H',raw,6+i*20))) for i in range(count)]

def read(path):
    raw=path.read_bytes();assert len(raw) in (218,352,576,708)
    magic,version,count,launches,segment=struct.unpack_from('<5H',raw)
    assert magic==0xae51 and version==2 and count<=8
    result=dict(launches=launches,resident_segment=segment,exits=[dict(zip(FIELDS,struct.unpack_from('<13H',raw,10+i*26))) for i in range(count)])
    if len(raw)>218:
        magic,version,count=struct.unpack_from('<3H',raw,218)
        assert magic==0xa148 and version in (1,2) and count<=16
        names=['paragraphs','ax','bx','carry']
        if version==2:names+=['near_calls','far_calls','backup_extent','display_owned','process_busy','native_errno','native_dos_error']
        assert len(raw)==224+16*len(names)*2+(132 if len(raw)==708 else 0)
        result['allocations']=[dict(zip(names,struct.unpack_from('<'+str(len(names))+'H',raw,224+i*len(names)*2))) for i in range(count)]
    if len(raw)==708:
        assert struct.unpack_from('<2H',raw,576)==(0xb008,1)
        names=['stage','status','display_status','serial_status','process_status','crt_error','dos_error','child_status']
        result['program_results']=[dict(zip(names,struct.unpack_from('<8H',raw,580+i*16))) for i in range(len(result['exits']))]
    return result
