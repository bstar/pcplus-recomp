#!/usr/bin/env python3
"""Execute real menu/recorder/owner guards; BIOS/UART/DOS boundaries modeled."""
import hashlib,json,re
from pathlib import Path
from check_recording_foreground_live import Recorder,ROOT,BINARY
from check_recording_rx_live import ordinary
from check_terminal_monitor_live import Monitor


class UI(Monitor,Recorder):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.uc.mem_write(0x484,b'\x18')
        self.call('csi_clear_tabs',[1]);self.call('terminal_clear_home')
        assert self.call('terminal_reset_capture')==0
    def key(self,value):
        self.keys.append(value);self.call('terminal_poll_io',limit=1000000)
    def menu(self):
        self.key(0x2c00);assert self.get('_command_menu_active')
    def choice(self,value):self.menu();self.key(ord(value))
    def text(self):return bytes(self.uc.mem_read(0xb8000,4000))[::2]
    def start_record(self):
        self.choice('C');assert b'Recording file:' in self.text()
        self.key(13);assert not self.get('_command_menu_active') and self.field('state')==1
    def back(self):self.key(27);self.key(27);assert not self.get('_command_menu_active')


def main():
    cases=[]
    def check(name,function):
        function();cases.append(dict(case=name,passed=True));print(name,'PASS',flush=True)

    def save():
        m=UI();m.start_record();ordinary(m,b'Name? ')
        for b in b'bstar':m.key(b)
        m.drain();m.choice('C')
        assert b'Recording saved.' in m.text() and m.field('published')==1
        source=bytes(m.files['PCPLUS.ASP']);assert source.endswith(b'endproc\r\n')
        payload=b''.join(bytes.fromhex(x.decode()) for x in re.findall(rb'^transmitraw "([0-9A-F]*)"\r?$',source,re.M))
        assert payload==b'bstar' and b'waitfor loc_prompt 30' in source
        assert not m.handles;m.back()
    check('menu-start-prompt-user-output-and-save-through-real-file-owner',save)

    def replace():
        m=UI();m.files['PCPLUS.ASP']=bytearray(b'ORIGINAL');m.choice('C');m.key(13)
        assert b'Replace it' in m.text() and m.files['PCPLUS.ASP']==b'ORIGINAL' and not m.handles
        m.key(ord('N'));m.key(ord('C'));m.key(13);m.key(ord('Y'))
        assert m.field('state')==1 and m.files['PCPLUS.ASP']==b'ORIGINAL'
        m.key(ord('x'));m.drain();m.choice('C')
        assert m.files['PCPLUS.ASP']!=b'ORIGINAL' and not any(n.endswith('.BAK') for n in m.files)
    check('existing-target-requires-Y-and-stays-original-until-save',replace)

    def cancel():
        m=UI();m.start_record();m.key(ord('x'));m.drain();m.choice('D')
        assert b'Discard the unpublished' in m.text();m.key(ord('N'));m.back()
        assert m.field('state')==1;m.choice('D');m.key(ord('Y'))
        assert b'Recording canceled' in m.text() and not m.files and not m.handles
    check('cancel-confirmation-decline-and-explicit-discard',cancel)

    def held():
        m=UI();m.put('_terminal_transfer_preferences',1);m.call('_terminal_autostart_input',[ord('*')])
        m.choice('C');m.key(13)
        assert m.field('state')==1 and not m.get('_command_menu_active')
        assert m.state()[128:132]==bytes(4) # Existing keyboard boundary flushed before start.
        assert not m.get('terminal_transfer_pending')
    check('held-invitation-prefix-is-flushed-before-the-record-start-key',held)

    def queue():
        m=UI();m.start_record();m.thre=False;m.key(ord('A'));m.choice('C')
        assert b'pending' in m.text() and m.field('state')==1 and not m.field('published')
        m.thre=True;m.drain();m.back();m.choice('C')
        assert b'Recording saved.' in m.text() and b'transmitraw "41"' in m.files['PCPLUS.ASP']
    check('save-refuses-unsent-output-and-preserves-it-until-UART-acceptance',queue)

    def guards():
        m=UI();m.start_record();before=m.state()
        for name in ('terminal_transfer_start','terminal_upload_start','terminal_monitor_start',
                     'terminal_controller_start','terminal_break_start','terminal_connection_start'):
            m.call(name)
            assert m.state()==before and not m.get('terminal_transfer_pending') and not m.get('terminal_monitor_active')
            assert not m.get('terminal_controller_active') and not m.get('uart_break_hold')
        pointer=m.stage_near(b'TEST.COM\0')
        assert m.call('terminal_program_start',ax=pointer)==2 and not m.get('terminal_program_pending')
        assert m.call('terminal_translation_reload_safe')!=0
        m.call('terminal_script_start');assert not m.get('terminal_program_pending')
        m.put('terminal_option_mask',16);m.uc.mem_write(m.symbols['terminal_config_path'],b'TEST.PRM\0')
        assert m.call('terminal_setup_start')==2 and not m.get('terminal_program_pending')
        m.call('terminal_translation_edit_start');assert not m.get('terminal_program_pending')
        m.call('terminal_connection_cancel');assert m.state()==before
        m.choice('S');assert b'Save or cancel recording' in m.text()
        assert m.state()==before and not m.get('terminal_transfer_pending')
    check('menu-and-root-byte-owner-admission-guards-preserve-recording',guards)

    def recovery():
        m=UI(fault='close');m.start_record();m.choice('C')
        assert b'Close uncertain' in m.text() and m.field('claimed')==1
        before=m.state();calls=len(m.capture_calls)+len(m.fs_calls)
        m.key(ord('U'));m.key(ord('Y'))
        assert m.state()==before and len(m.capture_calls)+len(m.fs_calls)==calls
        assert m.handles and any(n.endswith('.TMP') for n in m.files)
    check('uncertain-close-status-and-explicit-cleanup-do-not-retry-or-delete',recovery)

    def long_path():
        m=UI();m.choice('C')
        for i in range(10):m.key(8)
        path=b'C:\\'+b'ABCDEFGH\\'*6+b'GG.ASP';assert len(path)==63
        for value in path:m.key(value)
        m.key(ord('Z'))
        assert bytes(m.uc.mem_read(m.symbols['_recording_terminal_path'],64))==path+b'\0'
        m.key(13);assert m.field('state')==1 and not m.get('_command_menu_active')
    check('63-byte-filename-editing-bounds-and-terminator',long_path)

    def invalid():
        m=UI();m.choice('C')
        for i in range(10):m.key(8)
        for value in b'CON.ASP':m.key(value)
        m.key(13)
        assert b'no devices' in m.text() and not m.files and not m.handles
    check('invalid-device-path-rejected-before-file-IO',invalid)

    def cleanup():
        m=UI();m.start_record();m.fault='install';m.choice('C')
        assert m.field('stage_owned')==m.field('claimed')==1 and b'LPR00001.TMP' in m.text()
        m.key(ord('U'));assert b'Discard owned scratch' in m.text();m.key(ord('Y'))
        assert not m.field('claimed') and not m.field('stage_owned') and not m.files
        assert m.field('status')==10 and b'Temporary files cleaned.' in m.text() # Preserve original error.
    check('retained-complete-stage-discard-requires-explicit-cleanup-confirmation',cleanup)

    result=dict(passed=True,binary_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),cases=cases,
        test_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope=__doc__)
    (ROOT/'build/terminal/recording-ui-checks.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
