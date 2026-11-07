#!/usr/bin/env python3
"""Bind the active-ALARM native abort fix, memory funding and same-process reuse."""
import hashlib,json,struct,subprocess
from pathlib import Path
from build_context_help import ROOT,sha


def minimum(path):
    w=struct.unpack_from('<14H',path.read_bytes())
    module=w[2]*512-(512-w[1]if w[1]else 0)-w[4]*16
    return (((module+15)//16)+w[5]+16)*16


def main():
    sources,receipts={},{}
    def read(name,passed=True,field=None):
        path=ROOT/name;r=json.loads(path.read_text());assert r.get('passed',passed)==passed,name
        receipts[name]=sha(path)
        if field:
            for n,h in r[field].items():assert sha(ROOT/n)==h,n;sources[n]=h
        return r
    parent=ROOT/'build/terminal-alarm-policy-admission-20261106'
    child=ROOT/'build/aspect-alarm-unwind-funded-20261106'
    products={'TERMINAL.EXE':sha(parent/'TERMINAL.EXE'),'ASPECT.EXE':sha(child/'ASPECT.EXE')}
    assert products['ASPECT.EXE']=='b4f0aecc7a6538920711c2fa866324d2ddad856883a437cbb2f125cd0e26efbe'
    pm=read(str((parent/'manifest.json').relative_to(ROOT)),field='sources')
    cm=read(str((child/'manifest.json').relative_to(ROOT)),field='sources')
    assert pm['binary_sha256']==products['TERMINAL.EXE'] and cm['binary_sha256']==products['ASPECT.EXE'] and not cm['diagnostic_build']
    assert cm['startup_heap_growth_bytes']==512 and cm['experimental_deferred_script_buffers'] and cm['experimental_alarm_VM']
    # Bind the pre-fix executable to its actual public source revision, without
    # pretending that its old source hashes describe today's worktree.
    old=read('build/aspect-alarm-progress-20261106/manifest.json')
    names=list(old['sources']);queries=''.join('4057dd3:'+n+'\n' for n in names).encode()
    data=subprocess.check_output(['git','cat-file','--batch'],input=queries,cwd=ROOT);at=0
    for n in names:
        end=data.index(b'\n',at);header=data[at:end].split();assert len(header)==3 and header[1]==b'blob',n
        size=int(header[2]);at=end+1;assert hashlib.sha256(data[at:at+size]).hexdigest()==old['sources'][n],n;at+=size+1
    assert at==len(data)
    negative=read('build/alarm-carrier-matrix-20261106/checks.json',passed=False)
    bad=next(c for c in negative['cases']if c['case']=='XOFF')
    folder=ROOT/'build/alarm-carrier-matrix-20261106/XOFF'
    assert sha(folder/'ASPECT.EXE')==old['binary_sha256']
    assert bad['child_header'][6]==14 and bad['speaker_words'][3:6]==[3,1,6]
    for n,h in bad['captures'].items():assert sha(folder/n)==h,n;receipts[str((folder/n).relative_to(ROOT))]=h
    cases=[]
    for label,profile in (('alarm-carrier-funded-ansi-20261106',6),('alarm-carrier-funded-vt220-20261106',4)):
        folder=ROOT/'build'/label;report=read(str((folder/'checks.json').relative_to(ROOT)),field='sources')
        assert report['products']==products and not report['diagnostic_reuse'] and report['profile']==profile
        assert [c['case']for c in report['cases']]==['NONE','CALL','TX','XOFF']
        for c in report['cases']:
            assert c['passed']and all(c['checks'].values())and c['observer_segment']>=0xa000
            assert c['speaker_words'][3:]==[0,0,4,1]and c['armed_at_exit']==0
            assert c['child_header'][6]==(14 if c['case']=='XOFF'else 0)
            times=c['event_times'];assert times['hold']<times['query']<=times['reply']<times['hangup']
            for n,h in c['captures'].items():assert sha(folder/c['case']/n)==h,n;receipts[str((folder/c['case']/n).relative_to(ROOT))]=h
            cases.append(dict(profile=profile,case=c['case'],child_exit=c['child_header'][6],speaker_words=c['speaker_words'],checks=c['checks']))
    reuse=read('build/alarm-carrier-reuse-funded-20261106/checks.json',field='sources')
    dm=read('build/aspect-alarm-reuse-funded-20261106/manifest.json',field='sources')
    assert dm['diagnostic_build']and dm['diagnostic_alarm_reuse']and dm['reference_binary_sha256']==products['ASPECT.EXE']
    assert set(dm['objects'])==set(cm['objects'])and all(h==cm['objects'][n]for n,h in dm['objects'].items()if n!='runner.o')
    assert reuse['diagnostic_reuse']and reuse['products']['ASPECT.EXE']==dm['binary_sha256']
    rc=reuse['cases'][0];assert rc['passed']and all(rc['checks'].values())and [r[0]for r in rc['reuse_rows']]==[14,0,0]
    for n,h in rc['captures'].items():
        p=ROOT/'build/alarm-carrier-reuse-funded-20261106/XOFF'/n;assert sha(p)==h,n;receipts[str(p.relative_to(ROOT))]=h
    unfunded=read('build/aspect-alarm-unwind-20261106/manifest.json')
    assert set(unfunded['objects'])==set(cm['objects'])and [n for n,h in cm['objects'].items()if h!=unfunded['objects'][n]]==['runner.o']
    failed_capacity=read('build/alarm-unwind-capacity-20261106/result.json',passed=False)
    assert failed_capacity['interpreter_sha256']==unfunded['binary_sha256']and sum(not v for v in failed_capacity['checks'].values())==7
    for label,count,cpu in (('alarm-unwind-funded-capacity-20261106',27,'386'),('alarm-unwind-funded-capacity-8086-20261106',26,'8086')):
        r=read('build/'+label+'/result.json',field='sources');assert r['interpreter_sha256']==products['ASPECT.EXE']and r['cpu']==cpu
        assert len(r['checks'])==count and all(r['checks'].values())and r['nested_child_count']==3
    compact=read('build/alarm-cli-path-compact-20261106/result.json',field='sources');assert compact['cases']==113580
    cold=read('build/alarm-unwind-funded-cold-20261106/result.json',field='overlay_sources')
    assert cold['products']==products and cold['source_files']==5420
    assert cold['results']['active_alert']['cases']==1 and cold['results']['compact_cli']['cases']==113580
    assert cold['results']['unit']['cases']==33341 and cold['results']['legacy']['cases']==94 and cold['results']['progress']['cases']==33
    assert cold['results']['numeric']['cases']==cold['results']['strings']['cases']==512
    assert cold['results']['numeric']['deep_cases']==cold['results']['strings']['deep_cases']==2 and cold['results']['ALARM']['cases']==1
    inventory=ROOT/'build/alarm-unwind-funded-cold-20261106/inventory.json';assert sha(inventory)==cold['inventory_sha256']and len(json.loads(inventory.read_text()))==5420
    default=ROOT/'build/aspect-runner/ASPECT.EXE';assert sha(default)=='91256a7b873b3ff65dd0b4df177f2dfaff2ee72860db5b3b4fd44c481f1d364b'
    assert read('build/aspect-runner/manifest.json',field='sources')['binary_sha256']==sha(default)
    sources['standalone/record_alarm_unwind.py']=sha(Path(__file__))
    result=dict(passed=True,release_accepted=False,products=products,sources=sources,receipts=receipts,cases=cases,
                same_process_reuse_rows=rc['reuse_rows'],matching_diagnostic_backend_objects=len(cm['objects'])-1,
                minimum_including_PSP=dict(unfunded=minimum(ROOT/'build/aspect-alarm-unwind-20261106/ASPECT.EXE'),funded=minimum(child/'ASPECT.EXE')),
                negative_source_commit='4057dd3',original_inputs=[],scope=__doc__,limitations=[
                    'Actual DOSBox modem/DCD plus standard BIOS and verified UMB observer, not physical Boca/SPA2102/SIP/DSP/CTS or acoustic acceptance.',
                    'Only the marked diagnostic replaces the CLI to invoke VM three times;205 backend objects are exact. It must never be packaged/deployed. Eight ordinary-product carrier cases are separate.',
                    'Cold5420-source export repeats bank/clock/compact-path suites, one normal ALARM and one active XOFF error. It does not repeat the whole carrier matrix, same-process diagnostic, capacity or modern BBS suites.',
                    'Early fixture attempts inherited8086 and failed before ALARM; subsequent menu checks expected an obsolete title. Accepted386 fixtures require actual UMB residency and capture the restored PROCOMM PLUS command screen.',
                    'XOFF service timeout uses PCPLUS_TXWAIT=2. The watchdog bounds callbacks between progress observations; it does not preempt a synchronous native TX callback before its own stall deadline.',
                    'Unfunded fix failed7capacity checks; only runner.o changed for the funded candidate. No buffer/stack/slot reduction. Ordinary interpreter byte-identical.',
                    'Modern Enigma/Synchronet regressions for this new candidate, package selection, physical acceptance and remaining application inventory are still open. Installed RCC859D7/private config/history are unchanged. Foreign-stack, kernel/allocator corruption and recursive cleanup faults are not claimed.'
                ])
    assert result['minimum_including_PSP']==dict(unfunded=131344,funded=131168)
    (ROOT/'docs/validation/aspect-alarm-unwind.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS active ALARM abort/reuse/funding/cold checkpoint')


if __name__=='__main__':main()
