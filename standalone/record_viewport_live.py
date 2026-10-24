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
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
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
    reproduction=read(proof/'result.json');assert reproduction['passed'] and reproduction['viewport_passed']
    assert reproduction['checker_sha256']==sha(ROOT/'standalone/prove_line_metadata_source.py')
    assert reproduction['binary_sha256']==binary and reproduction['source_files']==len(reproduction['sources'])
    for name,digest in reproduction['sources'].items():
        assert sha(ROOT/name)==sha(proof/'source'/name)==digest,name;sources[name]=digest
    assert sha(proof/'source/build/terminal/TERMINAL.EXE')==binary
    assert sha(proof/'source/build/terminal/viewport-live-checks.json')==reproduction['viewport_report_sha256']
    assert read(proof/'source/build/terminal/viewport-live-checks.json')==viewport
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
    for name,digest in actual['inputs'].items():assert sha(ROOT/name)==digest,name;sources[name]=digest
    raw=(dos/'product/LINEATTR.BIN').read_bytes();assert len(raw)==12216
    assert sha(dos/'product/LINEATTR.BIN')==actual['capture_sha256'] and sha(dos/'VPWATCH.COM')==actual['observer_sha256']
    state=struct.unpack_from('<12H',raw);assert list(state)==actual['state']
    assert state[:4]==(0x4c41,1,1,0) and state[4]==state[5] and state[6:11]==(1,7,3168,0,15) and state[11]>=1
    shadow=bytearray(raw[24:8216]);video=raw[8216:]
    for row in range(24):shadow[row*264:row*264+160]=video[row*160:row*160+160]
    expected=[0x0720]*3168
    for row,col,text in [(0,0,b'FIRST BYTE SAFE'),(0,131,b'R'),(5,0,b'LEFT'),(5,79,b'EF'),(23,131,b'Z')]:
        for i,char in enumerate(text):expected[row*132+col+i]=0x700|char
    expected_bytes=struct.pack('<3168H',*expected)
    assert shadow[:6336]==expected_bytes and shadow[6336:]==b'\x5a\xa5'*928
    assert hashlib.sha256(expected_bytes).hexdigest()==actual['expected_logical_sha256']
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
    args.output.write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS live viewport binding: cursor/parser, DOS8086, fresh-source replay and foreign-DS negative')


if __name__=='__main__':main()
