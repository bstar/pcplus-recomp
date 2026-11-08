#!/usr/bin/env python3
"""Actual DOS8086 same-process Chat mode changes through the production settings child."""
import argparse,json,re,shutil,struct,sys
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
from build_path_session import ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('terminal','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--editor',type=Path,required=True)
    p.add_argument('--to-mode',type=int,choices=[0,1,255],required=True)
    p.add_argument('--mode',type=int,choices=[0,1,255],required=True)
    a=p.parse_args();binary,out=a.terminal.resolve(),a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    m=json.loads(binary.with_name('manifest.json').read_text());assert m['experimental_chat_send_mode'] and m['chat_loader']['module']['api_version']==0x107
    assert sha(binary)==m['binary_sha256']
    names=['standalone/test_chat_send_mode_live_dos.py','standalone/test_connection_dos.py',
           'standalone/directory_fixtures.py','standalone/modem_fixtures.py',
           'standalone/terminal_config_fixtures.py','standalone/test_terminal.py',
           'standalone/directory_test_support.py','standalone/build_path_session.py']
    sources={**m['sources'],**{n:sha(ROOT/n) for n in names}}
    assert all(sha(ROOT/n)==h for n,h in sources.items())
    out.mkdir();stage=out/'program';stage.mkdir()
    shutil.copyfile(binary,stage/'TERMINAL.EXE');shutil.copyfile(binary.parent/'PCCHAT.OVL',stage/'PCCHAT.OVL')
    name=out.name+'-main';assert re.fullmatch('[A-Za-z0-9_-]+',name)
    capture=ROOT/'build/connection-dos'/name;assert not capture.exists()
    settings=bytearray(prm(port=3,baud=5))
    for off,value in [(0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),
                      (0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0)]:
        struct.pack_into('<H',settings,off,value)
    harness.BINARY=stage/'TERMINAL.EXE'
    settings[0x1f2]=a.mode;settings[0x1f3]=0xa7
    editor=a.editor.resolve();em=json.loads(editor.with_name('manifest.json').read_text())
    assert em['experimental_chat_mode'] and em['field_count']==52 and sha(editor)==em['binary_sha256']
    sources.update(em['sources']);assert all(sha(ROOT/n)==h for n,h in sources.items())
    shutil.copyfile(editor,stage/'PRMEDIT.EXE')
    expected_settings=bytearray(settings);expected_settings[0x1f2]=a.to_mode
    editor_keys='a-f10 p1000 pgdown '+('tab p100 '*15)+'home del del del '+' '.join(str(a.to_mode))+' f10 p300 escape p500 space p1200 '
    keys='p900 enter p5000 a-o p1500 P p120 I p120 N p120 G p1700 escape p700 '+editor_keys+'a-o p1500 L p120 I p120 V p120 E p1700 escape p700 a-o p1500 S p120 E p120 N p120 D p120 enter p1800 escape p800 N p120 O p120 R p120 M p120 A p120 L p1200 a-x'
    triggers=[(b'SEND\r',[(0,b'CHAT-REMOTE\xf0\x1b[6n')]),(b'NORMAL',[(0,b'BACK\x1b[6n')])]
    r=harness.run(name,'success',keys,prm=bytes(settings),prm_expected=bytes(expected_settings),com=3,irq=5,cpu='8086',
        working_drive='d',timeout=45,
        online_triggers=triggers)
    wire=(capture/'serial.bin').read_bytes();screen=(capture/'SCREEN.BIN').read_bytes()[::2]
    replies=re.findall(rb'\x1b\[\d+;\d+R',wire)
    checks=dict(harness=r['passed'],all_real_peer_triggers=r['checks']['online_triggers_sent'],
        exact_two_CPR=len(replies)==2,chat_submission=b'SEND\r' in wire,
        partial_line_policy=((b'PING' in wire)==(a.mode==0)),
        changed_mode_applied_before_second_Chat=(b'LIVESEND\r' in wire if a.to_mode==0 else b'LIVE' not in wire),
        editor_unchanged=sha(stage/'PRMEDIT.EXE')==em['binary_sha256'],
        ordinary_keys_resume=b'NORMAL' in wire,chat_underlay_restored=b'CHAT-REMOTE' not in screen,
        ordinary_RX_after_chat=b'BACK' in screen,
        unchanged_sources=all(sha(ROOT/n)==h for n,h in sources.items()),
        unchanged_module=sha(stage/'PCCHAT.OVL')==m['chat_loader']['module']['binary_sha256'])
    report=dict(passed=all(checks.values()),checks=checks,binary_sha256=sha(binary),
                mode=a.mode,to_mode=a.to_mode,editor_sha256=em['binary_sha256'],
                sources=sources,CPR_replies=[x.hex() for x in replies],
                capture=str(capture.relative_to(ROOT)),capture_files={str(q.relative_to(ROOT)):sha(q) for q in capture.rglob('*') if q.is_file()},
                scope=__doc__+' Actual Alt-O, imported mode0/1/255; unfinishedPING canceled by Escape before SEND/Enter in a second Chat session. A Chat line over UART triggers raw incoming text/CPR; Chat must not parse/reply to that CPR. Escape restores the underlay; normal typed keys trigger the next actual CPR reply. Ordinary startup supplies first CPR. Full main/normal exit/hardware/settings checks; synthetic modem, no passive TSR, no original executable. Actual Alt-F10 editor changes only PRM01F2, preserves adjacentA7, and returns before the second Chat admission; source UI and native EXEC are real. No Help/direct TEXT, notice/trap/carrier, BBS or physical acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    assert report['passed'],checks
    print('PASS normal DOS8086 Chat entry, BIOS typing, UART RX ownership and ordinary return')


if __name__=='__main__':main()
