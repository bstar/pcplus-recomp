#!/usr/bin/env python3
"""Audit linked code banks and every near call/jump in their C objects."""
import json,re,subprocess
from pathlib import Path
from build_aspect_process import ROOT,sha

OUT=ROOT/'build/aspect-fault-break'

def audit_object(path):
    listing=OUT/(path.stem+'-audit.dis')
    subprocess.run(['wdis','-e','-l='+str(listing),str(path)],check=True)
    text=listing.read_text().split('\nSegment: CONST',1)[0]
    labels=set(re.findall(r'^[0-9a-f]{4}\s+([\w$]+):\s*$',text,re.M|re.I))
    near=[];far=[]
    for match in re.finditer(r'^([0-9a-f]{4})\s+((?:[0-9a-f]{2}\s+)+)(call|jmp)\s+(\S+)',text,re.M|re.I):
        address,encoded,operation,target=match.groups();opcode=encoded.split()[0].upper()
        if opcode in ['9A','EA']:
            assert target.startswith(('_program_bank_','_native_break_')),(path.name,target)
            far.append(dict(offset=address,operation=operation,target=target))
        elif opcode in ['E8','E9','EB']:
            assert target in labels,(path.name,address,operation,target,'near target outside object')
            near.append(dict(offset=address,operation=operation,target=target))
        else:raise AssertionError((path.name,address,'Unreviewed indirect control transfer',encoded))
    assert far and near,path
    return dict(object_sha256=sha(path),near_internal=len(near),far_transfers=far,
                listing_sha256=sha(listing))

def main():
    manifest=json.loads((OUT/'manifest.json').read_text())
    assert manifest['experimental_break_owner']
    assert sha(OUT/'ASPECT.EXE')==manifest['binary_sha256']
    for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
    listing=(OUT/'ASPECT.map').read_text()
    symbols={name:(int(seg,16),int(off,16)) for seg,off,name in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})\s+(\w+)\s*$',listing,re.M|re.I)}
    segments={name:dict(segment=int(seg,16),offset=int(off,16),bytes=int(size,16))
        for name,seg,off,size in re.findall(r'^(_TEXT|BRKCODE|PROGRAMCODE)\s+CODE\s+\S+\s+([0-9a-f]+):([0-9a-f]+)\s+([0-9a-f]+)',listing,re.M|re.I)}
    assert set(segments)=={'_TEXT','BRKCODE','PROGRAMCODE'}
    for segment in segments.values():assert segment['offset']+segment['bytes']<=65536
    resident=segments['_TEXT']['segment']
    owner=symbols['program_break_install'][0]
    assert owner!=resident
    for name in ['program_break_restore','program_break_ignore','_native_break_open','_native_break_handler']:
        assert symbols[name][0]==owner,name
    controller=symbols['_native_program_execute'][0]
    assert controller!=resident
    assert symbols['_native_program_recover'][0]==controller
    assert symbols['_native_program_wait_key'][0]==controller
    # Both banks may share a linker-packed CS, but never the near CRT CS.
    for name,(segment,offset) in symbols.items():
        if name.startswith('_program_bank_'):assert segment==resident,name
    report=dict(passed=True,segments=segments,
        near_spare=65536-segments['_TEXT']['offset']-segments['_TEXT']['bytes'],
        objects=dict(controller=audit_object(OUT/'native_program_far.obj'),
                     owner=audit_object(ROOT/'build/break-owner-far/break_owner_far.obj')),
        binary_sha256=manifest['binary_sha256'],checker_sha256=sha(Path(__file__)),
        scope='Linked map placement plus decoded C-object near/far transfers. Every near transfer stays in its own object. Runtime/interrupt correctness requires the independent DOS and VM tests.')
    (OUT/'bank-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Both banks have explicit far external calls;',report['near_spare'],'near-code bytes spare')

if __name__=='__main__':main()
