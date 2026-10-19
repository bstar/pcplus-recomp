#!/usr/bin/env python3
"""Actual parent STATUS through SET WHENCASE and ASIOv4, never a renderer stub.
--prepare freezes source/row predictions without product execution or rebuilding.
"""
import argparse
import inspect
import json
import re
import struct
import subprocess
import sys
from pathlib import Path
import test_aspect_renderer_dos as renderer

ROOT=renderer.ROOT
OUT=ROOT/'build/aspect-status-dos'


def definitions():
    fixture=json.loads((ROOT/'standalone/fixtures/status_formatter_vectors.json').read_text())
    fmt=bytes.fromhex(next(c for c in fixture['cases'] if c['name']=='normal')['format_hex'])
    header=renderer.ESC+b'[2J'+renderer.ESC+b'[HFIRST BYTE SAFE'+renderer.QUERY+renderer.DA+b'LOGIN:'
    cases=[]
    for name,settings,value,profile in [
        ('WHENCASE-on-ANSI','set whencase on\n',1,6),
        ('WHENCASE-off-ANSI','set whencase on\nset whencase off\n',0,6),
        ('WHENCASE-repeat-ANSI','set whencase on\nset whencase off\nset whencase on\n',1,6),
        ('WHENCASE-on-VT220','set whencase on\n',1,4),
    ]:
        source=('proc main\nwaitfor "LOGIN:" 5\n'+settings+
                'pause 1\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendproc\n')
        emulation=b'ANSI' if profile==6 else b'VT220'
        rows=[]
        for carrier in [b'OFF-LINE',b'ON-LINE ']:
            text=fmt%(b'LOGIN.ASX',emulation,ord('F'),b'38400',ord('N'),8,1,b'CLOSED ',b'FF',carrier)
            assert len(text)==81
            row=bytearray()
            for index,byte in enumerate(text):row.extend((byte,0x1e if 1<=index<=14 else 0x1f))
            rows.append(bytes(row))
        cases.append(dict(name=name,source=source,banner=header,success=True,
                          screen=[(0,0,'FIRST BYTE SAFE')],post=renderer.QUERY,
                          post_reply=renderer.ESC+b'[1;22R',profile=profile,
                          when_value=value,expected_status_rows=rows,
                          carrier_scope='Two predeclared native carrier labels; observer does not read destructive UART MSR. Physical DCD correlation is outside this test.'))
    return cases


def encode(value):
    if isinstance(value,bytes):return {'hex':value.hex()}
    if isinstance(value,(list,tuple)):return [encode(v) for v in value]
    if isinstance(value,dict):return {k:encode(v) for k,v in value.items()}
    return value


