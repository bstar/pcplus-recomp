#!/usr/bin/env python3
"""Actual terminal -> attached ASPECT -> DOS child -> shared renderer/UART."""
import argparse,json,re,shutil,struct,subprocess,sys,uuid
from pathlib import Path
import test_aspect_renderer_dos as render
from directory_fixtures import directory,prm
ROOT=render.ROOT;sha=render.sha
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source


def prepare_observer(out,offsets,map_path,exit_map=None,mouse_probe=False,retry_probe=False,trap_probe=False,sound_probe=False):
    render.observer(offsets)
    source=(out/'observer.asm').read_text()
    resources=[('terminal_directory_context_valid',2),('terminal_directory_context',496),
        ('terminal_translation_mode',2),('terminal_translation_enabled',2),('terminal_translation_table',256),
        ('terminal_configuration_values',44),('uart_rx_mask',2),('terminal_keymap',948),('terminal_tab_stops',30),
        ('screen_attribute_cells',4096),('erase_attribute_values',4096),('screen_line_flags',128),('_script_handoff',50)]
    if sound_probe:resources.append(('_terminal_sound_enabled',2))
    resources += [(n,2) for n in re.findall(r'X\((\w+)\)',(ROOT/'src/aspect/renderer_policy.h').read_text())]
    size=sum(n for _,n in resources)
    symbols={n:(int(seg,16),int(off,16)) for seg,off,n in re.findall(r'^\s*([0-9a-f]{4}):([0-9a-f]{4,8})[*+]?\s+(\w+)',map_path.read_text(),re.M|re.I)}
    seg,owned=symbols['render_program_owned'];assert all(symbols[n][0]==seg for n in ('render_program_begins','render_program_ends','render_program_refreshes'))
    old=f' cmp word [cs:exec_seen],0\n jne .chain\n cmp word [{offsets["terminal_program_kind"]}],4'
    assert source.count(old)==1;source=source.replace(old,old.replace('jne .chain','jne nested_exec'))
    old=' cmp word [cs:exec_done],0\n jne .chain\n mov al,[ss:bp+16]'
    new=' cmp word [cs:exec_done],0\n jne .chain\n mov ah,0x62\n int 0x21\n mov es,bx\n mov ax,[es:0x16]\n cmp ax,[cs:parent_psp]\n jne .chain\n mov al,[ss:bp+16]'
    assert source.count(old)==1;source=source.replace(old,new)
    # Exact bytes, not hashes, are compared around the real DOS EXEC. The
    # observer never calls the parent renderer, supplies data or restores state.
    final=''' mov ax,[parent_psp]
 add ax,0x10+LEASE_SEG
 mov es,ax
 mov ax,[es:LEASE_OWNED]
 mov [final_owned],ax
 mov ax,[es:LEASE_BEGINS]
 mov [final_begins],ax
 mov ax,[es:LEASE_ENDS]
 mov [final_ends],ax
 mov ax,[es:LEASE_REFRESHES]
 mov [final_refreshes],ax
'''
    extra=r'''
nested_exec:
 cmp word [cs:exec_done],0
 jne handler.chain
 mov ah,0x62
 int 0x21
 mov es,bx
 mov ax,[es:0x16]
 cmp ax,[cs:parent_psp]
 jne handler.chain
 push cs
 pop ds
 inc word [nested_count]
 cmp word [nested_count],32
 ja .record_overflow
 mov ax,[nested_count]
 dec ax
 mov cx,70
 mul cx
 mov di,nested_records
 add di,ax
 mov [active_record],di
 mov bp,sp
 mov es,[ss:bp+2]
 mov si,[ss:bp+10]
 mov cx,63
.name:
 mov al,[es:si]
 mov [di],al
 inc si
 inc di
 or al,al
 jz .name_done
 loop .name
.name_done:
 jmp .record_ready
.record_overflow:
 inc word [records_overflow]
 mov word [active_record],0
.record_ready:
 mov di,resource_before
 call copy_resources
 mov ax,[parent_psp]
 add ax,0x10+LEASE_SEG
 mov es,ax
 mov ax,[es:LEASE_OWNED]
 mov di,[active_record]
 or di,di
 jz .lease_count
 mov [di+64],ax
.lease_count:
 cmp ax,1
 je .owned
 cmp ax,2
 jne .not_owned
.owned:
 inc word [leased_count]
.not_owned:
 restore
 pushf
 call far [cs:old21]
 save
 push cs
 pop ds
 mov bp,sp
 mov di,[active_record]
 or di,di
 jz .result_ready
 mov ax,[ss:bp+16]
 mov [di+66],ax
 mov ax,[ss:bp+18]
 and ax,1
 mov [di+68],ax
.result_ready:
 mov di,resource_after
 call copy_resources
 push cs
 pop es
 mov si,resource_before
 mov di,resource_after
 mov cx,RESOURCE_SIZE
 repe cmpsb
 je .same
 inc word [resource_mismatches]
.same:
 mov ax,[parent_psp]
 add ax,0x10+LEASE_SEG
 mov es,ax
 mov ax,[es:LEASE_OWNED]
 mov [lease_on_return],ax
 mov ax,[es:LEASE_BEGINS]
 mov [lease_begins],ax
 mov ax,[es:LEASE_ENDS]
 mov [lease_ends],ax
 mov ax,[es:LEASE_REFRESHES]
 mov [lease_refreshes],ax
 ; Preserve the real DOS returned flags in the intercepted interrupt frame.
 mov bp,sp
 mov ax,[ss:bp+18]
 mov [ss:bp+24],ax
 restore
 iret
copy_resources:
 mov es,[parent_ds]
 mov si,resource_table
 mov bp,RESOURCE_COUNT
.region:
 lodsw
 mov bx,ax
 lodsw
 mov cx,ax
.byte:
 mov al,[es:bx]
 mov [di],al
 inc bx
 inc di
 loop .byte
 dec bp
 jnz .region
 ret
resource_table: dw RESOURCE_TABLE
'''
    replacements={'LEASE_SEG':seg,'LEASE_OWNED':owned,'LEASE_BEGINS':symbols['render_program_begins'][1],
        'LEASE_ENDS':symbols['render_program_ends'][1],'LEASE_REFRESHES':symbols['render_program_refreshes'][1],
        'RESOURCE_SIZE':size,'RESOURCE_COUNT':len(resources),'RESOURCE_TABLE':','.join(str(v) for name,n in resources for v in (offsets[name],n))}
    for token,value in replacements.items():extra=extra.replace(token,str(value));final=final.replace(token,str(value))
    old=' mov di,after_history\n call copy_history\n inc word [exec_done]'
    assert source.count(old)==1;source=source.replace(old,' mov di,after_history\n call copy_history\n'+final+' inc word [exec_done]')
    sample='nested_count: dw 0\nleased_count: dw 0\nresource_mismatches: dw 0\nlease_on_return: dw 0\nlease_begins: dw 0\nlease_ends: dw 0\nlease_refreshes: dw 0\nfinal_owned: dw 0\nfinal_begins: dw 0\nfinal_ends: dw 0\nfinal_refreshes: dw 0\nrecords_overflow: dw 0\nactive_record: dw 0\nnested_records: times 32*70 db 0\nresource_before: times '+str(size)+' db 0\nresource_after: times '+str(size)+' db 0\n'
    source=source.replace('sample_end:',sample+'sample_end:').replace('resident_end:',extra+'\nresident_end:')
    if exit_map is not None:source=exit_observer(source,exit_map)
    if mouse_probe:
        from mouse_parent_probe import instrument
        source=instrument(source,map_path,offsets)
    if retry_probe:
        from parent_retry_probe import instrument
        source=instrument(source,map_path,exit_map,offsets)
    if trap_probe:
        from trap_parent_probe import instrument
        source=instrument(source,map_path,exit_map,offsets,retry_probe)
    (out/'observer.asm').write_text(source)
    subprocess.run(['nasm','-fbin',str(out/'observer.asm'),'-o',str(out/'RENDER.COM')],check=True)
    assert (out/'RENDER.COM').stat().st_size<=0xff00,'Observer exceeds DOS COM load limit'
    return (out/'RENDER.COM').read_bytes(),size


