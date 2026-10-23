#!/usr/bin/env python3
"""Run every PROGRAM message branch, then an actual successful DOS child."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    out=parser.parse_args().output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    rows=[]
    for error in ['missing','longtail','format','memory','generic']:
        for port,flow in [(1,'H'),(2,'B')]:
            folder=out/f'{error}-com{port}-{flow}'
            result=subprocess.run([sys.executable,str(ROOT/'standalone/test_program_notices_dos.py'),'--mode','0N','--error',error,'--success-after-error','--port',str(port),'--flow',flow,'--output',str(folder)],cwd=ROOT)
            report=json.loads((folder/'result.json').read_text()) if (folder/'result.json').exists() else {}
            passed=result.returncode==0 and report.get('passed',False) and len(report.get('cases',[]))==1
            rows.append(dict(error=error,port=port,flow=flow,passed=passed,result=str((folder/'result.json').relative_to(ROOT)),result_sha256=sha(folder/'result.json') if report else None))
            receipt=dict(passed=len(rows)==10 and all(row['passed'] for row in rows),cases=rows,checker_sha256=sha(Path(__file__)),scope=__doc__+' COM1/HARD and COM2/BOTH; real missing/empty-file DOS failures, bounded composed-batch-tail rejection, actual free-paragraph exhaustion and explicitly unsupported EXEC-mode4. The latter proves the errno8 route, not malformed-executable rejection on real DOS. Each session runs a second missing command and a source-built child that creates SUCCESS.OK and returns0; two popups only, last CRT/DOS errors0,508 retained bytes and exact flow wire.')
            (out/'result.json').write_text(json.dumps(receipt,indent=2)+'\n');assert passed
    print(json.dumps(dict(passed=True,cases=len(rows))))
if __name__=='__main__':main()