def run_product():
    source=inspect.getsource(renderer.main)
    old="expectations=[{k:(v.hex() if isinstance(v,bytes) else v) for k,v in c.items()} for c in cases]"
    assert source.count(old)==1;source=source.replace(old,'expectations=encode(cases)')
    old='payload=bytearray(directory());'
    assert source.count(old)==1
    source=source.replace(old,"payload=bytearray(directory(profile=case['profile']));")
    old="settings=bytearray(prm());extra=' /A:NETWORK'"
    new="settings=bytearray(prm());struct.pack_into('<H',settings,0x1d18-0x1b84,case['profile']);extra=' /A:NETWORK'"
    assert source.count(old)==1;source=source.replace(old,new)
    old="files=files,banner=case['banner'],working_drive='d',observer='RENDER')"
    new="files=files,banner=case['banner'],working_drive='d',observer='RENDER',profile=case['profile'])"
    assert source.count(old)==1;source=source.replace(old,new)
    scope=dict(renderer.__dict__);scope.update(__file__=__file__,OUT=OUT,definitions=definitions,encode=encode)
    def labelled_adapter():
        previous=renderer.OUT;renderer.OUT=scope['OUT']
        try:return renderer.adapter()
        finally:renderer.OUT=previous
    def status_observer(offsets):
        previous=renderer.OUT;renderer.OUT=scope['OUT']
        try:
            _,modes,pairs,snapshots=renderer.observer(offsets)
            child_map=(ROOT/'build/aspect-runner/ASPECT.map').read_text()
            group=int(re.search(r'DGROUP\s+([0-9a-fA-F]{4}):0000',child_map)[1],16)
            def child_word(name):
                m=re.search(r'^\s*([0-9a-fA-F]{4}):([0-9a-fA-F]{4,8})[+*]?\s+'+re.escape(name)+r'$',child_map,re.M)
                assert m,name
                return int(m[1],16)*16+int(m[2],16)-group*16
            psp=child_word('__psp');opcode=child_word('_runtime_last_opcode')
            when=child_word('_runtime_when_case_sensitive')
            path=renderer.OUT/'observer.asm';asm=path.read_text()
            assert asm.count('sample_end:')==1
            asm=asm.replace('sample_end:', 'status_samples: dw 0\nstatus_parent_duplex: dw 0\nstatus_profile: dw 0\nstatus_attribute: dw 0\nstatus_when: dw 0\nstatus_row: times 162 db 0\nsample_end:')
            hook=f'''timer:
 save
 cld
 cmp word [cs:exec_seen],1
 jne .status_done
 cmp word [cs:exec_done],0
 jne .status_done
 mov ax,ss
 mov es,ax
 cmp ax,{group+16}
 jb .status_done
 sub ax,{group+16}
 cmp ax,[es:{psp}]
 jne .status_done
 push es
 mov es,ax
 cmp word [es:0],0x20cd
 pop es
 jne .status_done
 cmp word [es:{opcode}],0x88
 jne .status_done
 inc word [cs:status_samples]
 mov ax,[es:{when}]
 mov [cs:status_when],ax
 mov ax,[cs:parent_ds]
 mov es,ax
 mov ax,[es:{offsets['modes_value_1d1a']}]
 mov [cs:status_parent_duplex],ax
 mov ax,[es:{offsets['csi_terminal_id']}]
 mov [cs:status_profile],ax
 mov ax,[es:{offsets['ui_flow_attribute']}]
 mov [cs:status_attribute],ax
 mov ax,0xb800
 mov es,ax
 mov si,3840
 mov di,status_row
 mov cx,162
.status_byte:
 mov al,[es:si]
 mov [cs:di],al
 inc si
 inc di
 loop .status_byte
.status_done:
'''
            assert asm.count('timer:\n save\n cld\n')==1
            asm=asm.replace('timer:\n save\n cld\n',hook);path.write_text(asm)
            subprocess.run(['nasm','-fbin',str(path),'-o',str(renderer.OUT/'RENDER.COM')],check=True)
            return (renderer.OUT/'RENDER.COM').read_bytes(),modes,pairs,snapshots
        finally:renderer.OUT=previous
    scope.update(adapter=labelled_adapter,observer=status_observer)
    exec(compile(source,__file__,'exec'),scope)
    scope['main']()
    output=scope['OUT'];report=json.loads((output/'checks.json').read_text())
    cases={c['name']:c for c in definitions()}
    for result in report['cases']:
        case=cases[result['case']];folder=output/result['case'];raw=(folder/'RENDER.BIN').read_bytes()
        samples,duplex,profile,attribute,when=struct.unpack_from('<5H',raw,len(raw)-172)
        row=raw[-162:];checks=result['checks']
        checks.update(actual_child_PAUSE_status_observed=samples>0,
                      native_status_row_exact=row in case['expected_status_rows'],
                      fourteen_label_attributes=row[3:30:2]==bytes([0x1e])*14,
                      eighty_first_native_cell=row[160:162]==b' \x1f',
                      parent_duplex_unchanged=duplex==0,
                      parent_profile_retained=profile==case['profile'],
                      parent_ui_attribute_retained=attribute==0x1e,
                      SETWHENCASE_value=when==case['when_value'])
        result.update(status_samples=samples,status_row_hex=row.hex(),
                      status_characters=row[::2].decode('cp437'),
                      status_parent_duplex=duplex,passed=all(checks.values()))
        (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    report.update(passed=all(c['passed'] for c in report['cases']),
                  reused_renderer_checker_sha256=renderer.sha(Path(renderer.__file__)),
                  status_fixture_sha256=renderer.sha(ROOT/'standalone/fixtures/status_formatter_vectors.json'),
                  scope='Actual product parent native status via child SETWHENCASE ASIOv4 STATUS, passive child-PSP/DS=SS/PAUSE-qualified VRAM observer, full parent queries/history and owner restoration. DCD label alternatives are frozen; destructive MSR reads are not injected. DISPLAY and direct STATUS override/invalid-client calls are untested.')
    (output/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print('STATUS product',len(report['cases']),'cases',sum(len(c['checks']) for c in report['cases']),'checks',report['passed'])
    return 0 if report['passed'] else 1


if __name__=='__main__':
    if '--prepare' in sys.argv:
        parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');parser.add_argument('--label',required=True);args=parser.parse_args()
        assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
        folder=OUT/args.label;folder.mkdir(parents=True,exist_ok=False)
        cases=definitions()
        for case in cases:renderer.compile_source(case['source'])
        (folder/'predictions.json').write_text(json.dumps(encode(cases),indent=2)+'\n')
        print('Prepared',len(cases),'STATUS cases; no product execution or build')
    else:raise SystemExit(run_product())
