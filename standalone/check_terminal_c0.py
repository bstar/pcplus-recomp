#!/usr/bin/env python3
"""Execute linked C0 dispatch and admitted EOT/ENQ/GS; optional original replay."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn.x86_const import UC_X86_REG_DX,UC_X86_REG_BP,UC_X86_REG_SI,UC_X86_REG_DI
import check_transport as transport
from check_terminal_screen_print_live import ScreenPrint,ExplicitGap
from check_meta_actions_live import ROOT

sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
FIELDS=['screen_cursor_row','screen_cursor_column','screen_video_offset','screen_attribute_offset','csi_wrap_pending']


def machine(mono=1,row=0,column=0):
    m=ScreenPrint();m.put('csi_terminal_id',6);m.put('attributes_monochrome',mono)
    m.uc.reg_write(UC_X86_REG_DX,column);m.call('screen_set_cursor',ax=row)
    return m


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('terminal','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--original',type=Path);p.add_argument('--noise-capture',type=Path)
    a=p.parse_args();out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
    transport.BINARY=a.terminal.resolve();transport.MAP=transport.BINARY.parent/'terminal.map';cases=[]
    manifest=json.loads(transport.BINARY.with_name('manifest.json').read_text())
    assert manifest['memory_layout']['resident_CS_extent_bytes']<65536
    for n,h in manifest['sources'].items():assert sha(ROOT/n)==h,n
    for value in range(32):
        if value==27:continue # ESC is a stream prefix, tested with continuation below.
        m=machine();m.csi(bytes([value]));assert not m.get('terminal_quit')
        cases.append(dict(case='ANSI6-C0',value=value,passed=True))
    m=machine();m.csi(b'\x1b[2;4HZ');assert (m.get('screen_cursor_row'),m.get('screen_cursor_column'))==(1,4)
    cases.append(dict(case='ESC-continuation-retains-CSI',passed=True))
    for mono in (0,1):
        for value in (4,5):
            m=machine(mono,3,9);before=bytes(m.uc.mem_read(0xb8000,4000));m.csi(bytes([value]))
            after=bytes(m.uc.mem_read(0xb8000,4000))
            assert after[2*(3*80+9)]==value if mono else after==before
            assert m.get('screen_cursor_column')==9+mono and not m.tx
            cases.append(dict(case='default-glyph-policy',mono=mono,value=value,passed=True))
        m=machine(mono,3,9);m.csi(b'\x1d')
        assert (m.get('screen_cursor_row'),m.get('screen_cursor_column'))==(3,9-mono)
        cases.append(dict(case='GS-native-left-policy',mono=mono,passed=True))
    for row,column in ((0,0),(3,9),(23,79)):
        m=machine(1,row,column);m.put('terminal_newline_mode_9020',1);m.csi(b'\x05');m.drain()
        assert bytes(m.tx)==bytes((31,column,row))
        cases.append(dict(case='legacy-ENQ-raw-coordinate-report',row=row,column=column,passed=True))
    for value,field,setting,want in [(5,'terminal_c0_enquiry_mode',1,0xe7c),
            (5,'terminal_c0_enquiry_mode',2,0xe7c),(4,'terminal_c0_remote_enabled',1,0x4cd7),
            (29,'terminal_newline_mode_9020',1,0x1292)]:
        m=machine();m.put(field,setting)
        try:m.csi(bytes([value]))
        except ExplicitGap as error:assert error.args==(want,)
        else:raise AssertionError('Unimplemented nondefault mode silently succeeded')
        assert not m.tx and not m.files and not m.children
        cases.append(dict(case='nondefault-remains-explicit',value=value,field=field,setting=setting,passed=True))
    original_cases=[]
    if a.original:
        from compare_input_dispatch_original import OriginalInput
        from compare_render_original import EXPECTED
        image=a.original.read_bytes();assert sha(a.original)==EXPECTED
        for mono in (0,1):
            for value in (4,5,29):
                for row,column in ((0,0),(3,9),(22,79)):
                    m=machine(mono,row,column)
                    # The resident replay's synthetic history lives atE000;
                    # use a bounded ring instead of the application's63KB bank.
                    m.put('terminal_history_end',m.get('terminal_history_start')+512)
                    original=OriginalInput(image,m)
                    original.uc.mem_write(0xb8000,bytes(m.uc.mem_read(0xb8000,4000)))
                    m.csi(bytes([value]));original.character(value)
                    for reg,want in ((UC_X86_REG_BP,0xbabe),(UC_X86_REG_SI,0x1234),(UC_X86_REG_DI,0x5678)):
                        assert m.uc.reg_read(reg)==original.uc.reg_read(reg)==want,(mono,value,'callee register',reg)
                    assert bytes(m.uc.mem_read(0xb8000,4000))==bytes(original.uc.mem_read(0xb8000,4000)),(mono,value,row,column,'video')
                    for field in FIELDS:assert m.get(field)==original.get(field),(mono,value,field)
                    assert not m.tx
                    original_cases.append(dict(mono=mono,value=value,row=row,column=column,passed=True))
    noise=None
    if a.noise_capture:
        data=a.noise_capture.read_bytes();start=data.rfind(b'\x1b[22;0m');end=data.rfind(b'Connection closed by remote host.')
        assert 0<=start<end;fragment=data[start:end];assert b'NO CARRIER' in fragment
        m=machine();m.advance_ticks=True;m.csi(fragment);assert not m.get('terminal_quit')
        noise=dict(path=str(a.noise_capture.resolve().relative_to(ROOT)),sha256=sha(a.noise_capture),bytes=len(fragment),passed=True)
    sources=['standalone/check_terminal_c0.py','standalone/check_terminal_screen_print_live.py',
        'standalone/check_transport.py','standalone/compare_input_dispatch_original.py','standalone/compare_render_original.py']
    result=dict(passed=True,terminal_sha256=sha(transport.BINARY),cases=cases,original_comparisons=original_cases,
        original_sha256=sha(a.original) if a.original else None,noise_capture=noise,
        sources={n:sha(ROOT/n) for n in sources},scope=__doc__+' Actual linked owner/render/left/transport instructions; hardware/DOS modeled. Original comparisons execute unmodified resident default-mode paths. Nondefault answerback/remote evaluator and legacy GS remain explicitly unsupported; no physical or all-emulation claim.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS C0:',len(cases),'linked cases,',len(original_cases),'original comparisons')


if __name__=='__main__':main()
