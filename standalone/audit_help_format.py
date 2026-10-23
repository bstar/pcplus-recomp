#!/usr/bin/env python3
"""Preserve and independently check contextual-help format component evidence."""
import argparse,hashlib,json,shutil,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['source-only','compat','cohort','output']:p.add_argument('--'+name,required=True)
    a=p.parse_args();cohort=ROOT/a.cohort;cohort.mkdir(parents=True,exist_ok=False)
    custody={};runs=[]
    for name,compat in [(a.source_only,False),(a.compat,True)]:
        folder=ROOT/name;d=json.loads((folder/'result.json').read_text())
        assert d['passed'] and all(d['checks'].values()) and d['self_checks']==52
        assert (folder/'OUTPUT.TXT').read_bytes()==b'HELPFMT checks=52 failures=0\r\n'
        assert (folder/'INDEX.TXT').read_bytes()==b'HELP INDEX topics=2 lines=3 bytes=65543\r\n'
        b=(folder/'HELPTEST.HLP').read_bytes();assert len(b)==65543
        assert b[:3]==b'\x02\x03\0'
        assert struct.unpack_from('<HI',b,35)==(2,79)
        assert struct.unpack_from('<HI',b,73)==(1,65537)
        assert b[79:87]==b'ONE\nTWO\n' and b[65537:]==b'THREE\n'
        assert sha(folder/'HELPTEST.HLP')==sha(folder/'host/HELPTEST.HLP')
        assert sha(folder/'HELPFMT.EXE')==sha(folder/'rebuild/HELPFMT.EXE')==d['binary_sha256']
        assert sha(folder/'HELPREAD.EXE')==d['reader_sha256']
        assert all(str(folder/'source') in c for c in d['command'][-2:])
        assert d['original_inputs']==([dict(sha256='6aa2a38b1bae7c81d082d4efae4c7cd2becaf048bbdb93af4467b74bba9543d5',bytes=23558)] if compat else [])
        if compat:
            assert (folder/'COMPAT.TXT').read_bytes()==b'HELP INDEX topics=47 lines=463 bytes=23558\r\n'
            assert sha(folder/'COMPAT.HLP')==d['original_inputs'][0]['sha256']
        for n,h in d['sources'].items():assert sha(ROOT/n)==sha(folder/'source'/n)==h,n
        for n,h in d['captures_sha256'].items():assert sha(folder/n)==h,n
        runs.append(dict(path=name,checks=d['self_checks'],binary_sha256=d['binary_sha256'],reader_sha256=d['reader_sha256'],original_inputs=d['original_inputs']))
        for path in sorted(folder.rglob('*')):
            if not path.is_file():continue
            target=cohort/'accepted'/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
            assert sha(target)==sha(path);custody[str(target.relative_to(ROOT))]=sha(target)
    assert runs[0]['binary_sha256']==runs[1]['binary_sha256'] and runs[0]['reader_sha256']==runs[1]['reader_sha256']
    rea=ROOT/'analysis/help-context-01.rea.json';records=json.loads(rea.read_text())['records'];assert len(records)==13
    identities={r['subject']['digest']['sha256'] for r in records if 'subject' in r}
    assert {'6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904','5d135afc5808ddec923ec027f385490c7ecd4fa5004d11cefe6ff4a3c468d0aa'}.issubset(identities)
    for path in [rea,Path(__file__)]:
        target=cohort/'accepted'/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target);custody[str(target.relative_to(ROOT))]=sha(target)
    result=dict(passed=True,context_HLP_format_component_accepted=True,notice_Alt_Z_integration_accepted=False,
        full_application_accepted=False,runs=runs,REA_evidence_ids=[r['evidence_id'] for r in records if 'evidence_id' in r],
        custody_sha256=custody,scope='Source-only decoder component,52 host and DOS8086 assertions, sparse authored help data beyond64KiB, fresh diagnostic link, optional original47-topic/463-line read after compilation. Original PCHELP analyzed statically only. Main57AE is external contextual-help invocation; local script window is separate. No helper UI, cross-process descriptor admission, notice Alt-Z, nested EXEC, original resource redistribution or full application acceptance.')
    out=ROOT/a.output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS',len(custody),'preserved files; source-only and explicit compatibility components')
if __name__=='__main__':main()
