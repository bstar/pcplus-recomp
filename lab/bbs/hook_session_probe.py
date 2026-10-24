"""Source-owned helper preparation and raw return checks for live BBS probes."""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'standalone'))
from test_hook_apply_dos import FIELDS
from test_directory_key_bindings_dos import actions


def prepare(stage,terminal,mode):
    manifest=json.loads((terminal.parent/'manifest.json').read_text())
    assert manifest['experimental_hook_apply']
    symbols={name:(int(seg,16),int(off,16)) for seg,off,name in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',
        (terminal.parent/'terminal.map').read_text(),re.M|re.I)}
    (stage/'parent_layout.h').write_text('static const struct {unsigned segment,offset,bytes;} parent_spans[]={\n'+
        ''.join('{%d,%d,%d},\n'%(*symbols[name],size) for name,size in FIELDS)+'};\n')
    subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we','-k8192',*(['-dHOOK_CUSTOM_IRQ']if manifest.get('experimental_custom_irq')else[]),'-i='+str(stage),
        '-fm=APPLYCH.map','-fe=APPLYCH.EXE',str(ROOT/'standalone/hook_apply_child.c'),
        str(terminal.parent/'hook_exchange.obj')],cwd=stage,check=True)
    (stage/'MODE.BIN').write_bytes(struct.pack('<H',0 if mode=='accept' else 1))
    (stage/'ACTIONS.KEY').write_bytes(actions(b'APPLYCH.EXE',2))
    return [Path(__file__),ROOT/'standalone/hook_apply_child.c',
        ROOT/'standalone/test_hook_apply_dos.py',ROOT/'standalone/test_directory_key_bindings_dos.py']


def schedule(keys):
    delay,rest=keys.split(' ',1)
    assert delay in ('p25000','p33000')
    # The directory script has returned after authentication. No acknowledgement
    # keys are supplied: all three online helpers must resume without a prompt.
    return delay+' a-1 p1200 a-1 p1200 a-1 p1200 '+rest


def inspect(stage,mode):
    assert (stage/'COUNT.BIN').read_bytes()==struct.pack('<H',3)
    snapshots=[]
    for index in range(3):
        raw=(stage/f'S{index}.BIN').read_bytes();assert len(raw)==sum(size for _,size in FIELDS)
        offset=0;fields={}
        for name,size in FIELDS:fields[name]=raw[offset:offset+size];offset+=size
        snapshots.append(fields)
    before=[(stage/f'B{i}.BIN').read_bytes() for i in range(3)]
    after=[(stage/f'A{i}.BIN').read_bytes() for i in range(3)]
    assert all(len(frame)==2094 for frame in before+after)
    accepted=mode=='accept'
    assert before[1]==(after[0] if accepted else before[0])
    assert before[2]==after[1]==before[1]
    initial=struct.unpack_from('<H',snapshots[0]['_terminal_register_owner'],4)[0]
    assert initial==1,'Directory ASPECT must have committed before the first helper'
    for index in (1,2):
        fields=snapshots[index];owner=fields['_terminal_register_owner']
        assert struct.unpack_from('<H',owner)[0]==0 and owner[904:]==before[index][:830]
        assert struct.unpack_from('<H',owner,4)[0]==initial+index-(not accepted)
        baseline=fields['terminal_baseline_storage']
        if index==1 and not accepted:assert baseline==snapshots[0]['terminal_baseline_storage']
        else:assert struct.unpack_from('<H',baseline,4)[0]==3 and baseline[8:]==before[index][830:]
        assert struct.unpack('<H',fields['_terminal_hook_completed_status'])[0]==(107 if index==1 and not accepted else 0)
        if accepted or index==2:
            # The second child makes no changes; a rejected first offer must
            # therefore retain the original active configuration throughout.
            expected=after[0] if accepted else before[0]
            assert before[index]==expected
    for index in range(3):
        raw=(stage/f'H{index}.BIN').read_bytes();assert len(raw) in (26,34)
        h=struct.unpack('<17H' if len(raw)==34 else '<13H',raw)
        irq=struct.unpack_from('<H',snapshots[index]['terminal_configuration_values'],34)[0]
        assert irq in (3,4,5,7)
        assert h[4]==6 and h[5]==3 and h[7]==0 and not h[6]&2 and h[8]&(1<<irq)
        at={3:11,4:9,5:13,7:15}[irq]
        assert h[at:at+2]==tuple(struct.unpack('<H',snapshots[index][n])[0]for n in ('uart_previous_irq_offset','uart_previous_irq_segment'))
    result=dict(passed=True,mode=mode,helper_calls=3,initial_register_epoch=initial,
        first_return_accepted=accepted,second_return_accepted=True,
        third_child_exit=23,scope='Raw snapshots prove first return adoption/rejection and second return adoption. '
        'Third child deliberately fails; subsequent live editor evidence is separate. '
        'No post-third register snapshot or physical timing claim.',
        artifacts={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in stage.iterdir()
            if re.fullmatch(r'[SBAH][0-2]\.BIN|COUNT\.BIN|MODE\.BIN|ACTIONS\.KEY|APPLYCH\.EXE|parent_layout\.h',p.name)})
    (stage/'hook-checks.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
