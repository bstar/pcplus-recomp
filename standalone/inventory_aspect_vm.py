#!/usr/bin/env python3
"""Inventory original ASPECT loader/dispatch coordinates; optional private input.

No original code/resource blobs are exported. This does not implement a VM or
establish the semantics of every indexed handler.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
SHA = '6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original', type=Path, default=ROOT/'analysis/pcplus-originals/PCPLUS-main-2.01.EXE')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = args.original.read_bytes()
    assert sha(data) == SHA
    header = struct.unpack_from('<14H', data)
    header_bytes = header[4]*16
    module_end = (header[2]-1)*512+(header[1] or 512)
    manifest_path = ROOT/'analysis/pcplus-overlays/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    assert manifest['source_sha256'] == SHA and header_bytes == 0x1200
    overlays = {o['id']: o for o in manifest['overlays']}
    globals_ = overlays[32]
    assert globals_['source_file_offset'] == 0x25950 and globals_['relative_load_segment'] == 0xfb7
    assert sha(data[globals_['source_file_offset']:globals_['source_file_offset']+globals_['initialized_bytes']]) == globals_['sha256']
    # Native4B1F exact bounded indexed call: CMP SI,D6; JA; SHL SI; CALL[SI+4B08].
    assert data[header_bytes+0x4b9c:header_bytes+0x4ba8] == bytes.fromhex('81fed6007708d1e6ff94084b')
    table_offset = globals_['source_file_offset']+0x4b08
    targets = struct.unpack_from('<215H', data, table_offset)
    thunks = {t['file_offset']: t for t in manifest['trampolines']}
    records = []
    for opcode, target in enumerate(targets):
        location = header_bytes+target
        assert header_bytes <= location < module_end
        record = dict(opcode=opcode,opcode_hex=f'{opcode:02x}',resident_entry=f'{target:04x}',
                      resident_file_offset=location,entry_prefix_sha256=sha(data[location:location+12]))
        if location in thunks:
            thunk = thunks[location]
            raw = data[location:location+12]
            assert raw[:5] == bytes.fromhex('9aec02ec0a') and raw[7] == 0xea
            overlay_id = struct.unpack_from('<H',raw,5)[0]
            offset,segment = struct.unpack_from('<HH',raw,8)
            relative = segment*16+offset
            assert overlay_id == thunk['overlay'] and relative == thunk['target_relative_address']
            overlay = overlays[overlay_id]
            mapped = overlay['source_file_offset']+relative-overlay['relative_load_segment']*16
            assert overlay['source_file_offset'] <= mapped < overlay['source_file_offset']+overlay['initialized_bytes']
            record.update(kind='overlay-thunk',overlay=overlay_id,overlay_entry=f'{relative:04x}',
                          overlay_source_file_offset=mapped,overlay_entry_prefix_sha256=sha(data[mapped:mapped+12]))
        else:
            record['kind'] = 'resident'
        records.append(record)
    mappings = [
        ('resident-dispatch',None,0x4b1f,0x4bff),
        ('resident-byte-reader',None,0x4cb4,0x4cd7),
        ('loader-open-compile',2,0xd4d0,0xd6ea),
        ('loader-state-defaults',2,0xd6ea,0xd770),
        ('loader-start',2,0xd770,0xd804),
        ('loader-resource-cleanup',2,0xd804,0xd850),
        ('loader-global-strings',2,0xd850,0xd88e),
        ('loader-global-strings-release',2,0xd88e,0xd8b5),
        ('literal-reader',16,0xdfea,0xe0a4),
    ]
    units = []
    for name,overlay_id,start,end in mappings:
        source = header_bytes+start if overlay_id is None else overlays[overlay_id]['source_file_offset']+start-overlays[overlay_id]['relative_load_segment']*16
        units.append(dict(name=name,overlay=overlay_id,start=f'{start:04x}',end_exclusive=f'{end:04x}',
                          source_file_offset=source,bytes=end-start,sha256=sha(data[source:source+end-start])))
    out = args.output.resolve()
    assert out.is_relative_to(ROOT/'analysis/aspect-vm') and not out.exists()
    out.parent.mkdir(parents=True,exist_ok=True)
    result = dict(passed=True,original_sha256=SHA,inventory_source_sha256=sha(Path(__file__).read_bytes()),
        overlay_manifest_sha256=sha(manifest_path.read_bytes()),dispatch_table=dict(DS_offset='4b08',
            file_offset=table_offset,entries=len(records),bytes=430,sha256=sha(data[table_offset:table_offset+430])),
        resident_handlers=sum(r['kind']=='resident' for r in records),
        overlay_handlers=sum(r['kind']=='overlay-thunk' for r in records),
        overlay_handler_counts={str(i):sum(r.get('overlay')==i for r in records) for i in sorted({r['overlay'] for r in records if 'overlay' in r})},
        handlers=records,recovered_coordinates=units,
        facts=['First ASX byte is consumed by loaderD850 before dispatch and controls81-byte global-string allocations',
            'Dispatch accepts byte indices00..D6 inclusive; slots are not a declaration that each operand token has the same meaning when executed as a command',
            'For an out-of-range opcode, FILE+6 bit10 selects unexpected-EOF107, otherwise invalid-command106',
            'Loader and dispatcher retain original compiler/helper and application-service dependencies'],
        scope='Static index with source-byte coordinate verification only. Function boundaries use retained REA exports; handler semantics/completeness and runtime reachability are not established by table membership.')
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['handlers','recovered_coordinates']},indent=2))


if __name__=='__main__':
    main()
