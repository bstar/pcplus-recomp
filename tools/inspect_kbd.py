#!/usr/bin/env python3
"""Inspect KBD shape/schema without displaying or modifying private bindings."""
import argparse
import hashlib
import json
import os
from pathlib import Path

PROFILE_BYTES=948
SLOT_BYTES=12
HELPER_BYTES=31284


def inspect(path,profile):
    with path.open('rb') as stream:
        before=os.fstat(stream.fileno())
        stream.seek(profile*PROFILE_BYTES)
        selected=stream.read(PROFILE_BYTES)
        whole=None
        if before.st_size<=HELPER_BYTES:
            stream.seek(0)
            whole=stream.read(HELPER_BYTES+1)
        after=os.fstat(stream.fileno())
    stable=(before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
    complete=before.st_size>0 and before.st_size%PROFILE_BYTES==0
    selected_bad=([slot for slot in range(79) if b'\0' not in selected[slot*SLOT_BYTES:(slot+1)*SLOT_BYTES]]
                  if len(selected)==PROFILE_BYTES else None)
    all_bad=None
    if whole is not None and complete and len(whole)==before.st_size:
        all_bad=[slot for slot in range(len(whole)//SLOT_BYTES) if b'\0' not in whole[slot*SLOT_BYTES:(slot+1)*SLOT_BYTES]]
    return dict(file_bytes=before.st_size,whole_profiles=before.st_size//PROFILE_BYTES if complete else None,
                selected_profile=profile,stable_metadata=stable,
                selected_profile_present=len(selected)==PROFILE_BYTES,
                selected_unterminated_slots=selected_bad,
                parent_content_compatible=stable and complete and len(selected)==PROFILE_BYTES and not selected_bad,
                helper_contract=2,
                helper_content_compatible=stable and len(selected)==PROFILE_BYTES and all_bad is not None and not all_bad,
                legacy_full_helper_content_compatible=stable and before.st_size==HELPER_BYTES and all_bad is not None and not all_bad,
                helper_unterminated_slot_count=len(all_bad) if all_bad is not None else None,
                sha256=hashlib.sha256(whole).hexdigest() if whole is not None else None,
                content_check_only=True,
                scope='Read-only content check against maintained selected-profile loader and contract2 prefix editor; legacy full-file compatibility is separate. No binding values displayed. DOS path/access/close behavior, file locking and hardware are not verified.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file',type=Path)
    parser.add_argument('--profile',type=int,choices=range(33),default=6,help='Zero-based profile; ANSI6, VT2204')
    args=parser.parse_args()
    print(json.dumps(inspect(args.file,args.profile),indent=2))


if __name__=='__main__':main()
