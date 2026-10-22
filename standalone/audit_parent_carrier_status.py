#!/usr/bin/env python3
"""Audit parent DCD bookkeeping and status against passive DOS captures."""
import argparse,json,shutil,struct
from pathlib import Path
from audit_aspect_abort_carrier import ROOT,sha,read,verify_modem,ESC,QUERY
FIELDS=('parent_seen_in_child','parent_menu_sampled','parent_menu_state','parent_menu_status',
        'parent_loss_seen_after','parent_OFF_LINE_seen_after','parent_status_samples')


def parent_capture(folder,gap):
    report=read(folder/'checks.json')
    assert report['passed'] and report['gap_reproduced']==gap and report['compatibility_accepted']!=gap
    for name,digest in report['inputs'].items():assert sha(folder/'inputs'/name)==digest,name
    for name,digest in report['captures'].items():assert sha(folder/name)==digest,name
    assert sha(folder/'TERMINAL.EXE')==report['parent_sha256']
    assert sha(folder/'ASPECT.EXE')==report['runner_sha256']
    case=folder/'CALL-No';raw=(case/'RENDER.BIN').read_bytes()
    header=struct.unpack_from('<7H',raw)
    assert header[:4]==(0x524e,1,1,1) and header[6]==0
    assert raw[14:34]==raw[34:54] and raw[54:470]==raw[470:886]
    state=dict(zip(FIELDS,struct.unpack('<7H',raw[-14:])))
    assert state==report['observations'] and state['parent_menu_sampled']==1 and state['parent_status_samples']>18
    assert bool(state['parent_seen_in_child'])!=gap
    assert (state['parent_menu_state'],state['parent_menu_status'])==((6,1) if gap else (0,6))
    assert state['parent_loss_seen_after']==state['parent_OFF_LINE_seen_after']==int(not gap)
    before=(case/'BEFORE.BIN').read_bytes();assert len(before)==42 and before==(case/'AFTER.BIN').read_bytes()
    assert (case/'MAIN.OK').read_bytes()==b'DECLINED' and (case/'DCD.OK').read_bytes()==b'FRAME37'
    expected=ESC+b'[1;16R'+ESC+b'[?62;2cKEYREADY'+ESC+b'[1;22R'
    events=read(case/'peer-events.json')
    assert all(a['time']<=b['time'] for a,b in zip(events,events[1:]))
    for kind in ('connected','script-ready','hangup'):assert sum(e['kind']==kind for e in events)==1
    assert (case/'serial.bin').read_bytes()==expected==b''.join(bytes.fromhex(e['hex']) for e in events if e['kind']=='receive')
    sends=[bytes.fromhex(e['hex']) for e in events if e['kind']=='send']
    assert sends==[ESC+b'[2J'+ESC+b'[HFIRST BYTE SAFE'+QUERY+ESC+b'[0cLOGIN:',QUERY]
    query=next(e['time'] for e in events if e['kind']=='send' and e['hex']==QUERY.hex())
    hangup=next(e['time'] for e in events if e['kind']=='hangup');tail=b'';reply=None
    for e in events:
        if e['kind']=='receive' and e['time']>=query:
            tail+=bytes.fromhex(e['hex'])
            if ESC+b'[1;22R' in tail:reply=e['time'];break
    assert reply is not None and 0<=reply-query<=1 and reply<hangup
    screen=(case/'SCREEN.BIN').read_bytes();assert len(screen)==4000
    assert screen[3840+71*2:3840+79*2:2]==(b'ON-LINE ' if gap else b'OFF-LINE')
    log=(case/'dosbox.log').read_text()
    assert log.count('Modem response: NO CARRIER')==1 and 'Modem response: ERROR' not in log
    assert ('Command sent to modem: ->ATH<-' in log)==gap
    return report,dict(observations=state,query_reply_seconds=reply-query,wire_sha256=sha(case/'serial.bin'))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','fixed','model','mouse-model','modem','source-proof','program','confirmation','cohort','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();paths={k:v.resolve() for k,v in vars(a).items()}
    assert paths['output'].is_relative_to(ROOT/'docs/validation') and not paths['output'].exists()
    assert paths['cohort'].is_relative_to(ROOT/'build') and not paths['cohort'].exists()
    old,baseline=parent_capture(paths['baseline'],True);new,fixed=parent_capture(paths['fixed'],False)
    assert old['parent_sha256']!=new['parent_sha256'] and old['runner_sha256']==new['runner_sha256']
    identities={}
    for directory,key in [('terminal','normal'),('terminal-mouse','mouse'),('terminal-process','external')]:
        base=ROOT/'build'/directory;manifest=read(base/'manifest.json')
        assert sha(base/'TERMINAL.EXE')==manifest['binary_sha256']
        for name,digest in manifest['sources'].items():assert sha(ROOT/name)==digest,name
        identities[key]=dict(sha256=manifest['binary_sha256'],data_spare=manifest['memory_layout']['near_spare_bytes'],code_spare=manifest['memory_layout']['resident_code_spare_bytes'])
    assert identities['normal']['sha256']==new['parent_sha256']
    for key,variant in [('model','normal'),('mouse_model','mouse')]:
        r=read(paths[key]);assert r['passed'] and len(r['cases'])==32 and all(c['passed'] for c in r['cases'])
        assert r['parent_sha256']==identities[variant]['sha256']
        for name,digest in r['inputs'].items():assert sha(ROOT/name)==digest,name
    modem,cases=verify_modem(paths['modem'],parent_status=True)
    assert modem['parent_sha256']==new['parent_sha256'] and modem['runner_sha256']==new['runner_sha256']
    proof=read(paths['source_proof']);assert proof['passed'] and proof['original_inputs']==[] and len(proof['products'])==26
    for name,digest in proof['sources'].items():assert sha(ROOT/name)==digest,name
    assert all(row['actual']==row['expected'] for row in proof['products'].values())
    for directory,variant in [('terminal','normal'),('terminal-mouse','mouse'),('terminal-process','external')]:
        assert proof['products'][directory+'/TERMINAL.EXE']['actual']==identities[variant]['sha256']
    assert proof['products']['aspect-runner/ASPECT.EXE']['actual']==new['runner_sha256']
    program=read(paths['program']);assert program['passed'] and len(program['cases'])==13 and program['parent_sha256']==identities['external']['sha256']
    for row in program['cases']:assert row['passed'] and all(row['checks'].values())
    confirmation=read(paths['confirmation']);assert confirmation['passed'] and len(confirmation['results'])==10 and confirmation['parent_sha256']==new['parent_sha256']
    freeze=[paths[k] for k in ('baseline','fixed','modem')]
    freeze += [paths[k].parent for k in ('model','mouse_model','source_proof','program')]
    support={}
    for leaf,count in [('connection-checks.json',8),('status-live-checks.json',85)]:
        path=ROOT/'build/terminal'/leaf;r=read(path)
        assert r['passed'] and len(r['cases'])==count and r['binary_sha256']==new['parent_sha256']
        support[leaf]=count;freeze.append(path)
    terminal_checks=0
    for name in ('normal','software','partial','controller-disabled','break','break-exit'):
        folder=ROOT/'build/terminal-tests'/name;r=read(folder/'result.json')
        assert r['passed'] and all(r['checks'].values()) and r['binary_sha256']==new['parent_sha256']
        terminal_checks+=len(r['checks']);freeze.append(folder)
    # Failed intermediate candidates remain evidence, never accepted captures.
    for relative in ('build/parent-carrier-dos/fixed-01','build/parent-carrier-status/linked-01','build/parent-carrier-status/linked-02'):
        freeze.append(ROOT/relative)
    freeze += [paths['confirmation'],Path(__file__),ROOT/'standalone/audit_aspect_abort_carrier.py',ROOT/'standalone/test_parent_carrier_dos.py',ROOT/'standalone/check_parent_carrier_status.py']
    cohort=paths['cohort'];cohort.mkdir()
    for source in freeze:
        target=cohort/source.relative_to(ROOT)
        if target.exists():continue
        target.parent.mkdir(parents=True,exist_ok=True)
        if source.is_dir():shutil.copytree(source,target)
        else:shutil.copy2(source,target)
    files={str(p.relative_to(cohort)):sha(p) for p in cohort.rglob('*') if p.is_file()}
    (cohort/'files.json').write_text(json.dumps(files,indent=2)+'\n')
    result=dict(passed=True,parent_carrier_status_accepted=True,full_application_accepted=False,
        parent_sha256=new['parent_sha256'],runner_sha256=new['runner_sha256'],variants=identities,
        baseline=baseline,fixed=fixed,linked_groups=64,support_linked_cases=support,modem_cases=cases,
        terminal_DOS_sessions=6,terminal_DOS_checks=terminal_checks,confirmation_DOS_cases=10,attached_PROGRAM_cases=13,
        source_only_products=26,cohort=str(cohort.relative_to(ROOT)),frozen_files=len(files),
        files_manifest_sha256=sha(cohort/'files.json'),auditor_sha256=sha(Path(__file__)),
        scope='Initial DCD high is remembered before automatic script entry. Real DOS virtual-modem TCP loss, native CALL with local37, decline, parent state0/status6, ordinary menu and OFF-LINE refresh are passively observed. Native status sampling defers screen owners; 64 linked groups include modeled DCD/BDA, DS=SS, IF/DF, notice underlay and cache invalidation. Historical baseline keeps identical child. Four actual modem cases, ten confirmation cases and six terminal sessions retain exact wire/cleanup expectations.',
        remaining=['DCD initially low followed by an entire high/low transition inside a child can still escape the parent; late-rise detection is only verified when ordinary polling sees high.',
                   'Ordinary refresh is limited to supported80-column native status geometry; other layouts remain open.',
                   'Full XOFF/XON handback/reconnect, CTS stalls, remaining commands/emulations/protocols, physical hardware and all F01–F16 gates remain open.'])
    paths['output'].write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,linked_groups=64,terminal_DOS_checks=terminal_checks,frozen_files=len(files))))


if __name__=='__main__':main()
