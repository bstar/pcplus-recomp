#!/usr/bin/env python3
"""Require the real HARD watermark test to reject a source-built early-RTS mutant."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from build_phone_log_queue import ROOT,sha
from prove_phone_log_startup_terminal import flags


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--terminal',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--commit',required=True)
    args=parser.parse_args()
    source,parent,output=args.source.resolve(),args.terminal.resolve(),args.output.resolve()
    assert all(p.is_relative_to(ROOT/'build') for p in (source,parent,output))
    assert source.name=='source' and not output.exists() and not (source/'.git').exists()
    manifest=json.loads((parent/'manifest.json').read_text());original=sha(parent/'TERMINAL.EXE')
    assert original==manifest['binary_sha256'] and manifest['experimental_phone_log_controls']
    revision=subprocess.check_output(['git','rev-parse',args.commit+'^{commit}'],text=True).strip()
    copied={};output.mkdir(parents=True);fresh=output/'source'
    for path in sorted(source.rglob('*')):
        relative=path.relative_to(source)
        if not path.is_file() or relative.parts[0]=='build' or '__pycache__' in relative.parts:continue
        assert relative.parts[0] not in ('.git','original','originals','analysis','install')
        assert relative.suffix.lower() not in ('.exe','.com','.obj','.img','.db','.prm','.fon')
        public=subprocess.check_output(['git','show',revision+':'+relative.as_posix()])
        assert path.read_bytes()==public,relative
        target=fresh/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(public)
        stamp=path.stat();os.utime(target,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
        copied[relative.as_posix()]=sha(target)
    target=fresh/'src/directory/phone_log_disk.c'
    before=target.read_text();old='if(hard && !uart_rts_lowered)';new='if(hard)'
    assert before.count(old)==1
    target.write_text(before.replace(old,new))
    mutation=dict(path='src/directory/phone_log_disk.c',before_sha256=copied['src/directory/phone_log_disk.c'],
                  after_sha256=sha(target),before=old,after=new)
    with (output/'build.log').open('w') as log:
        subprocess.run([sys.executable,'standalone/build_terminal.py',*flags(manifest,True)],cwd=fresh,stdout=log,stderr=log,check=True)
        rebuilt=fresh/'build'/parent.name
        changed=sha(rebuilt/'TERMINAL.EXE');assert changed!=original
        run=subprocess.run([sys.executable,'standalone/test_phone_log_slow_terminal.py','--terminal',str(rebuilt),
                            '--label','early-rts','--watermark','--case','hard-watermark'],cwd=fresh,stdout=log,stderr=log)
        assert run.returncode==1
    path=fresh/'build/phone-log-slow-terminal/early-rts/result.json'
    report=json.loads(path.read_text());assert not report['passed'] and len(report['cases'])==1
    row=report['cases'][0];failed=[name for name,ok in row['checks'].items() if not ok]
    assert failed==['no_sampled_RTS_override'],failed
    assert report['checks']==dict(all_cases=False,sources_unchanged=True,binary_unchanged=True)
    assert row['slow_snapshot'][19]>0 and row['slow_snapshot'][20]>0
    assert row['native']['passed'] and original==sha(parent/'TERMINAL.EXE')
    assert sha(ROOT/'src/directory/phone_log_disk.c')==mutation['before_sha256']
    result=dict(passed=True,source_commit=revision,source_count=len(copied),original_inputs=[],
        all_copied_inputs_matched_public_commit=True,source_mutation=mutation,
        production_terminal_sha256=original,production_source_unchanged=True,mutant_terminal_sha256=changed,
        native_report={'path':str(path.relative_to(ROOT)),'sha256':sha(path)},expected_failed_checks=failed,
        post_logger_samples=row['slow_snapshot'][19],bad_RTS_samples=row['slow_snapshot'][20],
        slow_snapshot=row['slow_snapshot'],build_log_sha256=sha(output/'build.log'),
        scope=__doc__+' Separate ignored public-source copy; exactly one source guard removed. '
        'No production source, executable, product RAM, installed files, card or live service patched.')
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: deliberate early RTS rejected;',result['bad_RTS_samples'],'bad samples; production source/image unchanged')

if __name__=='__main__':main()