def exit_observer(source,map_path):
    """Observe actual DOS31/4D and invoke only the known retained test ISR."""
    symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',map_path.read_text(),re.M|re.I)}
    data_seg,hits=symbols['_aspect_exit_hits'];extra_seg,extra=symbols['_aspect_exit_extra']
    assert data_seg==extra_seg
    hook=r''' cmp byte [ss:bp+17],0x4d
 jne .ordinary
 cmp word [cs:exec_done],1
 jne .ordinary
 mov ah,0x62
 int 0x21
 cmp bx,[cs:parent_psp]
 jne .chain
 restore
 pushf
 call far [cs:old21]
 save
 mov bp,sp
 mov ax,[ss:bp+16]
 mov [cs:retained_raw_status],ax
 mov ax,[ss:bp+18]
 mov [ss:bp+24],ax
 restore
 iret
.ordinary:
'''
    old=' mov bp,sp\n cmp byte [ss:bp+17],0x4b'
    assert source.count(old)==1;source=source.replace(old,' mov bp,sp\n'+hook+' cmp byte [ss:bp+17],0x4b')
    old='.exit_check:\n cmp byte [ss:bp+17],0x4c\n jne .chain'
    new='.exit_check:\n cmp byte [ss:bp+17],0x4c\n je .outer_exit\n cmp byte [ss:bp+17],0x31\n jne .chain\n.outer_exit:'
    assert source.count(old)==1;source=source.replace(old,new)
    old=' mov al,[ss:bp+16]\n xor ah,ah\n mov [cs:exit_code],ax'
    capture=r''' mov al,[ss:bp+17]
 xor ah,ah
 mov [cs:retained_function],ax
 cmp ax,0x31
 jne .exit_recorded
 mov [cs:retained_psp],bx
 dec bx
 mov es,bx
 mov ax,[es:1]
 mov [cs:retained_owner_before],ax
 mov ax,[es:3]
 mov [cs:retained_paras_before],ax
.exit_recorded:
'''
    assert source.count(old)==1;source=source.replace(old,capture+old)
    after=r''' cmp word [cs:retained_function],0x31
 jne .retained_checked
 mov ax,[cs:retained_psp]
 dec ax
 mov es,ax
 mov ax,[es:1]
 mov [cs:retained_owner_after],ax
 mov ax,[es:3]
 mov [cs:retained_paras_after],ax
 xor ax,ax
 mov es,ax
 mov ax,[es:0x1b*4]
 mov [cs:retained_vector_off],ax
 mov ax,[es:0x1b*4+2]
 mov [cs:retained_vector_seg],ax
 mov ax,[cs:retained_psp]
 add ax,0x10+DATA_SEG
 mov es,ax
 mov ax,[es:HITS_OFF]
 mov [cs:retained_hits_before],ax
 mov ax,[es:EXTRA_OFF]
 mov [cs:retained_extra],ax
 dec ax
 mov es,ax
 mov ax,[es:1]
 mov [cs:retained_extra_owner],ax
 mov ax,[es:3]
 mov [cs:retained_extra_paras],ax
 mov ax,[cs:retained_extra]
 mov es,ax
 mov ax,[es:0]
 mov [cs:retained_extra_word],ax
 ; This known source-owned callback is the only active probe operation.
 int 0x1b
 mov ax,[cs:retained_psp]
 add ax,0x10+DATA_SEG
 mov es,ax
 mov ax,[es:HITS_OFF]
 mov [cs:retained_hits_after],ax
.retained_checked:
'''
    for token,value in {'DATA_SEG':data_seg,'HITS_OFF':hits,'EXTRA_OFF':extra}.items():after=after.replace(token,str(value))
    old=' inc word [exec_done]';assert source.count(old)==1;source=source.replace(old,after+old)
    names=['function','psp','owner_before','paras_before','owner_after','paras_after',
        'vector_off','vector_seg','hits_before','hits_after','raw_status','extra','extra_owner','extra_paras','extra_word']
    old='nested_count: dw 0';assert source.count(old)==1
    return source.replace(old,''.join('retained_'+n+': dw 0\n' for n in names)+old)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',default='parent-'+uuid.uuid4().hex);parser.add_argument('--case',action='append')
    parser.add_argument('--break-owner',action='store_true')
    parser.add_argument('--notice-bank',action='store_true')
    parser.add_argument('--exit-probe',action='store_true')
    parser.add_argument('--mouse',action='store_true')
    parser.add_argument('--retry',action='store_true')
    parser.add_argument('--terminal-exit-guard',action='store_true')
    parser.add_argument('--process-bank',action='store_true')
    parser.add_argument('--traps',action='store_true')
    args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    if args.exit_probe:assert args.break_owner
    if args.retry:assert args.exit_probe
    if args.terminal_exit_guard:assert args.break_owner
    if args.process_bank:assert args.terminal_exit_guard
    if args.traps:assert args.process_bank
    directory_name='aspect-parent-exit' if args.exit_probe else 'aspect-parent-break' if args.break_owner else 'aspect-parent-process'
    if args.mouse:directory_name+='-mouse'
    if args.retry:directory_name+='-retry'
    if args.terminal_exit_guard:directory_name+='-guarded'
    if args.process_bank:directory_name+='-banked'
    if args.traps:directory_name+='-traps'
    if args.notice_bank:
        assert not any([args.break_owner,args.exit_probe,args.retry,args.terminal_exit_guard,args.process_bank,args.traps])
        directory_name+='-notice-bank'
    out=ROOT/'build'/directory_name/args.label;out.mkdir(parents=True,exist_ok=False)
    parent=ROOT/'build/terminal-process/TERMINAL.EXE';child=ROOT/('build/aspect-process-break/ASPECT.EXE' if args.break_owner else 'build/aspect-process-parent/ASPECT.EXE')
    if args.notice_bank:child=ROOT/'build/aspect-notice-parent/ASPECT.EXE'
    if args.mouse:parent=ROOT/'build/terminal-mouse-process/TERMINAL.EXE'
    if args.terminal_exit_guard:parent=ROOT/('build/terminal-exit-mouse/TERMINAL.EXE' if args.mouse else 'build/terminal-exit/TERMINAL.EXE')
    if args.process_bank:parent=ROOT/('build/terminal-process-bank-mouse/TERMINAL.EXE' if args.mouse else 'build/terminal-process-bank/TERMINAL.EXE')
    if args.traps:parent=ROOT/('build/terminal-traps-mouse/TERMINAL.EXE' if args.mouse else 'build/terminal-traps/TERMINAL.EXE')
    if args.exit_probe:child=ROOT/'build/aspect-exit-parent/ASPECT.EXE'
    if args.retry:child=ROOT/'build/aspect-exit-retry/ASPECT.EXE'
    identities={}
    for product in (parent,child,ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE'):
        manifest=json.loads((product.parent/'manifest.json').read_text())
        assert manifest['binary_sha256']==sha(product)
        identities.update(manifest['sources'])
    identities.update({str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'src/aspect/compiler.py',*[ROOT/'standalone'/n for n in ('aspect_parent_child.asm','aspect_process_shell.asm','test_aspect_renderer_dos.py','test_connection_dos.py','test_terminal.py','directory_fixtures.py','modem_fixtures.py','terminal_config_fixtures.py','directory_test_support.py')]]})
    if args.mouse:identities['standalone/mouse_parent_probe.py']=sha(ROOT/'standalone/mouse_parent_probe.py')
    if args.retry:identities['standalone/parent_retry_probe.py']=sha(ROOT/'standalone/parent_retry_probe.py')
    if args.traps and args.exit_probe:identities['standalone/trap_parent_probe.py']=sha(ROOT/'standalone/trap_parent_probe.py')
    for name,digest in identities.items():
        assert sha(ROOT/name)==digest,name
        target=out/'sources'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    render.OUT=out
    offsets=render.map_offsets(parent.parent/'terminal.map')
    observer,resource_size=prepare_observer(out,offsets,parent.parent/'terminal.map',child.parent/'ASPECT.map' if args.exit_probe else None,args.mouse,args.retry,args.traps and args.exit_probe)
    harness=render.adapter(observer_high=args.retry);results=[]
    cases=[dict(name=k,kind=k,option=o,port=1,flow='H',translation='identity',full=False) for k,o in [('G',''),('T',' NOCLEAR'),('W',' WAIT'),('R',' NOCLEAR'),('F','')]]
    cases += [dict(name=f'full-{port}-{flow}',kind='FULL',option='',port=port,flow=flow,translation=('table' if (port+ord(flow))%2 else 'seven'),full=True) for port in (1,2) for flow in 'NSHB']
    if args.exit_probe:
        cases=[dict(name=f'Q-{port}-{flow}',kind='G',option=' WAIT',port=port,flow=flow,translation='identity',full=False) for port in [1,2] for flow in 'NSHB']
    if args.case:cases=[c for c in cases if c['name'] in args.case];assert {c['name'] for c in cases}==set(args.case)
    for case in cases:
        name,kind,option,port,flow=(case[k] for k in ('name','kind','option','port','flow'));full=case['full'];folder=out/name;folder.mkdir()
        shutil.copyfile(parent,folder/'TERMINAL.EXE');shutil.copyfile(child,folder/'ASPECT.EXE');harness.BINARY=folder/'TERMINAL.EXE'
        subprocess.run(['nasm','-fbin','-DPORT='+hex(0x3f8 if port==1 else 0x2f8),'-DVECTOR='+str(12 if port==1 else 11),'-DIRQBIT='+str(16 if port==1 else 8),*(['-DREQUIRE_OUTPUT'] if full else []),str(out/'sources/standalone/aspect_parent_child.asm'),'-o',str(folder/'NESTED.COM')],check=True)
        script=('integer value\nproc main\nwaitfor "LOGIN:" 5\nif failure\nmessage "FAIL initial input"\nexit\nendif\n'
                'set display on\nfopen 0 "PRIVATE.BIN" "rb"\nfgetc 0 value\n'
                f'run "D:\\NESTED.COM {kind}"{option}\n'
                'fgetc 0 value\nif value!=69\nmessage "FAIL private stream"\nexit\nendif\n'
                'fclose 0\nmessage "AFTER CHILD"\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendproc\n')
        payload=bytearray(directory());payload[302:311]=b'LOGIN\0\0\0\0';payload[325:336]=b'Synth42\0\0\0\0'
        files={'LOGIN.ASX':compile_source(script),'LOGIN.ASP':script.encode(),
               'NESTED.COM':(folder/'NESTED.COM').read_bytes(),'RENDER.COM':observer,'PRIVATE.BIN':b'SEED0'}
        if args.retry:
            retry_source=('proc main\nset display on\nstrcmp $D_NAME "LAB NODE 001"\nif failure\nmessage "FAIL retry name"\nexit\nendif\n'
                'if $D_ENTRY!=1\nmessage "FAIL retry entry"\nexit\nendif\n'
                'run "D:\\NESTED.COM T" NOCLEAR\n'
                'transmit "RETRY-OK^M"\nwaitfor "RETRY-ACK" 5\nif waitfor\n'
                'fopen 0 "RETRY.OUT" "wb"\nfputs 0 "retry-owned"\nfclose 0\nmessage "RETRY COMPLETE"\n'
                'else\nmessage "FAIL retry peer"\nendif\nendproc\n')
            files.update({'RETRY.ASX':compile_source(retry_source),'RETRY.ASP':retry_source.encode()})
        if full:
            opening='set display on\nset fgets_crlf off\nputenv "CTRLVAR=OWNED"\n'
            for slot in range(5):opening+=f'fopen {slot} "SLOT{slot}.BIN" "rb"\nfgetc {slot} value\n';files[f'SLOT{slot}.BIN']=b'SEED0'
            opening+='fopen 5 "WRITE.BIN" "wb"\nfputs 5 "pending5"\nfindfirst "ENUM\\*.DAT"\n'
            verify=''
            for slot in range(5):verify+=f'ftell {slot} position\nif position!=1L\nmessage "FAIL position"\nexit\nendif\nfgetc {slot} value\nif value!=69\nmessage "FAIL prefetch"\nexit\nendif\nfseek {slot} 1L 0\n'
            verify+='strcmp $D_NAME "LAB NODE 001"\nif failure\nmessage "FAIL selected name"\nexit\nendif\nif $D_ENTRY!=1\nmessage "FAIL selected entry"\nexit\nendif\n'
            commands=''
            for k,o in [('G',''),('T',' NOCLEAR'),('W',' WAIT'),('R',' NOCLEAR'),('G',' NOCLEAR')]:commands+=f'run "D:\\NESTED.COM {k}"{o}\n'+verify
            commands+='run "ABSENT.COM"\nif success\nmessage "FAIL missing command"\nexit\nendif\ndos "ver > SYSTEM.OUT"\nputenv "COMSPEC=D:\\SHELLGO.COM"\nstrcmp "A" "A"\nshell\nif failure\nmessage "FAIL SHELL comparison"\nexit\nendif\n'
            script='integer value\nlong position\nproc main\nwaitfor "LOGIN:" 5\nif failure\nexit\nendif\n'+opening+commands+verify+'execute "NEXT.ASP"\nendproc\n'
            next_source='integer value,setting\nlong position\nstring preserved\nproc main\nfetch fgets_crlf setting\nif setting!=0\nmessage "FAIL setting"\nexit\nendif\ngetenv "CTRLVAR" preserved\nstrcmp preserved "OWNED"\nif failure\nmessage "FAIL environment"\nexit\nendif\nrun "D:\\NESTED.COM T" NOCLEAR\n'+verify+'findnext\nif found==0\nmessage "FAIL enumeration"\nexit\nendif\nfindnext\nif found\nmessage "FAIL enumeration end"\nexit\nendif\nmessage "AFTER CHILD"\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendproc\n'
            files.update({'LOGIN.ASX':compile_source(script),'LOGIN.ASP':script.encode(),'NEXT.ASP':next_source.encode(),'ENUM/A.DAT':b'A','ENUM/B.DAT':b'B'})
            shutil.copyfile(ROOT/'build/aspect-compiler-dos/ASPCOMP.EXE',folder/'ASPCOMP.EXE')
            subprocess.run(['nasm','-fbin',str(ROOT/'standalone/aspect_process_shell.asm'),'-o',str(folder/'SHELLGO.COM')],check=True)
            files['SHELLGO.COM']=(folder/'SHELLGO.COM').read_bytes()
        (folder/'CHILD.LOG').write_bytes(b'')
        settings=bytearray(prm(port=port,soft=int(flow in 'SB'),hard=int(flow in 'HB')));extra=''
        if args.mouse:struct.pack_into('<HH',settings,0x4e4,8,4)
        payload=bytearray(directory(port=port));payload[302:311]=b'LOGIN\0\0\0\0';payload[325:336]=b'Synth42\0\0\0\0'
        banner=b'\x1b[2J\x1b[HFIRST BYTE SAFE\x1b[6n\x1b[0cLOGIN:';post=render.QUERY
        if case['translation']=='table':
            table=bytearray(range(256));table[ord('z')]=27;table[27]=ord('!');table[ord('[')]=ord('{');files['TEST.XLT']=bytes(table);extra=' /X:D:\\TEST.XLT';banner=banner.replace(b'\x1b',b'z');post=post.replace(b'\x1b',b'z')
        if case['translation']=='seven':struct.pack_into('<H',settings,0x1d64-0x1b84,2);banner=bytes(x|128 for x in banner);post=bytes(x|128 for x in post)
        harness.RENDER_POST=b'\x1b[2;1H'+post if args.exit_probe else post
        harness.RENDER_TRIGGER=b'ready' if args.exit_probe else b'Synth42\r'
        keys='p6500 space p700 '+('a-z p1500 ' if args.mouse else '')+'r e a d y p700 a-x'
        if args.retry:
            harness.RENDER_POST=b'RETRY-ACK\x1b[2;1H'+post
            harness.RENDER_TRIGGER=b'RETRY-OK\r'
            keys='p6500 space p700 a-z p300 a p300 r e t r y . a s x enter p2000 '+('a-z p1500 ' if args.mouse else '')+'r e a d y p700 a-x'
        result=harness.run(name,'success',keys,directory=bytes(payload),prm=bytes(settings),com=port,
            arguments='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /A:NETWORK'+extra,files=files,
            banner=banner,working_drive='d',observer='RENDER')
        wire=(folder/'serial.bin').read_bytes();screen=(folder/'SCREEN.BIN').read_bytes();raw=(folder/'RENDER.BIN').read_bytes()
        header=struct.unpack_from('<7H',raw);checks=result['checks']
        at=len(raw)-26-32*70-resource_size*(1 if args.retry else 2)
        resources=struct.unpack_from('<13H',raw,at)
        records=[]
        for i in range(min(resources[0],32)):
            entry=raw[at+26+i*70:at+26+(i+1)*70];lease,result_word,carry=struct.unpack_from('<3H',entry,64)
            records.append(dict(name=entry[:64].split(b'\0',1)[0].decode('cp437'),lease=lease,result=result_word,carry=carry))
        successful=[r for r in records if not r['carry']]
        fatal=kind=='F' or args.exit_probe;calls=9 if full else 1
        checks.update(outer_ASPECT_exit=header[:4]==(0x524e,1,1,1) and header[6]==(10 if args.exit_probe else 14 if fatal else 0),
            real_nested_EXEC_observed=len(successful)==(9 if full else 1) and not resources[11],
            owned_parent_lease=sum(r['lease']!=0 for r in successful)==(8 if full else 1) and resources[3]==(1 if full or kind in 'TR' else 2),
            parent_resources_unchanged=resources[2]==0,
            exact_lease_sequence=resources[4:7]==(calls,calls-1,2 if full else 0),
            parent_lease_retired=resources[7:11]==(0,calls,calls,2 if full else int(kind=='R')),
            actual_child_log=(folder/'CHILD.LOG').read_bytes()==(b'GT' if args.retry else b'GTWRGT' if full else kind.encode()),
            private_stream_continued=b'FAIL' not in screen[::2] and (b'AFTER CHILD' in screen[::2])!=fatal,
            password_after_child=wire.count(b'Synth42\r')==int(not fatal),
            resumed_parent_keyboard=b'ready' in wire,parent_JFT=raw[14:34]==raw[34:54],
            parent_file_owners=raw[54:470]==raw[470:886],
            expected_parent_error=(b'ASPECT returned an error.' in screen[::2])==fatal)
        if kind in 'TR':checks['NOCLEAR_visible_child_text']=screen[20*160:20*160+2]==b'C\x4f'
        if not fatal:checks['post_child_CPR']=b'\x1b[2;1R' in wire[wire.find(b'Synth42\r')+8:]
        if kind in 'GW' and not fatal:checks['saved_parent_screen_restored']=screen[:42:2]==b'FIRST BYTE SAFELOGIN:'
        retained=None
        mouse=None
        trap_snapshot=None
        if args.traps and args.exit_probe:
            from trap_parent_probe import MARKER
            assert raw.count(MARKER)==1
            trap_snapshot=struct.unpack_from('<16H',raw,raw.index(MARKER)+len(MARKER))
            checks['caller_traps_suspended']=trap_snapshot[0]==2 and trap_snapshot[15]==1
            checks['caller_trap_vectors_restored']=trap_snapshot[1:7]==trap_snapshot[8:14]
            checks['caller_break_flag_restored']=trap_snapshot[7]==trap_snapshot[14] and trap_snapshot[7] in (0,1)
        if not args.exit_probe:checks['no_false_retention_notice']=b'ASPECT memory retained.' not in screen[::2]
        if args.exit_probe:
            retained=struct.unpack_from('<15H',raw,at-30)
            symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',(child.parent/'ASPECT.map').read_text(),re.M|re.I)}
            code_seg,code_off=symbols['_aspect_exit_foreign']
            checks.update(actual_DOS31_and_4D=retained[0]==0x31 and retained[10]==0x030a,
                retained_main_MCB=retained[1]==retained[2]==retained[4] and retained[3]==retained[5] and retained[3]>0,
                retained_source_ISR=retained[6:8]==(code_off,retained[1]+0x10+code_seg),
                retained_callback_invoked=retained[8:10]==(0,1),
                retained_extra_MCB=retained[12]==retained[1] and retained[13:15]==(0x20,0xa55a),
                retained_memory_notice=b'ASPECT memory retained.' in screen[::2],
                continued_parent_CPR=b'\x1b[2;1R' in wire[wire.find(b'RETRY-OK\r')+9:] if args.retry else b'\x1b[2;1R' in wire[wire.find(b'ready')+5:])
        if args.mouse:
            from mouse_parent_probe import WORDS,BUFFER,BYTES
            start=at-(30 if args.exit_probe else 0)-BYTES
            mouse=dict(zip(WORDS,struct.unpack_from('<'+str(len(WORDS))+'H',raw,start)))
            syms={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+]?\s+(\w+)\s*$',(parent.parent/'terminal.map').read_text(),re.M|re.I)}
            cb_seg,cb_off=syms['mouse_callback'];expected=(cb_off,header[5]+0x10+cb_seg)
            before_at=start+len(WORDS)*2;driver_bytes=mouse['state_bytes']
            capture=folder/'PCPLUS.SCR'
            checks.update(mouse_registered_after_return=mouse['seen']==1 and (mouse['resume_off'],mouse['resume_seg'])==expected and mouse['resume_mask']==0x0b,
                mouse_suspended_for_ASPECT=mouse['suspended_mask']==0,
                mouse_foreign_DS_restored=mouse['returned_ds']==0x40,
                mouse_callback_depth=mouse['depth_before']==mouse['depth_after']==65535,
                mouse_PRM_scale=(mouse['scale_x'],mouse['scale_y'])==(8,4),
                neutral_mouse_event_preserves_queue=mouse['count_before']==mouse['count_after']==0,
                mouse_menu_native_events=(mouse['menu_stage'],mouse['menu_count'],mouse['menu_code'],mouse['button_count'],mouse['button_code'])==(2,2,2,1,4),
                mouse_menu_screen_action=capture.is_file() and capture.stat().st_size>0 and b'Command Menu' not in capture.read_bytes(),
                original_mouse_registration_restored=(mouse['after_mask'],mouse['after_off'],mouse['after_seg'])==(mouse['before_mask'],mouse['before_off'],mouse['before_seg']),
                original_mouse_driver_state=0<driver_bytes<=BUFFER and mouse['state_equal']==1 and raw[before_at:before_at+driver_bytes]==raw[before_at+BUFFER:before_at+BUFFER+driver_bytes])
        retry=None
        if args.retry:
            from parent_retry_probe import WORDS as RETRY_WORDS,BYTES as RETRY_BYTES
            from mouse_parent_probe import BYTES as MOUSE_BYTES
            start=at-30-(MOUSE_BYTES if args.mouse else 0)-RETRY_BYTES
            retry=dict(zip(RETRY_WORDS,struct.unpack_from('<'+str(len(RETRY_WORDS))+'H',raw,start)))
            pairs=[('vector_before_off','vector_before_seg'),('vector_after_off','vector_after_seg')]
            normal_witness=struct.unpack('<3H',(folder/'RETRYWIT.BIN').read_bytes()) if (folder/'RETRYWIT.BIN').exists() else None
            cleanup_witness=struct.unpack('<10H',(folder/'RETRYDBG.BIN').read_bytes()) if (folder/'RETRYDBG.BIN').exists() else None
            checks.update(same_session_second_EXEC=retry['seen']==retry['returned']==1 and retry['carry']==0,
                observer_loaded_high=retry['observer_segment']>=0xa000,
                retry_normal_DOS4C=retry['child_function']==0x4c and retry['child_code']==retry['status']==0,
                retry_distinct_PSP=retry['psp'] not in (0,retained[1],header[5]),
                retry_real_PROGRAM=retry['nested_calls']==1 and retry['nested_carry']==0 and retry['nested_lease']==1 and retry['nested_status']==37,
                retry_resources_unchanged=retry['resources_equal']==1,
                retry_lease_retired=retry['final_lease']==0,
                retry_retained_vector_preserved=all(tuple(retry[n] for n in pair)==(trap_snapshot[1:3] if args.traps else retained[6:8]) for pair in pairs),
                retry_retained_callback_live=(retry['callback_before'],retry['callback_after'])==(1,2),
                retry_retained_MCB=retry['retained_owner']==retained[1] and retry['retained_paras']==retained[3],
                retry_retained_extra=(retry['extra_owner'],retry['extra_paras'],retry['extra_word'])==(retained[1],0x20,0xa55a),
                retry_parent_JFT=retry['jft_equal']==1,retry_parent_file_owners=retry['owners_equal']==1,
                retry_serial_exchange=wire.count(b'RETRY-OK\r')==1,
                retry_file_completion=(folder/'RETRY.OUT').is_file() and (folder/'RETRY.OUT').read_bytes()==b'retry-owned',
                retry_completed_screen=b'RETRY COMPLETE' in screen[::2],
                retry_actual_cli_witness=normal_witness is not None and normal_witness[0]==0,
                retry_reusable_owners=cleanup_witness==(37,0,0,0,0,0,0,0,1,0),
                retry_interrupts_enabled=bool(retry['nested_caller_flags']&0x200))
        if full:
            checks['DOS_source_compiler']=(folder/'NEXT.ASX').is_file() and (folder/'NEXT.ASX').read_bytes()==compile_source(next_source)
            checks['real_command_shell']=(folder/'SHELL.OUT').is_file() and (folder/'SHELL.OUT').read_bytes()==b'SHELLREAL'
            checks['pending_stream_output']=(folder/'WRITE.BIN').is_file() and (folder/'WRITE.BIN').read_bytes()==b'pending5'
        result.update(passed=all(checks.values()),passive_header=header,resource_words=resources,nested_EXEC=records,compared_parent_bytes=resource_size,configuration=case,retained_words=retained,mouse_probe=mouse,retry_probe=retry,trap_snapshot=trap_snapshot)
        (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result)
        print(name,'FINAL PASS' if result['passed'] else 'FINAL FAIL',flush=True)
    for name,digest in identities.items():assert sha(ROOT/name)==digest,name
    report=dict(passed=all(r['passed'] for r in results),banked_process=args.process_bank,terminal_exit_guard=args.terminal_exit_guard,same_session_retry=args.retry,experimental_mouse=args.mouse,experimental_break_owner=args.break_owner,exit_probe=args.exit_probe,cases=results,parent_sha256=sha(parent),child_sha256=sha(child),
        source_hashes=identities,
        checker_sha256=sha(Path(__file__)),observer_sha256=sha(out/'RENDER.COM'),
        scope=('Actual retained child return through capability7; observer records DOS31/4D/MCBs and invokes only the known retained test ISR. Real renderer/UART reacquisition; no state repair or physical modem claim.' if args.exit_probe else 'Experimental capability7; real attached parent renderer, selected synthetic directory, actual DOS child and UART mutation. No physical modem or whole-application publication.'))
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
