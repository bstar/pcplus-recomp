#!/usr/bin/env python3
"""Bind interactive accepted state, UART traces, component gates and clean builds."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
from terminal_memory import inspect_terminal_memory

ROOT=Path(__file__).resolve().parents[1]
FIELDS=[('_terminal_register_owner',1734),('terminal_baseline_storage',1272),('terminal_configuration_values',44),
        ('terminal_modem_settings',368),('_terminal_transfer_preferences',66),('terminal_keymap',948),
        ('terminal_translation_table',256),('_terminal_sound_enabled',2),('_terminal_hook_completed_status',2),
        ('terminal_translation_mode',2),('terminal_translation_enabled',2),('uart_rx_mask',2),('csi_terminal_id',2),
        ('uart_previous_irq_offset',2),('uart_previous_irq_segment',2)]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def seal(raw,token):
    value=token
    for byte in raw:value=(((value<<1)|(value>>15))&65535)^byte
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--proof',type=Path,required=True)
    parser.add_argument('--register-prefix',required=True)
    args=parser.parse_args()
    base=ROOT/'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers-controls-return-execute-modem-input-apply'
    binary=sha(base/'TERMINAL.EXE');sources,custody={},{}
    def collect(report):
        for name,digest in report['sources'].items():
            assert name not in sources or sources[name]==digest,name
            assert sha(ROOT/name)==digest,name
            sources[name]=digest
    def capture(path):
        assert path.resolve().is_relative_to(ROOT/'build')
        custody[str(path.relative_to(ROOT))]=sha(path)
    def artifacts(folder):
        for path in folder.rglob('*'):
            if path.is_file():capture(path)
    for folder in [base,base.with_name(base.name+'-inputprobe'),base.with_name(base.name+'-hookprobe')]:
        manifest=read(folder/'manifest.json');assert manifest['experimental_hook_apply']
        assert sha(folder/'TERMINAL.EXE')==manifest['binary_sha256'];collect(manifest)
        for name in ['TERMINAL.EXE','terminal.map','manifest.json','hook_apply.obj','hook_launch.obj']:capture(folder/name)
    listing=(base/'terminal.map').read_text()
    symbols={name:(int(seg,16),int(off,16))for seg,off,name in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
    layout=inspect_terminal_memory(base/'TERMINAL.EXE',base/'terminal.map');sizes={s['name']:s['bytes']for s in layout['code_segments']}
    assert layout['near_bytes']==65520
    assert (sizes['_TEXT'],sizes['HOOK_CODE'],sizes['CONFIG_CODE'],sizes['MOUSE_CODE'])==(65052,25108,63776,2900)
    assert '_terminal_hook_input_probe' not in listing
    prior=base.with_name(base.name.removesuffix('-apply'))
    legacy=ROOT/'build/terminal-directory-keys-process-bank-session-capture-projection-bound-registers'
    assert sha(prior/'TERMINAL.EXE')==read(ROOT/'docs/validation/hook-input.json')['terminal_sha256']
    assert sha(legacy/'TERMINAL.EXE')==read(ROOT/'docs/validation/register-bbs.json')['terminal_sha256']
    for folder in [prior,legacy]:collect(read(folder/'manifest.json'));capture(folder/'TERMINAL.EXE');capture(folder/'manifest.json')
    capture(ROOT/'build/hook-apply-prior-builds.log');capture(ROOT/'build/hook-apply-shared-builds.log')
    linked=[]
    for path,count in [('hook-apply-linked-02',40),('hook-apply-input-linked-01',39),('hook-apply-modem-linked-01',3394),
                       ('hook-apply-return-linked-01',4822),('hook-apply-admission-01',152)]:
        report_path=ROOT/'build'/path/'result.json';report=read(report_path)
        assert report['passed'] and report['inputs']==count and report['binary_sha256']==binary
        collect(report);capture(report_path);linked.append(dict(report=str(report_path.relative_to(ROOT)),inputs=count))
    cases=[]
    offline=[(mode,1)for mode in range(13)]+[(mode,2)for mode in [0,4,5,7,8,11,12]]
    online=[(mode,1)for mode in [0,1,3,5,6,10]]+[(mode,2)for mode in [0,5,6]]
    for is_online,rows in [(False,offline),(True,online)]:
        for mode,port in rows:
            label=('online' if is_online else 'offline')+f'-{port}-{mode}'
            folder=ROOT/'build'/('hook-apply-final-'+label);report=read(folder/'result.json')
            assert report['passed'] and report['binary_sha256']==binary and report['mode']==mode and report['port']==port
            assert report['online']==is_online and report['restored_uart_count']==(1 if is_online else 2)
            collect(report);artifacts(folder)
            expected_status={1:107,2:105,3:106,8:408,9:107,10:305}.get(mode,0)
            assert report['status']==expected_status and report['committed']==(expected_status==0)
            header='static const struct {unsigned segment,offset,bytes;} parent_spans[]={\n'+''.join('{%d,%d,%d},\n'%(*symbols[name],size)for name,size in FIELDS)+'};\n'
            assert (folder/'parent_layout.h').read_text()==header
            frames=[(folder/f'B{i}.BIN').read_bytes()for i in range(3)]
            after=[(folder/f'A{i}.BIN').read_bytes()for i in range(3)]
            assert all(len(frame)==2094 for frame in frames+after)
            assert frames[1]==(after[0] if not expected_status else frames[0]) and frames[2]==after[1]==frames[1]
            snapshots=[]
            for index in range(3):
                raw=(folder/f'S{index}.BIN').read_bytes();assert len(raw)==sum(size for _,size in FIELDS)
                at=0;sample={}
                for name,size in FIELDS:sample[name]=raw[at:at+size];at+=size
                snapshots.append(sample)
            for index in [1,2]:
                owner=snapshots[index]['_terminal_register_owner'];phase,token,epoch,checksum=struct.unpack_from('<4H',owner)
                assert phase==0 and epoch==(index if not expected_status else index-1)
                assert owner[904:]==frames[index][:830] and checksum==seal(owner[904:],epoch)
                baseline=snapshots[index]['terminal_baseline_storage'];magic,generation,kind,checksum=struct.unpack_from('<4H',baseline)
                assert magic==0xb451 and generation==(index+1 if not expected_status else index)
                assert kind==(3 if not expected_status or index==2 else 1)
                expected_raw=frames[index][830:] if kind==3 else (folder/'TEST.PRM').read_bytes()
                assert baseline[8:]==expected_raw
                value=0xb41d^generation^kind
                for word in struct.unpack('<632H',baseline[8:]):value=(((value<<1)|(value>>15))&65535)^word
                assert checksum==value
            assert struct.unpack('<H',snapshots[1]['_terminal_hook_completed_status'])[0]==expected_status
            if expected_status:
                for name,_ in FIELDS:
                    if name not in ['_terminal_register_owner','_terminal_hook_completed_status']:
                        assert snapshots[0][name]==snapshots[1][name],(label,name)
            for index in range(3):
                trace=struct.unpack('<13H',(folder/f'H{index}.BIN').read_bytes());raw=frames[index][830:]
                selected,baud=struct.unpack_from('<2H',raw);parity,stop,bits=struct.unpack_from('<3H',raw,4)
                line=[0,8,0x18,0x28,0x38][parity]|(2 if bits==7 else 3)|(0 if stop==1 else 4)
                assert trace[selected*4]==[384,96,48,24,12,6,3,2,1][baud]
                assert trace[selected*4+1]==line and trace[selected*4+3]==0 and not trace[selected*4+2]&2
                irq=struct.unpack_from('<H',raw,0x184+selected*2)[0];assert trace[8]&(1<<irq)
                vector=trace[9:11] if irq==4 else trace[11:13]
                assert vector==tuple(struct.unpack('<H',snapshots[index][name])[0]for name in ['uart_previous_irq_offset','uart_previous_irq_segment'])
            for a,b in ([('BEFORE.BIN','AFTER.BIN')] if is_online else [('BEFORE.BIN','AFTER.BIN'),('BEFORE2.BIN','AFTER2.BIN')]):
                assert (folder/a).read_bytes()==(folder/b).read_bytes() and len((folder/a).read_bytes())==42
            if is_online:
                assert report['peer']['passed'] and all(report['peer']['checks'].values())
                wire=(folder/'serial.bin').read_bytes();assert wire.index(b'observe\r')<wire.rindex(b'\x1b[0n')
            cases.append(dict(mode=mode,port=port,online=is_online,committed=not expected_status,status=expected_status,passed=True))
    combined=[]
    for port in [1,2]:
        folder=ROOT/'build'/f'hook-apply-aspect-01-{port}';report=read(folder/'result.json')
        assert report['passed'] and report['combined_ASPECT'] and report['binary_sha256']==binary
        collect(report);artifacts(folder);combined.append(dict(port=port,passed=True,aspect_sha256=report['aspect_sha256']))
        raw=(folder/'B1.BIN').read_bytes();expected=bytearray((folder/'A0.BIN').read_bytes())
        expected[:20]=bytes(20)
        for i in range(10):expected[20+i*81]=0
        assert raw==expected and (folder/'B2.BIN').read_bytes()==(folder/'A1.BIN').read_bytes()
    component_DOS=[]
    for label,count,probe_suffix in [('hook-apply-input-DOS-01',19,'-inputprobe'),('hook-apply-helper-DOS-01',5,'-hookprobe')]:
        folder=ROOT/'build'/label;report=read(folder/'result.json')
        assert report['passed'] and len(report['cases'])==count and report['binary_sha256']==sha(base.with_name(base.name+probe_suffix)/'TERMINAL.EXE')
        collect(report);artifacts(folder);component_DOS.append(dict(label=label,cases=count,passed=True))
    regressions=[]
    for port in [1,2]:
        for case in ['normal','bad-token','missing-script','missing-helper','divide','budget','abort']:
            label=f'{args.register_prefix}-{port}-{case}';path=ROOT/'build/register-handoff-dos'/label/'result.json'
            report=read(path);assert report['passed'] and report['hook_apply'] and report['cpu']=='8086'
            assert report['parent_sha256']==report['DOS']['binary_sha256']==binary and all(report['DOS']['checks'].values())
            collect(report);capture(path)
            folder=ROOT/'build/connection-dos'/('register-'+label);artifacts(folder)
            for sample in report['snapshots']:
                assert sha(folder/f'OWNER{sample["index"]}.BIN')==sample['owner_sha256']
                assert sha(folder/f'CHILD{sample["index"]}.BIN')==sample['child_sha256']
            regressions.append(dict(port=port,case=case,snapshots=len(report['snapshots']),passed=True))
    proof_path=args.proof.resolve()/'result.json';proof=read(proof_path)
    assert proof['passed'] and proof['original_inputs']==[] and proof['source_files']==712 and len(proof['products'])==7
    for name,digest in proof['products'].items():assert sha(ROOT/name)==digest,name
    assert proof['checker_sha256']==sha(ROOT/'standalone/prove_directory_keys_source.py');collect(proof);capture(proof_path);capture(proof_path.parent/'build.log')
    for name in ['standalone/record_hook_apply.py','docs/HOOK_APPLY.md','standalone/modem_fixtures.py']:sources[name]=sha(ROOT/name)
    result=dict(passed=True,linked_cases=linked,application_workflows=cases,combined_ASPECT=combined,component_DOS=component_DOS,
                register_regressions=regressions,source_files=712,products=proof['products'],terminal_sha256=binary,
                prior_input_sha256=sha(prior/'TERMINAL.EXE'),unchanged_BBS_product_sha256=sha(legacy/'TERMINAL.EXE'),near_bytes=65520,
                resident_code_bytes=65052,hook_code_bytes=25108,config_code_bytes=63776,mouse_code_bytes=2900,
                sources=sources,custody_sha256=custody,
                scope='Supported interactive KEY kind2/PROGRAM helper transaction with actual accepted settings/register/baseline publication. '
                'Offline and synthetic online UART/driver checks, refusal retention and combined ASPECT bank lifetime. '
                'No full native metadata/lookup parity, combined exit/trap gate, new live BBS, physical modem or arbitrary asynchronous fault acceptance.')
    target=args.output.resolve();assert target.is_relative_to(ROOT/'build') or target.is_relative_to(ROOT/'docs/validation')
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(result,indent=2)+'\n')
    print('PASS40 apply;20 offline/9 online;2 combined;14 recovery;712 sources/seven products')


if __name__=='__main__':main()
