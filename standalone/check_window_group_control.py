#!/usr/bin/env python3
"""A single missing DGROUP declaration must fail the actual DOS window probe."""
import argparse,hashlib,json,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    baseline=json.loads((ROOT/'build/notice-window/manifest.json').read_text());inputs=dict(baseline['sources']);inputs['standalone/test_notice_window_dos.py']=sha(ROOT/'standalone/test_notice_window_dos.py')
    with tempfile.TemporaryDirectory(prefix='pcplus-window-group-') as name:
        stage=Path(name)
        for path,digest in inputs.items():
            assert sha(ROOT/path)==digest;target=stage/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/path,target)
        binding=stage/'src/ui/notice_window_native.asm';text=binding.read_text();assert text.count('GROUP DGROUP _DATA\n')==1;binding.write_text(text.replace('GROUP DGROUP _DATA\n','',1))
        assert not (stage/'analysis').exists()
        with (out/'build.log').open('w') as log:subprocess.run(['python3',str(stage/'standalone/build_notice_window.py')],cwd=stage,stdout=log,stderr=log,check=True)
        variant=json.loads((stage/'build/notice-window/manifest.json').read_text());raw=[path for path in baseline['products'] if path.endswith('.bin')]
        assert all(variant['products'][path]==baseline['products'][path] for path in raw)
        assert variant['products']['WINDOW.EXE']!=baseline['products']['WINDOW.EXE']
        with (out/'probe.log').open('w') as log:process=subprocess.run(['python3',str(stage/'standalone/test_notice_window_dos.py'),'--output',str(stage/'build/probe')],cwd=stage,stdout=log,stderr=log)
        result=json.loads((stage/'build/probe/result.json').read_text());assert process.returncode!=0 and not result['passed'] and result['checks']['emulator_exit'] and not result['checks']['DOS_exit']
        assert (stage/'build/probe/FAIL.TXT').exists() and not (stage/'build/probe/PASS.TXT').exists()
        shutil.copytree(stage/'build/probe',out/'rejected-DOS')
        for path in (binding,stage/'build/notice-window/manifest.json',stage/'build/notice-window/WINDOW.map'):
            target=out/path.relative_to(stage);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
        variant_binding_sha256=sha(binding)
    record=dict(passed=True,single_change='Remove GROUP DGROUP _DATA from the native window adapter only',rejected=True,raw_native_products_unchanged=len(raw),bad_binary_sha256=variant['products']['WINDOW.EXE'],good_binary_sha256=baseline['products']['WINDOW.EXE'],variant_binding_sha256=variant_binding_sha256,inputs=inputs,checker_sha256=sha(Path(__file__)),captures_sha256={str(path.relative_to(out)):sha(path) for path in out.rglob('*') if path.is_file()},scope=__doc__+' Source-only controlled link-context regression. Raw recovered instruction products stay identical while the deliberately misframed linked DOS program fails. No altered source or executable is published as a working application.')
    (out/'result.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(dict(passed=True,rejected=True,raw_native_products_unchanged=len(raw))))
if __name__=='__main__':main()
