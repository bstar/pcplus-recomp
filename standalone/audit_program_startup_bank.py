#!/usr/bin/env python3
"""Bind pure startup-code relocation, ABI results and measured code capacity."""
import argparse,json,re,shutil
from pathlib import Path
from audit_aspect_transmit_wait import ROOT,sha,read


def extent(path,name):
    line=next(l for l in path.read_text().splitlines() if l.startswith(name+' '))
    fields=line.split();return int(fields[-2].split(':')[1],16)+int(fields[-1],16)


def body(path,banked):
    text=path.read_text();label='terminal_program_initialize_far:' if banked else 'terminal_program_initialize:'
    text=text.split(label,1)[1].split('; AX near stored command',1)[0]
    lines=[l.split(';',1)[0].strip() for l in text.splitlines()]
    return '\n'.join(l for l in lines if l and not l.startswith(('SEGMENT ','global ')))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','fixed','source-proof','program','cohort','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();old=read(a.baseline/'checks.json');new=read(a.fixed/'checks.json')
    assert old['passed'] and new['passed'] and not old['banked'] and new['banked']
    for r in (old,new):
        assert len(r['cases'])==8 and all(c['passed'] for c in r['cases'])
        assert {(c['product'],c['flags']) for c in r['cases']}=={(n,f) for n in ('terminal','terminal-mouse') for f in (2,0x202,0x402,0x602)}
    before=body(a.baseline/'inputs/src/terminal/program_actions.asm',False)
    after=body(a.fixed/'inputs/src/terminal/program_actions.asm',True)
    assert before.count('pop ax\nret')==1 and before.replace('pop ax\nret','pop ax\nretf',1)==after
    assert sha(a.fixed/'inputs/src/terminal/program_actions.asm')==sha(ROOT/'src/terminal/program_actions.asm')
    assert sha(a.baseline/'inputs/standalone/check_program_startup_bank.py')==old['checker_sha256']
    assert sha(a.fixed/'inputs/standalone/check_program_startup_bank.py')==new['checker_sha256']==sha(ROOT/'standalone/check_program_startup_bank.py')
    capacity={}
    for product in ('terminal','terminal-mouse'):
        for r,folder in ((old,a.baseline),(new,a.fixed)):
            assert sha(folder/(product+'.EXE'))==r['products'][product]
        assert old['products'][product]!=new['products'][product]==sha(ROOT/'build'/product/'TERMINAL.EXE')
        old_spare=65536-extent(a.baseline/(product+'.map'),'_TEXT');new_spare=65536-extent(a.fixed/(product+'.map'),'_TEXT')
        assert new_spare-old_spare==164
        manifest=read(ROOT/'build'/product/'manifest.json');assert manifest['memory_layout']['near_spare_bytes']==(112 if product=='terminal' else 64)
        capacity[product]=dict(near_code_spare_before=old_spare,near_code_spare_after=new_spare,bytes_freed=164,near_data_spare=manifest['memory_layout']['near_spare_bytes'])
    proof=read(a.source_proof);assert proof['passed'] and proof['original_inputs']==[] and len(proof['products'])==26
    assert all(v['actual']==v['expected'] for v in proof['products'].values())
    for product in ('terminal','terminal-mouse'):assert proof['products'][product+'/TERMINAL.EXE']['actual']==new['products'][product]
    for name,digest in proof['sources'].items():assert sha(ROOT/name)==digest,name
    program=read(a.program);assert program['passed'] and program['inputs']==60 and program['binary_sha256']==new['products']['terminal']
    cohort=a.cohort.resolve();output=a.output.resolve();assert cohort.is_relative_to(ROOT/'build') and not cohort.exists()
    assert output.is_relative_to(ROOT/'docs/validation') and not output.exists();cohort.mkdir()
    for item in (a.baseline.resolve(),a.fixed.resolve(),a.source_proof.resolve().parent,a.program.resolve(),Path(__file__)):
        target=cohort/item.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
        if item.is_dir():shutil.copytree(item,target)
        else:shutil.copy2(item,target)
    files={str(f.relative_to(cohort)):sha(f) for f in cohort.rglob('*') if f.is_file()};(cohort/'files.json').write_text(json.dumps(files,indent=2)+'\n')
    result=dict(passed=True,startup_placement_component_accepted=True,full_application_accepted=False,physical_hardware_accepted=False,baseline_products=old['products'],products=new['products'],capacity=capacity,linked_ABI_cases=8,existing_PROGRAM_inputs=60,source_products=26,
        cohort=str(cohort.relative_to(ROOT)),files_manifest_sha256=sha(cohort/'files.json'),auditor_sha256=sha(Path(__file__)),
        scope='Pure startup retention body moved from _TEXT to CONFIG_CODE behind a stable near/far wrapper. Source instruction sequence is identical except outer RET becomes RETF. Normal/mouse linked ABI, IF/DF, stack canary, retained-size and DS=SS checks, 60 existing linked PROGRAM inputs and 26 original-free product rebuilds pass. This is limited code headroom, not a complete placement/memory solution. Current DOS/BBS/audio and physical/full F01-F16 requirements remain separate.')
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,capacity=capacity)))


if __name__=='__main__':main()
