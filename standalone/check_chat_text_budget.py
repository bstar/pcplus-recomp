#!/usr/bin/env python3
"""Check physical Chat TX funding against the exact preceding foreground build."""
import argparse,json,re
from pathlib import Path
from build_path_session import ROOT,sha,object_segments
from terminal_memory import inspect_terminal_memory


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('terminal','control','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();binary=a.terminal.resolve();control=a.control.resolve();out=a.output.resolve()
    assert all(q.is_relative_to(ROOT/'build') for q in (binary,control,out)) and not out.exists()
    assert sha(control)=='5875536a193a3f7db696307dfb358bc0adc1b3d3fdae44b7eeb40980d9198fef'
    m=json.loads(binary.with_name('manifest.json').read_text());assert sha(binary)==m['binary_sha256']
    assert m['experimental_chat_text_transport']
    profile=json.loads((ROOT/'src/chat/text_transport_size.json').read_text());rows=[]
    for name,entry in profile['sources'].items():
        assert sha(ROOT/name)==entry['source_sha256']
        assert m['optimized_c_sources'][name]==profile['compiler_options'][entry['profile']]
        segments=object_segments(binary.parent/(Path(name).stem+'.obj'))
        code=sum(s['bytes'] for s in segments.values() if s['class'] in ('CODE','FARCODE'))
        data=sum(s['bytes'] for s in segments.values() if s['class'] not in ('CODE','FARCODE'))
        assert [code,data]==entry['optimized_code_data_bytes'],(name,code,data)
        rows.append(dict(source=name,code_bytes=code,data_bytes=data))
    live=inspect_terminal_memory(binary,binary.with_name('terminal.map'))
    old=inspect_terminal_memory(control,control.with_name('terminal.map'))
    capacities=('near_bytes','far_bytes','history_bytes','native_reset_private_stack_bytes',
        'native_reset_shadow_bytes','native_reset_workspace_bytes','snapshot_bytes',
        'far_ui_storage_bytes','redisplay_snapshot_bytes','redisplay_row_index_bytes')
    for n in capacities:assert live[n]==old[n],n
    for q in (binary,control):
        listing=q.with_name('terminal.map').read_text()
        stack=re.search(r'^STACK\s+STACK\s+DGROUP\s+\S+\s+([0-9a-f]+)',listing,re.M|re.I)
        assert stack and int(stack[1],16)==8192
    assert live['minimum_allocated_module_bytes']<=old['minimum_allocated_module_bytes']
    same_module=sha(binary.parent/'PCCHAT.OVL')==sha(control.parent/'PCCHAT.OVL')
    if m.get('experimental_chat_timing'):
        module=m['chat_loader']['module']
        assert module['api_version']==0x103 and module['state_bytes']==448
        assert module['image_bytes']<8192 and module['DGROUP_bytes']==module['own_stack_bytes']==0
        assert sha(binary.parent/'PCCHAT.OVL')==module['binary_sha256']
    else:assert same_module
    inputs=['standalone/check_chat_text_budget.py','standalone/build_path_session.py',
            'standalone/terminal_memory.py','src/chat/text_transport_size.json']
    out.mkdir();(out/'result.json').write_text(json.dumps(dict(passed=True,
        binary_sha256=sha(binary),control_sha256=sha(control),compiled_sources=rows,
        minimum_bytes=live['minimum_allocated_module_bytes'],control_minimum_bytes=old['minimum_allocated_module_bytes'],
        module_unchanged=same_module,module_sha256=sha(binary.parent/'PCCHAT.OVL'),
        capacities_unchanged={n:live[n] for n in capacities},stack_bytes=8192,
        sources={n:sha(ROOT/n) for n in inputs},scope=__doc__+' Object counts, live MZ/map inspection, declared stack/capacities and module identity: API0103 when explicitly selected, otherwise the unchanged presentation module. Runtime and default-flag identity checks are separate.'),indent=2)+'\n')
    print('PASS three compiled size choices; capacities/stack unchanged; declared module and parent fit budget')


if __name__=='__main__':main()
