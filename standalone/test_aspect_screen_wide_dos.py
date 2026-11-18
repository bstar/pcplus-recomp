#!/usr/bin/env python3
"""Actual DOS screen commands after canonical peer132 activation; passive caches.

No product geometry/field seeding. Existing GET/UART/parser/config/file/return
checks stay active. Checked-HOME activation is recorded separately from HOME0.
"""
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import test_aspect_get_vm_dos as base

ROOT=base.ROOT
ORIGINAL_MAIN=inspect.getsource(base.main)
ORIGINAL_DEFINITIONS=base.definitions
FIELDS=['screen_attribute_row_bytes','screen_columns','ui_window_rows','csi_row_count','csi_last_row',
        'screen_cursor_row','screen_cursor_column','screen_visible_column','screen_video_offset',
        'screen_attribute_offset','screen_viewport_active','screen_viewport_offset','screen_viewport_enabled',
        'screen_attribute_checks','attributes_normal_value','attributes_current','terminal_parser_active',
        'terminal_aspect_active','terminal_ansi_wait_active']
STAGES=list(range(201,208))
RECORD_WORDS=2+len(FIELDS)+4
RECORD_BYTES=2*RECORD_WORDS


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def guard(expression,label):return 'if '+expression+'\ntransmit "BAD'+label+'"\nendif\n'
def hold(stage):return 'n8='+str(stage)+'\ntransmit "SW'+str(stage)+'^M"\npause 1\n'


def definitions():
 row=dict(ORIGINAL_DEFINITIONS()[0]);source=row['source'].replace('pause 0\n','get value 10\n')
 wide=('set msg_crlf off\n'
       'transmit "WIDECMDREADY"\nwaitfor "WIDE:" 5\nfopen 0 "WIDE.TXT" "w+b"\nfputs 0 "BEFORE|"\n'
       +guard('$row!=2 || $col!=120 || $scrncols!=80 || $scrnrows!=25','WIDEACTIVATION')+
       'locate 2 130\nmessage "R"\nlocate 2 131\n'
       +guard('$row!=2 || $col!=131','RIGHTLOCATE')+hold(201)+
       'getvattr 24 79 n0\nputvattr 24 79 46\ngetvattr 24 79 n1\n'
       +guard('n1!=46 || $row!=2 || $col!=131','RAWPHYSICAL')+hold(202)+
       'putvattr 24 79 n0\ngetvattr 24 79 n1\n'+guard('n1!=n0','RAWRESTORE')+
       'locate 4 0\nmessage "L"\nlocate 4 0\n'+guard('$row!=4 || $col!=0','LEFTLOCATE')+hold(203)+
       'locate 4 131\n'+guard('$row!=4 || $col!=131','RIGHTAGAIN')+hold(204)+
       'locate 24 131\n'+guard('$row!=24 || $col!=131','WIDESTATUSROW')+hold(205)+
       'home\n'+guard('$row!=0 || $col!=0','WIDEHOME')+hold(206)+
       'fputs 0 "AFTER|"\nfclose 0\ntransmit "WIDERESTORE"\nwaitfor "LOGIN:" 5\n'
       +guard('$row!=0 || $col!=21 || $scrncols!=80 || $scrnrows!=25','NARROWRESTORE')+hold(207)+
       'set msg_crlf on\n')
 assert source.count('transmit "GETREADY"\n')==1
 row.update(name='screen-wide-get',source=source.replace('transmit "GETREADY"\n',wide+'transmit "GETREADY"\n'),direct_GET=True,
  peer_triggers=[('WIDECMDREADY',[(0.25,'\x1b[?3h\x1b[3;116HWIDE:')]),
                 ('WIDERESTORE',[(0.25,'\x1b[?3l\x1b[2J\x1b[HFIRST BYTE SAFELOGIN:')])])
 return [row]


