#!/usr/bin/env python3
"""Seal live pane binding, actual DOS output and independent fresh-source checks."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--proof',type=Path,required=True);p.add_argument('--dos',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--wide-repair',action='store_true',help='Require the wide repair oracle and DOS field-repaint fixture')
    args=p.parse_args()
    base=ROOT/'build/terminal';proof=args.proof.resolve();dos=args.dos.resolve()
    assert proof.is_relative_to(ROOT/'build') and dos.is_relative_to(ROOT/'build')
    def read(path):return json.loads(path.read_text())
    manifest=read(base/'manifest.json');binary=sha(base/'TERMINAL.EXE')
    assert binary==manifest['binary_sha256'];sources=dict(manifest['sources']);artifacts={};reports={}
    for name,digest in sources.items():assert sha(ROOT/name)==digest,name
    checks=[('viewport','viewport-live-checks.json','check_viewport_live.py'),
        ('attributes','line-attributes-live-checks.json','check_line_attributes_live.py'),
        ('metadata','line-metadata-stride-checks.json','check_line_metadata_stride.py'),
        ('reset','terminal-reset-live-checks.json','check_terminal_reset_live.py'),
        ('callbacks','line-callback-live-checks.json','check_line_callbacks_live.py'),
        ('layout','line-controller-layout-checks.json','check_line_controller_layout.py')]
    for key,leaf,checker in checks:
        path=base/leaf;result=read(path);assert result['passed'] and result['binary_sha256']==binary
        checker_path=ROOT/'standalone'/checker;sources[str(checker_path.relative_to(ROOT))]=sha(checker_path)
        if 'checker_sha256'in result:assert result['checker_sha256']==sha(checker_path)
        reports[key]=result;artifacts[str(path.relative_to(ROOT))]=sha(path)
    viewport=reports['viewport']
    assert (viewport['cursor_transitions'],viewport['parser_output_erase_cases'],viewport['pre_copy_rejections'])==(80,60,186)
    assert viewport['capture_refresh_separate'] and viewport['hardware_callbacks_owned_DS'] and viewport['sources']==manifest['sources']
    assert (reports['attributes']['cases'],reports['attributes']['repair_operations'],reports['attributes']['pre_mutation_rejections'])==(512,192,45)
    assert reports['metadata']['width_cases']=={'80':240,'132':240}
    assert len(reports['reset']['cases'])==7 and all(c['passed']for c in reports['reset']['cases'])
    assert reports['callbacks']['cases']==24 and len(reports['layout']['rejected_mutations'])==45
    wide=None;legacy=None
    if args.wide_repair:
        wide=read(base/'attribute-repair-wide-checks.json');legacy=read(ROOT/'build/attribute-repair/live-checks.json')
        assert wide['passed'] and legacy['passed'] and wide['binary_sha256']==legacy['binary_sha256']==binary
        assert (wide['cases'],wide['pre_mutation_rejections'])==(360,13) and wide['sources']==manifest['sources']
        assert wide['navigation_cases']==84
        assert wide['checker_sha256']==sha(ROOT/'standalone/check_attribute_repair_wide.py')
        assert wide['oracle_sha256']==legacy['reference_sha256']==sha(ROOT/'standalone/check_attribute_repair.py')
        assert wide['fixture_sha256']==sha(ROOT/'standalone/check_viewport_live.py')
        assert legacy['checker_sha256']==sha(ROOT/'standalone/check_attribute_repair_live.py')
        for path in [base/'attribute-repair-wide-checks.json',ROOT/'build/attribute-repair/live-checks.json']:
            artifacts[str(path.relative_to(ROOT))]=sha(path)
        for name in ['check_attribute_repair_wide.py','check_attribute_repair.py','check_attribute_repair_live.py']:
            sources['standalone/'+name]=sha(ROOT/'standalone'/name)
        component_path=ROOT/'build/attribute-repair/checks.json';component=read(component_path)
        component_manifest=ROOT/'build/attribute-repair/manifest.json';control=read(component_manifest)
        assert component['passed'] and component['cases']==1928
        assert component['checker_sha256']==sha(ROOT/'standalone/check_attribute_repair.py')
        assert component['manifest_sha256']==sha(component_manifest)
        for name,digest in control['sources'].items():assert sha(ROOT/name)==digest,name;sources[name]=digest
        for unit in control['units']:
            unit_source=Path(unit['file'])
            path=component_path.parent/(unit_source.parent.name+'-'+unit_source.stem+'.bin')
            assert sha(path)==unit['sha256'];artifacts[str(path.relative_to(ROOT))]=sha(path)
        for path in [component_path,component_manifest]:artifacts[str(path.relative_to(ROOT))]=sha(path)
    reproduction=read(proof/'result.json');assert reproduction['passed'] and reproduction['viewport_passed']
    assert reproduction['checker_sha256']==sha(ROOT/'standalone/prove_line_metadata_source.py')
    assert reproduction['binary_sha256']==binary and reproduction['source_files']==len(reproduction['sources'])
    for name,digest in reproduction['sources'].items():
        assert sha(ROOT/name)==sha(proof/'source'/name)==digest,name;sources[name]=digest
    assert sha(proof/'source/build/terminal/TERMINAL.EXE')==binary
    assert sha(proof/'source/build/terminal/viewport-live-checks.json')==reproduction['viewport_report_sha256']
    assert read(proof/'source/build/terminal/viewport-live-checks.json')==viewport
    if args.wide_repair:
        assert reproduction['wide_repair_passed']
        assert sha(proof/'wide-repair-check.log')==reproduction['wide_repair_log_sha256']
        assert sha(proof/'source/build/terminal/attribute-repair-wide-checks.json')==reproduction['wide_repair_report_sha256']
        assert read(proof/'source/build/terminal/attribute-repair-wide-checks.json')==wide
        artifacts[str((proof/'wide-repair-check.log').relative_to(ROOT))]=sha(proof/'wide-repair-check.log')
    assert sha(proof/'viewport-check.log')==reproduction['viewport_log_sha256']
    assert sha(proof/'build.log')==reproduction['build_log_sha256']
    assert sha(proof/'negative-build.log')==reproduction['negative_log_sha256'] and reproduction['negative_exit_code']
    negative=reproduction['foreign_DS_negative'];assert negative['rejected'] and negative['exit_code']
    assert sha(proof/'foreign-ds-source/build/terminal/TERMINAL.EXE')==negative['binary_sha256']!=binary
    assert sha(proof/'foreign-ds-source/standalone/build_terminal.py')==negative['builder_sha256']
    for name,field in [('foreign-ds-build.log','build_log_sha256'),('foreign-ds-check.log','check_log_sha256')]:assert sha(proof/name)==negative[field]
    assert 'Viewport hardware callback inherited foreign DS'in(proof/'foreign-ds-check.log').read_text()
    actual=read(dos/'checks.json');canonical=read(dos/'product/result.json')
    assert actual['passed'] and canonical['passed'] and actual['binary_sha256']==canonical['binary_sha256']==binary
    assert actual['cpu']==canonical['cpu']=='8086' and all(actual['checks'].values()) and all(canonical['checks'].values())
    assert bool(actual.get('fields'))==args.wide_repair
    for name,digest in actual['inputs'].items():assert sha(ROOT/name)==digest,name;sources[name]=digest
    raw=(dos/'product/LINEATTR.BIN').read_bytes();assert len(raw)==(20408 if args.wide_repair else 12216)
    assert sha(dos/'product/LINEATTR.BIN')==actual['capture_sha256'] and sha(dos/'VPWATCH.COM')==actual['observer_sha256']
    state=struct.unpack_from('<12H',raw);assert list(state)==actual['state']
    assert state[:4]==(0x4c41,1,1,0) and state[4]==state[5] and state[6:11]==(1,7,3168,0,15) and state[11]>=1
    shadow=bytearray(raw[24:8216]);video=raw[8216:12216]
    for row in range(24):shadow[row*264:row*264+160]=video[row*160:row*160+160]
    expected=[0x0720]*3168
    if args.wide_repair:expected[3*132:6*132]=[0x1e20]*(3*132)
    text_row=7 if args.wide_repair else 5
    for row,col,text in [(0,0,b'FIRST BYTE SAFE'),(0,131,b'R'),(text_row,0,b'LEFT'),(text_row,79,b'EF'),(23,131,b'Z')]:
        for i,char in enumerate(text):expected[row*132+col+i]=0x700|char
    expected_bytes=struct.pack('<3168H',*expected)
    assert shadow[:6336]==expected_bytes and shadow[6336:]==b'\x5a\xa5'*928
    assert hashlib.sha256(expected_bytes).hexdigest()==actual['expected_logical_sha256']
    if args.wide_repair:
        flags=bytearray(3168);flags[10*132]=0x81
        values=bytearray(b'\x07'*3168);values[3*132-1:6*132]=b'\x1e'*(3*132+1)
        assert raw[12216:16312]==flags+b'\x55'*928 and raw[16312:]==values+b'\x66'*928
    wire=(dos/'product/serial.bin').read_bytes();assert b'\x1b[24;132R'in wire and b'\x1b[1;16R'in wire
    assert(dos/'product/BEFORE.BIN').read_bytes()==(dos/'product/AFTER.BIN').read_bytes()
    assert len((dos/'product/BEFORE.BIN').read_bytes())==42
    for path in dos.rglob('*'):
        if path.is_file():artifacts[str(path.relative_to(ROOT))]=sha(path)
    for path in [base/'TERMINAL.EXE',base/'terminal.map',base/'manifest.json',proof/'result.json',
        proof/'build.log',proof/'negative-build.log',proof/'viewport-check.log',proof/'foreign-ds-build.log',proof/'foreign-ds-check.log']:
        artifacts[str(path.relative_to(ROOT))]=sha(path)
    for path in [Path(__file__),ROOT/'standalone/prove_line_metadata_source.py',ROOT/'Makefile',ROOT/'standalone/prove_source_build.py']:
        sources[str(path.relative_to(ROOT))]=sha(path)
    receipt=dict(passed=True,compatibility_complete=False,binary_sha256=binary,
        near_data_stack_bytes=manifest['data_stack_bytes'],cursor_transitions=80,parser_output_erase_cases=60,
        pre_copy_rejections=186,hardware_callbacks_owned_DS=True,foreign_DS_negative=negative,
        actual_DOS_checks=actual['checks'],source_files=reproduction['source_files'],original_inputs=[],
        sources=sources,artifacts=artifacts,card_written=False,
        scope='Live static-buffer viewport/cursor/output/erase composition, modeled80/132 display plus realDOS8086 test-only staged132x24 geometry, native BIOS copies and real132-column CPR. Fresh-source same-image oracle and missing-DS-fix counterexample. Peer width requests, general132 field repair/UI/child/BBS and physical acceptance remain open; package/card unchanged.')
    if args.wide_repair:
        receipt.update(wide_repair_cases=360,wide_navigation_cases=84,wide_repair_rejections=13,legacy_repair_cases=legacy['cases'],
            reference_component_cases=1928,
            scope='Owned132-column native field repair now composes with the live viewport;360 oracle cases and13 pre-mutation refusals pass. ActualDOS8086 seeded deleted-field boundary repaints only its region with1Eh, preserves the outside marker and verifies complete planes/guards plus logical video. Fresh-source replay and existing80-column/native consumers pass. Peer width/reset ownership, broader scrolling/UI/child/BBS integration, updated package and physical acceptance remain open; card unchanged.')
    args.output.write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS live viewport binding: cursor/parser, DOS8086, fresh-source replay and foreign-DS negative')


if __name__=='__main__':main()
