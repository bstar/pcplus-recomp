#!/usr/bin/env python3
"""Execute ASPECT KEY dispatch and the real Script owner in the linked terminal.
Only DOS kernel, BIOS and UART boundaries use the existing Script model.
"""
import argparse,hashlib,json,struct
from pathlib import Path
import check_transport as transport
ROOT=transport.ROOT

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    base=ROOT/'build/terminal-aspect-keys'
    transport.BINARY=base/'TERMINAL.EXE';transport.MAP=base/'terminal.map'
    from check_script_launch_live import Script
    manifest=json.loads((base/'manifest.json').read_text());assert manifest['experimental_aspect_keys']
    sources=dict(manifest['sources'])
    for n in ['standalone/check_meta_aspect_live.py','standalone/check_script_launch_live.py','standalone/check_translation_edit_live.py','standalone/check_translation_reload_live.py','standalone/check_program_actions_live.py','standalone/check_meta_actions_live.py','standalone/check_transport.py','standalone/check_process.py','standalone/dos_image.py']:
        path=ROOT/n;sources[n]=hashlib.sha256(path.read_bytes()).hexdigest()
    for n,h in sources.items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==h,n
    cases=[]
    def model():
        m=Script();m.install_program_name();m.child_status=0;m.put('connection_state',6);return m
    def filename(m):return bytes(m.uc.mem_read(m.symbols['_command_menu_script'],64))
    def record(m,text,index=0,terminated=True):m.record(index,text,kind=0,terminated=terminated)
    def done(name,count):cases.append(dict(case=name,inputs=count,passed=True));print(name,count,flush=True)
    for index in range(10):
        m=model();p=('TEST'+str(index)+'.ASX').encode();record(m,p,index)
        m.keys.append((0x78+index)<<8);m.poll()
        assert not m.children and m.get('terminal_program_pending')==1 and m.get('terminal_program_kind')==4
        assert filename(m).split(b'\0',1)[0]==p and not m.tx
        m.safe();m.restored();assert len(m.children)==1 and m.get('terminal_program_status')==4
        child=m.children[0];assert child['path']==b'D:\\APP\\ASPECT.EXE' and child['tail'].startswith(b' '+p+b' /S1:')
        assert not m.get('terminal_quit') and not m.get('terminal_macro_active')
    done('all-ten-BIOS-Alt-digit-bindings-defer-direct-ASPECT-until-safe-point',10)
    for p in [b'',b'Q'*52]:
        m=model();before=filename(m);record(m,p,terminated=not p)
        assert m.start()==(3 if p else 0)
        assert filename(m)==before and not m.children and not m.get('terminal_program_pending') and not m.tx
    done('empty-native-noop-and-unterminated-text-atomic-rejection',2)
    for p in [b'test',b'TEST.ASP',b'D:\\SCRIPTS\\TEST.ASX',b'D:TEST.ASX',b'\\TEST.ASX',b'D:\\'+b'ABCDEFGH\\'*4+b'TEST1234.ASX']:
        m=model();record(m,p);assert m.start()==0 and not m.children
        m.safe();m.restored();assert len(m.children)==1 and m.get('terminal_program_status')==4
        assert m.children[0]['tail'].startswith(b' '+p+b' /S1:')
    done('bare-ASP-ASX-relative-rooted-and-full51byte-filename-staging',6)
    for name in ['uart_break_hold','terminal_controller_active','terminal_monitor_active','terminal_macro_active','terminal_program_pending','terminal_program_active']:
        m=model();record(m,b'TEST.ASX');before=filename(m);m.put(name,1)
        assert m.start()==4 and filename(m)==before and not m.children and not m.tx
    done('existing-owner-refusals-leave-shared-script-filename-unchanged',6)
    for key in [27,0x2d00,0x2300,0x2000]:
        m=model();record(m,b'TEST.ASX');assert m.start()==0;m.keys.append(key);m.poll()
        assert not m.get('terminal_program_pending') and not m.children
    done('pending-Escape-exit-hangup-redial-cancel-before-EXEC',4)
    for p in [b'CON.ASX',b'..\\TEST.ASX',b'TEST.ASX /P',b'TEST.ASX\r',b'TEST;BAD',b'LONGNAME9.ASX']:
        m=model();record(m,p);assert m.start()==0;m.keys.append(32);m.safe();m.restored()
        assert not m.children and m.get('terminal_program_status')==5 and not m.get('terminal_quit')
    done('invalid-device-traversal-arguments-control-and-component-rejected-before-EXEC',6)
    for failure in ['missing','nonzero','memory']:
        m=model();record(m,b'TEST.ASX')
        if failure=='missing':m.exec_error=2
        elif failure=='nonzero':m.child_status=7
        else:m.resize_error=8
        assert m.start()==0;m.keys.append(32);m.safe();m.restored()
        assert m.get('terminal_program_status')==5 and not m.get('terminal_quit')
    done('missing-helper-child-error-and-memory-failure-restore-parent',3)
    for mode in (0,1,2):
        m=model();record(m,b'TEST.ASX');m.put('terminal_translation_mode',mode)
        m.put('terminal_translation_enabled',int(mode==1));m.put('uart_rx_mask',127 if mode==2 else 255)
        m.handback=b'\0\x80\xffTAIL';assert m.start()==0;m.safe();m.restored()
        assert m.get('uart_rx_count')==len(m.handback)
        assert bytes(m.uc.mem_read(m.symbols['uart_rx_buffer'],len(m.handback)))==m.handback
        assert m.get('terminal_program_status')==4 and not m.get('terminal_quit')
    done('serial-handback-preserves-binary-suffix-and-three-translation-policies',3)
    assert hashlib.sha256(transport.BINARY.read_bytes()).hexdigest()==manifest['binary_sha256']
    result=dict(passed=True,inputs=sum(c['inputs'] for c in cases),cases=cases,sources=sources,binary_sha256=manifest['binary_sha256'],
        scope='Linked optional ASPECT KEY action and existing Script safe-point owner. DOS/BIOS/UART boundaries modeled; no product callback replaced. Child interpreter, real DOS, modern BBS and physical hardware need separate evidence; HOOK remains unsupported.')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS',result['inputs'],'linked inputs')
if __name__=='__main__':main()