def observer(source,offsets,child_symbols,parent_map,child_group,case):
 symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^\s*([0-9a-f]+):([0-9a-f]+)[*+ ]+\s+(\w+)\s*$',parent_map.read_text(),re.M|re.I)}
 segment,child_ds=symbols['render_child_ds'];assert symbols['render_attached'][0]==segment
 fields='wide_sample equ admit_snapshots\nwide_count equ wide_sample+6\nwide_records equ wide_sample+8\n%if SNAPSHOT_SIZE < '+str(8+RECORD_BYTES*len(STAGES))+'\n%error Insufficient wide scratch storage\n%endif\n'
 marker='get_input_injected: dw 0';assert source.count(marker)==1
 source=source.replace(marker,fields+marker)
 marker=" cmp byte [0x82],'T'\n jne collect\n";assert source.count(marker)==1
 source=source.replace(marker,marker+' mov word [wide_sample],0x5753\n mov word [wide_sample+2],0x4449\n mov word [wide_sample+4],1\n')
 marker='timer:\n save\n cld';assert source.count(marker)==1
 source=source.replace(marker,marker+'\n call wide_tick')
 body='''
wide_tick:
 cmp word [cs:admit_seen],0
 jne .done
 cmp word [cs:exec_seen],1
 jne .done
 cmp word [cs:exec_done],0
 jne .done
 cmp word [cs:wide_count],7
 jae .done
 mov ax,[cs:parent_psp]
 add ax,16+SCREEN_SEGMENT
 mov es,ax
 cmp word [es:SCREEN_ATTACHED],1
 jne .done
 mov ax,[es:SCREEN_CHILD_DS]
 or ax,ax
 jz .done
 mov es,ax
 cmp word [es:SCREEN_COMPILER_PAUSE],0
 jne .done
 cmp word [es:SCREEN_COMPILER_SCOPE],0
 jne .done
 mov bx,[es:SCREEN_REGISTERS+16]
 mov ax,[cs:wide_count]
 add ax,201
 cmp ax,bx
 jne .done
 mov ax,[cs:wide_count]
 mov dx,RECORD_SIZE
 mul dx
 mov di,wide_records
 add di,ax
 mov [cs:di],bx
 mov [cs:di+2],es
 add di,4
 mov ax,[cs:parent_ds]
 mov es,ax
'''
 body+=' mov si,wide_field_offsets\n mov cx,'+str(len(FIELDS))+\
  '\n.fields:\n mov bx,[cs:si]\n mov ax,[es:bx]\n mov [cs:di],ax\n add si,2\n add di,2\n loop .fields\n'
 body+=''' mov ax,0xb800
 mov es,ax
 mov ax,[es:640]
 mov [cs:di],ax
 mov ax,[es:476]
 mov [cs:di+2],ax
 mov ax,[es:3998]
 mov [cs:di+4],ax
 mov ax,0x40
 mov es,ax
 mov ax,[es:0x50]
 mov [cs:di+6],ax
 inc word [cs:wide_count]
.done:
 ret
'''
 values=dict(SCREEN_SEGMENT=segment,SCREEN_ATTACHED=symbols['render_attached'][1],SCREEN_CHILD_DS=child_ds,
             SCREEN_COMPILER_PAUSE=child_symbols['_aspect_serial_compile_pause_owned'],
             SCREEN_COMPILER_SCOPE=child_symbols['_runtime_compiler_scope_state'],
             SCREEN_REGISTERS=child_symbols['_runtime_integer_a'],RECORD_SIZE=RECORD_BYTES)
 for name,value in values.items():body=body.replace(name,str(value))
 body+='wide_field_offsets: dw '+','.join(str(offsets[field]) for field in FIELDS)+'\n'
 marker='resident_end:\nstart:';assert source.count(marker)==1
 return source.replace(marker,body+'\n'+marker)


