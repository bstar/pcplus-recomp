#!/usr/bin/env python3
"""Audit source-bound terminal projection, real DOS images and diagnostic separation."""
import argparse,hashlib,json,shutil,struct
from pathlib import Path
from terminal_memory import inspect_terminal_memory
from omf_imports import records,externals
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cohort',type=Path,required=True);a=ap.parse_args()
    out=a.cohort.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
    base=ROOT/'build/terminal-directory-keys-process-bank-session-capture-projection';m=read(base/'manifest.json')
    probe=ROOT/(str(base.relative_to(ROOT))+'-probe');pm=read(probe/'manifest.json')
    assert m['experimental_session_projection'] and not m['session_projection_probe'] and pm['session_projection_probe']
    for folder,r in [(base,m),(probe,pm)]:assert sha(folder/'TERMINAL.EXE')==r['binary_sha256']
    assert b'PBASE.BIN' not in (base/'TERMINAL.EXE').read_bytes()
    assert 'terminal_session_projection_probe_far' not in (base/'terminal.map').read_text()
    layout=inspect_terminal_memory(base/'TERMINAL.EXE',base/'terminal.map');assert layout==m['memory_layout']
    assert layout['near_bytes']==65520 and layout['resident_code_spare_bytes']==702
    assert next(c for c in layout['code_segments'] if c['name']=='HOOK_CODE')['bytes']==1983
    imports={}
    allowed={
        'prm_projection':{'hook_memcpy_service_','_hook_rate_index','_hook_transfer_path_service','_hook_terminal_decode_service','hook_memcmp_service_','_hook_modem_decode_service','_hook_transfer_decode_service','_small_code_'},
        'session_projection':{'_hook_session_capture','terminal_option_mask','terminal_directory_mode','terminal_directory_context_valid','_prm_project_session','_small_code_'}}
    for name,wanted in allowed.items():
        imports[name]=[n.decode() for kind,payload,_ in records((base/(name+'.obj')).read_bytes()) if kind==0x8c for n,_ in externals(payload)]
        assert set(imports[name])==wanted
    linked_path=ROOT/'build/session-projection/linked-final-01/result.json';linked=read(linked_path)
    assert linked['passed'] and linked['inputs']==54 and linked['binary_sha256']==m['binary_sha256']
    component=ROOT/'build/prm-projection/session-DOS-01';cr=read(component/'result.json')
    assert cr['passed'] and all(cr['checks'].values()) and cr['self_checks']==2688 and cr['original_inputs']==[]
    assert (component/'OUTPUT.TXT').read_bytes()==b'PRMPROJECT checks=2688 failures=0\r\n'
    assert sha(component/'PRMPROJ.EXE')==cr['binary_sha256']==sha(component/'rebuild/PRMPROJ.EXE')
    before=(component/'INBASE.BIN').read_bytes();after=(component/'INACTIVE.BIN').read_bytes()
    assert len(before)==len(after)==1264 and before[0xa:0x174]==after[0xa:0x174]==bytes([255])*(0x174-0xa)
    assert after[0x1a4:0x1a6]==struct.pack('<H',350)
    dos=ROOT/'build/session-projection/DOS-01';d=read(dos/'result.json')
    assert d['passed'] and len(d['cases'])==5 and d['binary_sha256']==pm['binary_sha256']
    for r in d['cases']:
        assert r['passed'] and all(r['checks'].values());folder=dos/r['case']
        initial=(folder/'TEST.PRM').read_bytes();assert initial==(folder/'PBASE.BIN').read_bytes() and len(initial)==1264
        expected=bytearray(initial);serial=r['case'] in ('serial','serial-inactive')
        struct.pack_into('<H',expected,2,5 if serial else 6)
        struct.pack_into('<H',expected,0x194,6 if r['case'].startswith('directory-') else 4)
        if serial:struct.pack_into('<H',expected,0x1a4,350)
        assert (folder/'POUT.BIN').read_bytes()==expected
        assert (folder/'PSTAT.BIN').read_bytes()==b'\0\0'
        assert (folder/'PASS.TXT').read_bytes().strip()==b'PASS' and not (folder/'FAIL.TXT').exists()
        assert (folder/'BEFORE.BIN').read_bytes()==(folder/'AFTER.BIN').read_bytes() and len((folder/'BEFORE.BIN').read_bytes())==42
        assert 'cputype=8086' in (folder/'dosbox.conf').read_text()
    proof_path=ROOT/'build/session-projection/source-final-01/result.json';proof=read(proof_path)
    assert proof['passed'] and proof['original_inputs']==[] and proof['source_files']==681 and len(proof['products'])==6
    for n,h in proof['products'].items():assert sha(ROOT/n)==h,n
    assert proof['checker_sha256']==sha(ROOT/'standalone/prove_directory_keys_source.py')
    serial_path=ROOT/'build/directory-keys/projection-script-final-01/result.json';serial=read(serial_path)
    assert serial['passed'] and all(serial['checks'].values()) and serial['port']==2 and serial['case']=='script'
    assert serial['binary_sha256']==m['binary_sha256']
    serial_folder=ROOT/'build/connection-dos/dirkeys-projection-script-final-01'
    assert bytes.fromhex(serial['expected_wire_hex']) in (serial_folder/'serial.bin').read_bytes()
    assert (serial_folder/'BEFORE.BIN').read_bytes()==(serial_folder/'AFTER.BIN').read_bytes()
    sources={}
    for r in [m,pm,linked,cr,d,proof,serial]:
        for n,h in r['sources'].items():assert n not in sources or sources[n]==h,n;sources[n]=h
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    files=[ROOT/n for n in sources]+[linked_path,proof_path,proof_path.parent/'build.log']
    files.append(serial_path)
    files.extend(p for p in serial_folder.iterdir() if p.is_file())
    for folder in [base,probe]:files.extend(folder/n for n in ['manifest.json','TERMINAL.EXE','terminal.map'])
    files.extend(base/(n+'.obj') for n in imports)
    for folder in [dos,component]:files.extend(p for p in folder.rglob('*') if p.is_file() and 'source' not in p.relative_to(folder).parts)
    files.extend([Path(__file__).resolve(),ROOT/'standalone/omf_imports.py',ROOT/'standalone/terminal_memory.py',ROOT/'Makefile',ROOT/'tools/dev',ROOT/'nix/flake.nix',ROOT/'nix/flake.lock'])
    out.mkdir(parents=True);custody={}
    for p in sorted(set(files)):
        target=out/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        assert sha(p)==sha(target);custody[str(target.relative_to(ROOT))]=sha(target)
    report=dict(passed=True,linked_cases=54,component_DOS_checks=2688,terminal_DOS_cases=d['cases'],
        source_files=681,products=proof['products'],normal_ASPECT_COM2=serial['checks'],memory_layout=layout,imports=imports,custody_sha256=custody,
        terminal_HOOK_accepted=False,full_native_PRM_accepted=False,full_application_accepted=False,
        scope='Source-built combined capture/projector, explicit inactive modem and shared-field rejection. Linked54 cases, component2688 DOS checks/two independent images, five diagnostic8086 startup workflows, six empty-tree products. No baseline identity/loading, remaining native fields, online helper/serial handoff, returned commit or hardware acceptance.')
    (ROOT/'docs/validation/session-projection.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS54 linked,2688 DOS checks,five terminal DOS cases,681 sources/six products')
if __name__=='__main__':main()
