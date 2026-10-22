#!/usr/bin/env python3
"""Corrupt raw lab evidence while keeping producer flags and hashes green."""
import argparse,json,shutil,struct
from pathlib import Path
import audit_manual_cancel_dos as audit


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixed',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(audit.ROOT/'build') and not out.exists();out.mkdir(parents=True);rows=[]
    for name in ('high-first-DCD','retained-pause','bad-vector-restore','lost-init-byte','stock-backend-label','forged-patch-provenance'):
        folder=out/name;shutil.copytree(a.fixed.resolve(),folder);r=audit.read(folder/'checks.json');row=next(c for c in r['cases'] if c['case']=='soft')
        if name in ('high-first-DCD','retained-pause'):
            f=folder/'soft/CANCEL.BIN';b=bytearray(f.read_bytes());struct.pack_into('<H',b,8 if name=='high-first-DCD' else 16,1);f.write_bytes(b);row['captures']['CANCEL.BIN']=audit.sha(f)
        elif name=='bad-vector-restore':
            f=folder/'soft/VECNEW.BIN';b=bytearray(f.read_bytes());b[0]^=1;f.write_bytes(b);row['captures']['VECNEW.BIN']=audit.sha(f)
        elif name=='lost-init-byte':
            f=folder/'soft/serial.bin';b=f.read_bytes().replace(b'ATZ\r',b'TZ\r',1);f.write_bytes(b);row['captures']['serial.bin']=audit.sha(f);row['wire_hex']=b.hex()
        elif name=='stock-backend-label':r['emulator']['test_backend']=False
        else:
            key='nix/patches/dosbox-dcd-control.patch';f=folder/'inputs'/key;f.write_bytes(f.read_bytes()+b'\n# Different declared patch\n');r['inputs'][key]=audit.sha(f);r['emulator']['patch_sha256']=audit.sha(f)
        assert r['passed'] and all(c['passed'] and all(c['checks'].values()) for c in r['cases'])
        (folder/'checks.json').write_text(json.dumps(r,indent=2)+'\n')
        try:audit.verify(folder,False)
        except AssertionError:rows.append(dict(case=name,rejected=True,producer_flags_green=True,changed_capture_or_input_hash_updated=True))
        else:raise AssertionError('Bad evidence accepted: '+name)
    result=dict(passed=True,cases=rows,auditor_sha256=audit.sha(Path(audit.__file__)),checker_sha256=audit.sha(Path(__file__)),scope=__doc__+' Six owned copied-fixture controls. Physical/device claims are not enlarged; actual Nix derivation patch identity must match declared patch bytes.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,rejected=len(rows))))


if __name__=='__main__':main()
