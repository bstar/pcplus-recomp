#!/usr/bin/env python3
"""Bind the logical-stride application change to CPU, DOS and fresh-build evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proof',type=Path,required=True)
    parser.add_argument('--dos',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();base=ROOT/'build/terminal'
    proof=args.proof.resolve();dos=args.dos.resolve()
    assert proof.is_relative_to(ROOT/'build') and dos.is_relative_to(ROOT/'build')
    def read(path):return json.loads(path.read_text())
    manifest=read(base/'manifest.json');binary=sha(base/'TERMINAL.EXE')
    assert binary==manifest['binary_sha256']
    sources=dict(manifest['sources']);reports={};artifacts={}
    for name,digest in sources.items():assert sha(ROOT/name)==digest,name
    for key,leaf,checker in [('kernel','line-metadata-stride-checks.json','check_line_metadata_stride.py'),
        ('attributes','line-attributes-live-checks.json','check_line_attributes_live.py'),
        ('policy','line-edit-live-checks.json','check_line_edit_live.py'),
        ('callbacks','line-callback-live-checks.json','check_line_callbacks_live.py'),
        ('layout','line-controller-layout-checks.json','check_line_controller_layout.py')]:
        path=base/leaf;result=read(path)
        assert result['passed'] and result['binary_sha256']==binary
        checker_path=ROOT/'standalone'/checker;sources[str(checker_path.relative_to(ROOT))]=sha(checker_path)
        if 'checker_sha256' in result:assert result['checker_sha256']==sha(checker_path)
        reports[key]=result;artifacts[str(path.relative_to(ROOT))]=sha(path)
    assert reports['kernel']['cases']==480 and reports['kernel']['width_cases']=={'80':240,'132':240}
    assert reports['kernel']['sources']==manifest['sources']
    assert (reports['attributes']['cases'],reports['attributes']['repair_operations'],reports['attributes']['pre_mutation_rejections'])==(512,192,45)
    assert reports['attributes']['repair_reference_sha256']==sha(ROOT/'standalone/check_attribute_repair.py')
    assert len(reports['policy']['cases'])==8 and all(c['passed']for c in reports['policy']['cases'])
    assert reports['callbacks']['cases']==24 and len(reports['layout']['rejected_mutations'])==45
    rebuilt=read(proof/'result.json');assert rebuilt['passed'] and rebuilt['binary_sha256']==binary
    assert rebuilt['negative_exit_code'] and rebuilt['source_files']==len(rebuilt['sources'])
    for name,digest in rebuilt['sources'].items():
        assert sha(ROOT/name)==sha(proof/'source'/name)==digest,name;sources[name]=digest
    assert sha(proof/'source/build/terminal/TERMINAL.EXE')==binary
    assert sha(proof/'negative-source/standalone/build_terminal.py')==rebuilt['negative_builder_sha256']
    assert sha(proof/'negative-build.log')==rebuilt['negative_log_sha256']
    assert sha(proof/'build.log')==rebuilt['build_log_sha256']
    assert rebuilt['checker_sha256']==sha(ROOT/'standalone/prove_line_metadata_source.py')
    actual=read(dos/'checks.json');assert actual['passed'] and actual['binary_sha256']==binary
    assert all(actual['checks'].values())
    for name,digest in actual['inputs'].items():assert sha(ROOT/name)==digest,name;sources[name]=digest
    raw=(dos/'product/LINEATTR.BIN').read_bytes();assert len(raw)==12216
    assert sha(dos/'product/LINEATTR.BIN')==actual['capture_sha256']
    assert sha(dos/'LATTR.COM')==actual['observer_program_sha256']
    state=struct.unpack_from('<12H',raw);assert tuple(actual['state'])==state
    assert state[:4]==(0x4c41,1,1,0) and state[4]==state[5] and state[6:11]==(1,7,2000,24,79) and state[11]>=3
    flags=bytearray(2000);flags[800]=0x81
    assert raw[24:4120]==bytes(flags)+b'\x55'*2096 and raw[4120:8216]==b'\x07'*2000+b'\x66'*2096
    cells=[0x0720]*2000
    for row,text in [(0,b'FIRST BYTE SAFE'),(1,b'TOP'),(2,b'R2'),(3,b'R4'),(6,b'BOTTOM')]:
        for i,char in enumerate(text):cells[row*80+i]=0x700|char
    assert raw[8216:]==struct.pack('<2000H',*cells)
    assert (dos/'product/BEFORE.BIN').read_bytes()==(dos/'product/AFTER.BIN').read_bytes()
    assert len((dos/'product/BEFORE.BIN').read_bytes())==42
    for folder in [dos]:
        for path in folder.rglob('*'):
            if path.is_file():artifacts[str(path.relative_to(ROOT))]=sha(path)
    for path in [base/'TERMINAL.EXE',base/'manifest.json',base/'terminal.map',proof/'result.json',proof/'build.log',proof/'negative-build.log']:
        artifacts[str(path.relative_to(ROOT))]=sha(path)
    for path in [Path(__file__),ROOT/'standalone/prove_line_metadata_source.py',ROOT/'standalone/check_attribute_repair.py']:
        sources[str(path.relative_to(ROOT))]=sha(path)
    receipt=dict(passed=True,compatibility_complete=False,binary_sha256=binary,near_data_stack_bytes=manifest['data_stack_bytes'],
        kernel_cases=reports['kernel']['width_cases'],linked_attribute_cases=512,linked_field_repairs=192,
        pre_edit_rejections=45,policy_groups=8,callback_cases=24,layout_negative_cases=45,
        actual_DOS_checks=actual['checks'],source_files=rebuilt['source_files'],diagnostic_glob_negative=True,
        sources=sources,artifacts=artifacts,card_written=False,
        scope='Live NETWORK line metadata now uses logical row stride. Actual linked80/132 plane kernel with RX/deferred and full near-state preservation; existing80-column parser/repair/BIOS/DOS and fresh-source reproduction pass. Native width diagnostic remains excluded; live132 admission, video/panes/repair/UI/child/BBS integration, new branded package and physical acceptance remain open.')
    args.output.write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS logical line stride: linked kernel, existing parser/repair, DOS and empty-tree reproduction')


if __name__=='__main__':main()
