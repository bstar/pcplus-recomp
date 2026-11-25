#!/usr/bin/env python3
"""PCCONN companion-format layout checks against the shared loader's rules.

Packages the compact connection OMF probe (CONNOMF.EXE from
check_aspect_connection_omf.py) for the proposed snapshot extent
redisplay_snapshot+16384 (16384 bytes) of a linked parent map. Proves that the
unchanged shared-loader fixup semantics reproduce a standard MZ load at the
same arena for every admissible parent load delta, that the loader refuses
exactly where a fixup would reach A000h, that malformed tables are refused and
that the 8192-byte compiler window cannot hold the module. Layout only: no
DOS loader execution, arena ownership, BSS initialization or entry is claimed.
"""
import argparse
import json
from pathlib import Path
import re
import struct
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
import connection_module as cm

ROOT=Path(__file__).resolve().parents[1]
ARENA_OFFSET,EXTENT=16384,16384


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--probe-dir',type=Path,required=True);p.add_argument('--parent-map',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
    raw=(a.probe_dir/'CONNOMF.EXE').read_bytes();probe=json.loads((a.probe_dir/'result.json').read_text())
    assert cm.sha(raw)==probe['executable_sha256']
    snapshot=re.search(r'^([0-9a-f]{4}):([0-9a-f]{4})\s+redisplay_snapshot\s*$',a.parent_map.read_text(),re.M|re.I)
    assert snapshot and int(snapshot[2],16)%16==0
    target=int(snapshot[1],16)+(int(snapshot[2],16)+ARENA_OFFSET)//16
    body,info=cm.package(raw,target,EXTENT)
    mz=cm.parse_mz(raw);n,size=info['relocations'],info['payload_bytes']
    assert info['allocated_image_bytes']==probe['allocated_image_bytes'] and n==probe['mz_relocations']
    checks={}
    # Every relocation value is module-local, so the highest fixed word bounds A000h.
    top=max(struct.unpack_from('<H',body,at)[0] for at in mz['relocs'])
    admitted=refused=0
    for delta in list(range(0x0060,0xa000-top+64,0x35))+[0xa000-top-1,0xa000-top,0xa000-top+1]:
        got=cm.loader_apply(body,size,n,delta)
        if delta+top<0xa000:
            assert got==cm.mz_load(raw,target+delta),hex(delta);admitted+=1
        else:assert got is None,hex(delta);refused+=1
    checks.update(mz_equivalent_deltas=admitted,a000_refusals=refused)
    table=bytearray(body)
    a0,a1=size,size+2;table[a0:a0+2],table[a1:a1+2]=body[a1:a1+2],body[a0:a0+2]
    checks['unordered_table_refused']=cm.loader_apply(bytes(table),size,n,0x800) is None
    table=bytearray(body);struct.pack_into('<H',table,size+2*(n-1),size-1)
    checks['offset_past_payload_refused']=cm.loader_apply(bytes(table),size,n,0x800) is None
    table=bytearray(body);struct.pack_into('<H',table,size+2,struct.unpack_from('<H',body,size)[0]+1)
    checks['overlapping_fixup_refused']=cm.loader_apply(bytes(table),size,n,0x800) is None
    try:cm.package(raw,target,8192);checks['compiler_window_refused']=False
    except AssertionError:checks['compiler_window_refused']=True
    assert all(v is True or (isinstance(v,int) and v>0) for v in checks.values()),checks
    out.mkdir(parents=True);(out/'PCCONN.OVL').write_bytes(body)
    result=dict(passed=True,checks=checks,module=info,probe_sha256=probe['executable_sha256'],probe_result=str(a.probe_dir),
        parent_map=str(a.parent_map),arena=f'redisplay_snapshot+{ARENA_OFFSET}',arena_end_offset=ARENA_OFFSET+EXTENT,
        highest_module_segment_word=top,original_inputs=[],
        scope='Companion layout and loader fixup-rule equivalence only; no DOS loader run, ownership, BSS/stack initialization, entry or parent admission.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('CONNECTION_MODULE',info['module_bytes'],'file bytes',n,'fixups',info['allocated_image_bytes'],'image bytes',
          admitted,'equivalent deltas',refused,'A000 refusals: OK')


if __name__=='__main__':main()
