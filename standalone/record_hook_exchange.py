#!/usr/bin/env python3
"""Bind pure HOOK component tests to retained REA and separate native comparisons."""
import argparse,hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--run',required=True);ap.add_argument('--cohort',required=True);ap.add_argument('--output',required=True);a=ap.parse_args()
    run=ROOT/a.run;cohort=ROOT/a.cohort;assert run.is_relative_to(ROOT/'build') and cohort.is_relative_to(ROOT/'build')
    d=read(run/'result.json');assert d['passed'] and all(d['checks'].values()) and d['self_checks']==325 and d['original_inputs']==[]
    assert (run/'OUTPUT.TXT').read_bytes()==b'HOOKEXCHANGE checks=325 failures=0\r\n'
    assert (run/'HOST.TXT').read_bytes()==b'HOOKEXCHANGE checks=325 failures=0\n'
    assert sha(run/'HKEXCH.EXE')==sha(run/'rebuild/HKEXCH.EXE')==d['binary_sha256']
    for n,h in d['sources'].items():assert sha(ROOT/n)==sha(run/'source'/n)==h,n
    frame=(run/'HOOK.BIN').read_bytes();assert len(frame)==2094 and frame==(run/'host/HOOK.BIN').read_bytes()
    assert frame[:20]==bytes((i*17+128)&255 for i in range(20))
    assert frame[830:]==bytes((i*37)&255 for i in range(1264))
    for i in range(10):
        slot=frame[20+i*81:20+(i+1)*81];end=80 if i==9 else i*8
        assert slot[end]==0 and all(v>=128 for j,v in enumerate(slot) if j!=end)
    assert (run/'TAIL.TXT').read_bytes()==(' PCPLUS '+str(0x1234d126)+' '+str(0x1234d13a)+' '+str(0x12341b84)+' 3').encode()==(run/'host/TAIL.TXT').read_bytes()
    sys.path.insert(0,str(ROOT/'standalone'));from omf_imports import records,externals
    imports=sorted({n.decode() for kind,body,_ in records((run/'exchange.obj').read_bytes()) if kind==0x8c for n,_ in externals(body)})
    assert imports==['_small_code_'],imports
    rea=ROOT/'analysis/hook-registers-16.rea.json';bundle=read(rea);assert len(bundle['records'])==2
    ids={r['evidence_id'] for r in bundle['records']}
    assert ids=={'ev_05db164d5a5d051f96140f6dff4a7378cea3995ed79134200ab57ba22cbc6455','ev_c4dfed9da35890d213145769f511bf4b86f145491e38a9ad0e02828c27f2a1bd'}
    assert all(r['subject']['digest']['sha256']=='e14871502dba5f55646eb6184cf488c216381e6eda2ca47227a06934592b8302' for r in bundle['records'])
    native=read(ROOT/'build/meta-keys/cpu-results.json');assert native['passed'] and native['cases']==native['original_comparisons']==297
    assert native['binary_sha256']==sha(ROOT/'build/meta-keys/METAKEYS.EXE')
    proof=read(ROOT/'reconstruction/meta_keys/provenance.json');assert proof['source_sha256']=='6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904'
    direct=ROOT/'build/hook-exchange/native-codec-final-01';comparison=read(direct/'result.json')
    assert comparison['passed'] and len(comparison['cases'])==5 and comparison['original_sha256']==proof['source_sha256']
    assert {c['context'] for c in comparison['cases']}=={3,0,-1,32767,-32768}
    for case in comparison['cases']:
        assert case['passed']
        expected=' PCPLUS '+str(case['integers'])+' '+str(case['strings'])+' '+str(case['prm'])+' '+str(case['context'])
        assert bytes.fromhex(case['tail_hex'])==expected.encode()
    for n,h in comparison['sources'].items():assert sha(ROOT/n)==h,n
    cohort.mkdir(parents=True,exist_ok=False);custody={}
    def keep(path):
        target=cohort/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
        assert sha(target)==sha(path);custody[str(target.relative_to(ROOT))]=sha(target)
    for p in sorted(run.rglob('*')):
        if p.is_file():keep(p)
    for p in sorted(direct.rglob('*')):
        if p.is_file():keep(p)
    extra=[ROOT/'build/meta-keys/METAKEYS.EXE',ROOT/'standalone/meta_keys_host.asm',rea,ROOT/'analysis/pcplus-overlays/manifest.json',ROOT/'analysis/pcplus-overlay-anchored-02/functions/0x1d6ea-asm.json',ROOT/'analysis/pcplus-main/functions/0x1414c-asm.json',ROOT/'build/meta-keys/cpu-results.json',ROOT/'build/meta-keys/manifest.json',ROOT/'build/hook-exchange/native-meta-comparison.log',ROOT/'standalone/check_meta_keys.py',ROOT/'standalone/dos_image.py',ROOT/'standalone/omf_imports.py',ROOT/'reconstruction/meta_keys/provenance.json',Path(__file__),ROOT/'Makefile',ROOT/'tools/dev',ROOT/'nix/flake.nix',ROOT/'nix/flake.lock']
    for p in extra:keep(p)
    for p in sorted((ROOT/'build/hook-exchange/DOS-01').rglob('*')):
        if p.is_file():keep(p)
    result=dict(passed=True,component_accepted=True,terminal_HOOK_accepted=False,full_application_accepted=False,
        self_checks=325,native_KEY_comparisons=297,direct_original_HOOK_codec_comparisons=5,binary_sha256=d['binary_sha256'],original_inputs_in_normal_build=[],sources=d['sources'],code_bank_imports=imports,
        REA_evidence_ids=sorted(ids),custody_sha256=custody,
        early_attempts=['Host warning-as-error caught compressed statement indentation before acceptance.','DOS warning-as-error caught always-true32-bit range comparisons; checks are compiled only for wider host longs.'],
        scope='Pure KEY-kind2 HOOK tail codec, typed-bank geometry and maintained raw2094-byte staging. Host/8086 DOS outputs match and a fresh link reproduces the diagnostic. Separate original KEY routing/formatter replay and static derived-overlay REA establish protocol/array shapes. No foreign-memory admission, DOS allocation/EXEC, live PRM application, terminal kind2 integration, arbitrary helper/fault behavior, BBS or physical hardware acceptance.')
    output=ROOT/a.output;output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n');print('PASS',len(custody),'preserved files')
if __name__=='__main__':main()
