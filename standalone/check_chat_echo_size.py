#!/usr/bin/env python3
"""Verify Chat echo memory recovery; runtime ASPECT acceptance remains separate."""
import argparse,json,re
from pathlib import Path
from build_path_session import ROOT,sha,object_segments
from terminal_memory import inspect_terminal_memory


def counts(path):
    rows=object_segments(path)
    return [sum(s['bytes'] for s in rows.values() if s['class'] in ('CODE','FARCODE')),
            sum(s['bytes'] for s in rows.values() if s['class'] not in ('CODE','FARCODE'))]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('terminal','control','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--require-baseline',action='store_true',help='Require the compact-label image to fit the479408-byte foreground baseline')
    a=p.parse_args();binary=a.terminal.resolve();control=a.control.resolve();out=a.output.resolve()
    assert all(q.is_relative_to(ROOT/'build') for q in (binary,control,out)) and not out.exists()
    m=json.loads(binary.with_name('manifest.json').read_text());assert m['experimental_chat_echo'] and sha(binary)==m['binary_sha256']
    assert sha(control)=='977d1f552fb214a464e79f640eff43f14eae02d0c10dede41d5b09d47969f70c'
    profile=json.loads((ROOT/'src/chat/echo_size.json').read_text());rows=[]
    for name,e in profile['sources'].items():
        assert sha(ROOT/name)==e['source_sha256']
        assert m['optimized_c_sources'][name]==profile['compiler_options'][e['profile']]
        leaf=Path(name).stem+'.obj';before=counts(control.parent/leaf);after=counts(binary.parent/leaf)
        assert before==e['control_code_data_bytes'] and after==e['optimized_code_data_bytes'],(name,before,after)
        assert before[1]==after[1] and after[0]<before[0]
        rows.append(dict(source=name,control=before,current=after))
    live=inspect_terminal_memory(binary,binary.with_name('terminal.map'));old=inspect_terminal_memory(control,control.with_name('terminal.map'))
    capacities=('near_bytes','far_bytes','history_bytes','native_reset_private_stack_bytes',
        'native_reset_shadow_bytes','native_reset_workspace_bytes','snapshot_bytes',
        'far_ui_storage_bytes','redisplay_snapshot_bytes','redisplay_row_index_bytes')
    assert all(live[n]==old[n] for n in capacities)
    for q in (binary,control):
        stack=re.search(r'^STACK\s+STACK\s+DGROUP\s+\S+\s+([0-9a-f]+)',q.with_name('terminal.map').read_text(),re.M|re.I)
        assert stack and int(stack[1],16)==8192
    assert live['minimum_allocated_module_bytes']<old['minimum_allocated_module_bytes']
    if a.require_baseline:
        assert m['experimental_code_label_offsets']
        assert live['minimum_allocated_module_bytes']<=479408
    assert sha(binary.parent/'PCCHAT.OVL')==sha(control.parent/'PCCHAT.OVL')
    sources={n:sha(ROOT/n) for n in ('standalone/check_chat_echo_size.py','standalone/build_path_session.py','standalone/terminal_memory.py','src/chat/echo_size.json','src/chat/echo_owner.asm')}
    out.mkdir();(out/'result.json').write_text(json.dumps(dict(passed=True,binary_sha256=sha(binary),control_sha256=sha(control),
        compiled_sources=rows,object_code_saving_bytes=sum(r['control'][0]-r['current'][0] for r in rows),
        minimum_bytes=live['minimum_allocated_module_bytes'],control_minimum_bytes=old['minimum_allocated_module_bytes'],
        allocation_saving_bytes=old['minimum_allocated_module_bytes']-live['minimum_allocated_module_bytes'],
        capacities_unchanged={n:live[n] for n in capacities},stack_bytes=8192,module_unchanged=True,
        allocation_budget_met=live['minimum_allocated_module_bytes']<=479408,
        complete_memory_funding=False,sources=sources,
        scope=__doc__+' Historical control is bound to its exact executable and object counts, not reclassified as current producer source. Current C source hashes and both object code/data sizes checked; allocation/stack/capacities inspected. No ASPECT, BBS, foreground TEXT or physical acceptance.'),indent=2)+'\n')
    print('PASS memory recovery:',old['minimum_allocated_module_bytes']-live['minimum_allocated_module_bytes'],'allocation bytes;',len(rows),'measured C choices, capacities unchanged; baseline required',a.require_baseline)


if __name__=='__main__':main()
