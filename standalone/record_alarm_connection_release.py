#!/usr/bin/env python3
"""Bind the matched ALARM package, fresh BBS gates and original-free reproduction."""
import argparse,json
from pathlib import Path
from package_connection_test import ROOT,sha,render_capability


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();receipts,sources={},{}
    def load(name,field='sources'):
        path=ROOT/name;r=json.loads(path.read_text());assert r['passed'],name;receipts[name]=sha(path)
        for n,h in r.get(field,{}).items():assert sha(ROOT/n)==h,n;sources[n]=h
        return r
    root=ROOT/'build/alarm-connection-candidate-20261106'
    build=load(str(root.relative_to(ROOT))+'/result.json')
    m=json.loads((root/'package/manifest.json').read_text())
    assert sha(root/'package/manifest.json')==build['package_manifest_sha256']and m['files']==build['files']
    assert len(m['files'])==13 and not m['original_inputs']and not m['card_written']
    assert m['parent_render_capability']==19 and m['experimental_alarm_VM']
    assert m['files']['TERMINAL.EXE']=='689bdce91c267320b4aad9136a530ab8ce90f733f4a540197e53e6ce4074df06'
    assert m['files']['ASPECT.EXE']=='b4f0aecc7a6538920711c2fa866324d2ddad856883a437cbb2f125cd0e26efbe'
    assert m['files']['ASPCOMP.EXE']=='c26199a3191ce70097cfbdcf1050d049d01be0ce5fd66ad172004b9c924137a4'
    for n,h in m['sources'].items():assert sha(ROOT/n)==h,n;sources[n]=h
    for n,h in m['files'].items():assert sha(root/'package/PCPLUS'/n)==h,n
    assert not any(Path(n).suffix.upper()in('.PRM','.DIR','.KEY','.KBD','.XLT','.FON')for n in m['files'])
    assert render_capability(root/'terminal/TERMINAL.EXE')==19
    recipe=ROOT/'standalone/alarm_connection_candidate_recipe.json'
    r=json.loads(recipe.read_text());assert sha(recipe)==build['recipe_sha256']and r['expected_files']==m['files']
    cold=load('build/alarm-connection-source-proof-20261106/result.json')
    assert cold['files']==m['files']and cold['archive_sha256']==build['archive_sha256']and cold['ancestor_git_unavailable']and not cold['original_inputs']
    archive=load('build/alarm-connection-candidate-20261106/archive/result.json')
    assert archive['archive_sha256']==r['expected_archive_sha256']==build['archive_sha256']==sha(root/'archive/PCPLUSSE.ZIP')
    guard=load('docs/validation/aspect-alarm-unwind.json')
    for n,h in guard['products'].items():assert m['files'][n]==h,n
    sync=load('build/bbs-lab/results/synchronet/alarm-unwind-funded-sync-20261106/proxy-integration.json','product_inputs')
    assert sync['binary_sha256']==m['files']['TERMINAL.EXE']and sync['interpreter_sha256']==m['files']['ASPECT.EXE']
    assert all(sync['checks'].values())and len(sync['checks'])==25 and sync['external_viewer']['passed']
    carrier=load('build/bbs-lab/results/enigma/alarm-unwind-funded-carrier-20261106/carrier-checks.json')
    assert all(carrier['checks'].values())and carrier['transfer_wait_ms']==150000
    audit=load('build/alarm-unwind-funded-carrier-audit-20261106/result.json')
    assert audit['exact_retry_bytes']==65539
    for n in ('TERMINAL.EXE','ASPECT.EXE','ASPCOMP.EXE'):assert audit['products'][n]['sha256']==m['files'][n]
    for n,h in audit['captures'].items():assert sha(ROOT/n)==h,n;receipts[n]=h
    tests=[]
    for name in ('chat','splash','setup','precompile'):
        folder=ROOT/('build/alarm-package-'+name+'-final-20261106')
        t=load(str(folder.relative_to(ROOT))+'/result.json')
        assert t['package_files']==m['files']and t['package_manifest_sha256']==sha(root/'package/manifest.json')
        assert(t['cpu'],t['port'],t['irq'])==('8086',3,5)
        assert t['chat_help']==(name=='chat')and t['bios_port_omitted']==(name in ('chat','precompile'))
        assert t['precompiled_before_terminal']==t['packaged_ASPECT_clock_alarm_exercised']==(name=='precompile')
        assert set(t['private_fixture_sha256'])=={'PCPLUS.'+x for x in ('PRM','DIR','KEY','KBD','XLT','FON')}
        for n,h in t['private_fixture_sha256'].items():assert sha(folder/'drive/PCPLUS'/n)==h,n
        for n,h in t['artifacts'].items():assert sha(folder/n)==h,n;receipts[str((folder/n).relative_to(ROOT))]=h
        tests.append(dict(case=name,checks=t['checks'],private_files=t['private_fixture_sha256'],packaged_new_commands=t['packaged_ASPECT_clock_alarm_exercised']))
    sources['standalone/record_alarm_connection_release.py']=sha(Path(__file__))
    result=dict(passed=True,software_acceptance=True,physical_acceptance=False,selected=False,installed=False,
                files=m['files'],archive_sha256=archive['archive_sha256'],archive_bytes=archive['archive_bytes'],
                sources=sources,receipts=receipts,DOS_tests=tests,
                summary=dict(public_files=13,cold_source_files=cold['source_count'],launch_tests=4,parent_capability=19,
                             BBS_servers=['Enigma','Synchronet'],Enigma_exact_retry_bytes=65539,
                             application_source_commit=m['source_base_commit'],package_source_commit=cold['source_commit']),
                limitations=['Dummy-UART DOS package tests preserve synthetic private files, not actual machine settings; physical Boca/SIP/audio/CTS and hardware runtime acceptance remain unverified.',
                             'Fresh BBS gates use isolated stock servers through staged SynthModem Telnet code. No physical adapter/DSP/analog or production BBS changes.',
                             'Archive and all five executables reproduce from2471 public files with no originals, prior objects, private config or Git ancestry. The recipe explicitly selects the new profile; the installed selector remains unchanged.',
                             'Separate full original feature inventory remains open. This receipt does not authorize a full-parity claim or itself select/deploy a release.'],
                scope=__doc__+' Matched source-built parent/interpreter/compiler, Chat and native Help companions; all13 application files/ZIP exact. Four DOS8086 launch workflows include packaged DATE/TIME/ALARM and BIOS-unlisted COM3/IRQ5. Magenta special-edition splash and Chat/Help return are observed. Six private file types remain byte-identical.')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS ALARM connection software package and fresh BBS gates')


if __name__=='__main__':main()
