#!/usr/bin/env python3
"""Exercise damaged/replaced notice ownership, rejected retry and repaired VM reuse."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    out=parser.parse_args().output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    rows=[]
    for ownership in ['guard','foreign']:
        for port,flow in [(1,'H'),(2,'B')]:
            for mode in ['2D','2A','2F']:
                folder=out/f'{ownership}-com{port}-{flow}-{mode}'
                process=subprocess.run([sys.executable,str(ROOT/'standalone/test_program_notices_dos.py'),'--mode',mode,'--quarantine',ownership,'--success-after-error','--port',str(port),'--flow',flow,'--output',str(folder)],cwd=ROOT)
                path=folder/'result.json';r=json.loads(path.read_text()) if path.exists() else {}
                passed=process.returncode==0 and r.get('passed',False) and len(r.get('cases',[]))==1
                rows.append(dict(ownership=ownership,port=port,flow=flow,mode=mode,passed=passed,result=str(path.relative_to(ROOT)),result_sha256=sha(path) if r else None))
                (out/'result.json').write_text(json.dumps(dict(passed=len(rows)==12 and all(row['passed'] for row in rows),cases=rows,checker_sha256=sha(Path(__file__)),scope=__doc__+' Real DIV, foreign-DS DIV and typed abort in DOS8086 on COM1/HARD and COM2/BOTH. A bad guard or foreign replacement remains owned, with private streams/JFT masks and program/view leases retained. Live retry and new VM entry reject. Owner repair followed by stopped-invocation retry retires all resources, preserves the original cause, runs another popup and a successful child, and retains508 peer bytes.'),indent=2)+'\n')
                assert passed
    print(json.dumps(dict(passed=True,cases=len(rows))))
if __name__=='__main__':main()