def observer_priority(folder, parent, child):
    """Replay actual observer: admission capture replaces wide scratch, then wins."""
    from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE
    from unicorn.x86_const import (UC_X86_REG_AX, UC_X86_REG_BP, UC_X86_REG_CS,
        UC_X86_REG_DS, UC_X86_REG_ES, UC_X86_REG_SS, UC_X86_REG_SP, UC_X86_REG_EFLAGS)
    listing = folder/'observer-priority.lst'
    binary = folder/'observer-priority.com'
    subprocess.run(['nasm','-fbin','-l',str(listing),str(folder/'observer.asm'),'-o',str(binary)], check=True)
    assert binary.read_bytes() == (folder/'RENDER.COM').read_bytes()
    lines = listing.read_text().splitlines()

    def label(name):
        indexes = [i for i,line in enumerate(lines) if re.search(r'(?<!\w)'+re.escape(name)+r':',line)]
        assert len(indexes) == 1, name
        for line in lines[indexes[0]:]:
            match = re.match(r'^\s*\d+\s+([0-9a-fA-F]{8})\s',line)
            if match:
                return int(match[1],16)+0x100
        raise AssertionError(name)

    def table(name):
        asm = (folder/'observer.asm').read_text()
        match = re.search(r'^'+name+r': dw ([0-9,]+)$',asm,re.M)
        assert match, name
        return [int(value) for value in match[1].split(',')]

    offsets = base.renderer.map_offsets(parent/'terminal.map')
    group = base.renderer.GROUP_REL
    psp, data, observer = 0x1000, 0x1010+group, 0x8000
    uc = Uc(UC_ARCH_X86,UC_MODE_16)
    uc.mem_map(0,0x100000)
    uc.mem_write(observer*16+0x100,binary.read_bytes())
    uc.mem_write(data*16,bytes((i*29+7)&255 for i in range(65536)))
    uc.mem_write(0x400,bytes((i*11+3)&255 for i in range(256)))
    uc.mem_write(psp*16,b'\xcd\x20')

    def word(at,value):
        uc.mem_write(at,struct.pack('<H',value))

    for name,value in (('process_psp',psp),('terminal_program_active',1),('terminal_program_kind',4),('terminal_program_status',5)):
        word(data*16+offsets[name],value)
    for name,value in (('parent_psp',psp),('parent_ds',data),('exec_seen',0),('exec_done',0),('admit_seen',0)):
        word(observer*16+label(name),value)
    at = observer*16+label('admit_snapshots')
    size = label('admit_bda')-label('admit_snapshots')
    assert size >= (8+RECORD_BYTES*len(STAGES))
    # Simulate a prior complete screen record without replacing executable code.
    uc.mem_write(at,b'SWID'+struct.pack('<HH',1,7)+bytes([0xa5])*((8+RECORD_BYTES*len(STAGES))-8))
    word(observer*16+label('old1c'),0xff00)
    word(observer*16+label('old1c')+2,observer)
    state = dict(stop=None,stopped=False)

    def code(machine,address,size,user):
        if address == state['stop']:
            state['stopped'] = True
            machine.emu_stop()
    uc.hook_add(UC_HOOK_CODE,code)

    def run(start,stop):
        state.update(stop=observer*16+stop,stopped=False)
        word(data*16+0xf000,0xff00)
        for register,value in ((UC_X86_REG_CS,observer),(UC_X86_REG_DS,data),(UC_X86_REG_SS,data),
                (UC_X86_REG_ES,0),(UC_X86_REG_SP,0xf000),(UC_X86_REG_BP,0x7000),(UC_X86_REG_AX,0),
                (UC_X86_REG_EFLAGS,2)):
            uc.reg_write(register,value)
        uc.emu_start(observer*16+start,0,count=100000)
        assert state['stopped'], 'Observer priority replay did not stop'

    # Execute the unchanged original timer admission-failure path. It must
    # overwrite the scratch record with every actual source byte and BDA byte.
    expected_words = b''.join(struct.pack('<H',int.from_bytes(uc.mem_read(data*16+off,2),'little')) for off in table('policy_table'))
    chunks = table('snapshot_table')
    expected_snapshots = b''.join(bytes(uc.mem_read(data*16+off,count)) for off,count in zip(chunks[::2],chunks[1::2]))
    expected_bda = bytes(uc.mem_read(0x400,256))
    run(label('timer'),0xff00)
    assert int.from_bytes(uc.mem_read(observer*16+label('admit_seen'),2),'little') == 1
    assert bytes(uc.mem_read(observer*16+label('admit_words'),len(expected_words))) == expected_words
    assert bytes(uc.mem_read(at,size)) == expected_snapshots
    assert bytes(uc.mem_read(observer*16+label('admit_bda'),256)) == expected_bda
    protected = bytes(uc.mem_read(at,size+256))
    run(label('wide_tick'),0xff00)
    assert bytes(uc.mem_read(at,size+256)) == protected
    result = dict(passed=True,cases=2,checks=6,observer_sha256=sha(binary),
        snapshots_preserved_bytes=size,bda_preserved_bytes=256,new_snapshot_storage_bytes=0,
        scope='Actual source-owned observer x86 bytes: complete original admission failure capture replaces prior scratch, then wide sampler preserves all failure snapshot/BDA bytes. Synthetic parent data and interrupt-chain endpoint; no application admission model substituted into DOS execution.')
    (folder/'observer-priority.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('parent-dir','child-dir','compiler-dir','output'):p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--cpu',choices=('8086','386'),default='8086');a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build') and not out.exists()
 parent,child,compiler=(getattr(a,n+'_dir').resolve() for n in ('parent','child','compiler'))
 pm=json.loads((parent/'manifest.json').read_text());assert pm['experimental_screen_commands_parent'] and pm['native_reset_transaction']
 base.definitions=definitions;base.wide_observer=observer
 marker="   temporary=dict(renderer.__dict__);exec(compile(observer_source,__file__,'exec'),temporary)"
 assert ORIGINAL_MAIN.count(marker)==1
 source=ORIGINAL_MAIN.replace(marker,"   observer_source=wide_observer(observer_source,offsets,child_symbols,parent/'terminal.map',int(group[1],16),active_case[0])\n"+marker)
 exec(compile(source,base.__file__,'exec'),base.__dict__)
 sys.argv=[sys.argv[0],'--parent-dir',str(parent),'--child-dir',str(child),'--get-compiler-dir',str(compiler),
           '--output',str(out),'--cpu',a.cpu,'--allocation-probe','--stream-probe']
 status=base.main();report=json.loads((out/'checks.json').read_text());result=report['cases'][0]
 folder=out/result['case'];raw=(folder/'RENDER.BIN').read_bytes();wire=(folder/'serial.bin').read_bytes()
 priority=observer_priority(folder,parent,child)
 at=raw.find(b'SWID');assert at>=0 and raw.count(b'SWID')==1
 version,count=struct.unpack_from('<2H',raw,at+4);records=[]
 checks=dict(result['checks']);checks['observer_failure_capture_has_priority']=priority['passed']
 checks['shared_FOPEN_GET_scratch_and_stream_retained']=(folder/'OWNED.TXT').is_file() and (folder/'OWNED.TXT').read_bytes()==b'BEFORE|LoC42'
 checks.update(wide_observer_schema=version==1 and count==len(STAGES),
  no_screen_guard_output=b'BAD' not in wire,owned_stream_across_wide=(folder/'WIDE.TXT').is_file() and (folder/'WIDE.TXT').read_bytes()==b'BEFORE|AFTER|',
  exact_wide_and_narrow_peer_triggers=wire.count(b'WIDECMDREADY')==wire.count(b'WIDERESTORE')==1)
 coordinates=[(2,131),(2,131),(4,0),(4,131),(24,131),(0,0),(0,21)]
 for index in range(count):
  values=struct.unpack_from('<'+str(RECORD_WORDS)+'H',raw,at+8+index*RECORD_BYTES)
  record=dict(stage=values[0],child_ds=values[1],fields=dict(zip(FIELDS,values[2:2+len(FIELDS)])),
              left_pixel=values[-4],right_pixel=values[-3],status_pixel=values[-2],bios_cursor=values[-1]);records.append(record)
  f=record['fields'];row,col=coordinates[index];width=80 if index==6 else 132;offset=52 if col>=80 else 0
  checks['native_coordinate_cache_'+str(index)]=(record['stage']==STAGES[index] and record['child_ds']==result['child_exit_probe']['DS']
   and f['screen_attribute_row_bytes']==width and f['screen_columns']==80 and f['ui_window_rows']==25
   and f['csi_row_count']==24 and f['csi_last_row']==23
   and f['screen_cursor_row']==row and f['screen_cursor_column']==col and f['screen_visible_column']==col-offset
   and f['screen_viewport_offset']==offset and f['screen_video_offset']==row*160+2*(col-offset)
   and f['screen_attribute_offset']==row*width+col and f['screen_viewport_enabled']==(width==132)
   and (width!=132 or f['screen_viewport_active']==(offset==0))
   and f['terminal_parser_active']==f['terminal_aspect_active']==f['terminal_ansi_wait_active']==0
   and record['bios_cursor']==row*256+col-offset)
  if index in (0,1,3,4):checks['native_right_pane_pixel_'+str(index)]=record['right_pixel']==0x0752
  if index in (2,5):checks['native_left_pane_pixel_'+str(index)]=record['left_pixel']==0x074c
 if len(records)>=2:
  checks['raw_physical_attribute_independent_of_pan']=(records[1]['status_pixel']>>8==46 and records[1]['status_pixel']&255==records[0]['status_pixel']&255)
 checks['HOME_flag0_observed']=len(records)>5 and records[5]['fields']['screen_attribute_checks']==0
 result.update(checks=checks,observer_priority=priority,wide_samples=records,passed=status==0 and all(checks.values()))
 (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 dependencies=[Path(__file__).resolve(),Path(base.__file__),ROOT/'standalone/test_aspect_renderer_dos.py',ROOT/'standalone/test_connection_dos.py']
 final=dict(passed=result['passed'],cases=[result],cpu=a.cpu,parent_sha256=sha(parent/'TERMINAL.EXE'),child_sha256=sha(child/'ASPECT.EXE'),
  compiler_sha256=sha(compiler/'ASPCOMP.EXE'),sources={str(q.relative_to(ROOT)):sha(q) for q in dependencies},
  adapted_harness_sha256=hashlib.sha256(source.encode()).hexdigest(),original_inputs=[],
  checked_HOME_exercised=False,checked_HOME_gap=dict(current='Supported profile initializes0 and reset clears screen_attribute_checks; no linked supported activation to1. Observer does not seed it.',original_producer='analysis/pcplus-overlay-anchored-13/functions/0x1f59e.asm',enable_evidence='ev_f6cd43c0efbc9a215618d5f2d2bb4df8e3675c3b99564b21b5592cf25297b202',disable_evidence='ev_3595d0cbb43110faa9e6224d35037ca51cea98ffffee1977a658b42df5ada861',caller_evidence='ev_4bca6fda2fa059463560f718d111c872c2dbb78451d82642cec963a85c74465f',remaining='Recover outer prefix/profile routing and real attribute-plane initialization; do not substitute arbitrary toggle.'),
  scope=__doc__+' Actual DOS compiler/host ASX agreement and full unchanged parent/child plus GET/owned streams; peer CSI?3h/3l activates and retires132. Native LOCATE pans0/131 and row24; raw physical attributes stay independent of logical pane. Observer reads caches/pixels only. HOME executes with observed checks0; checks1 remains a producer/integration gap. Emulated BIOS/UART/owned peer; no physical or live BBS acceptance.')
 (out/'result.json').write_text(json.dumps(final,indent=2)+'\n');print('SCREEN_WIDE_DOS',result['passed'],len(records),'samples',a.cpu)
 assert result['passed']


if __name__=='__main__':main()
