#!/usr/bin/env python3
"""Current parent/ASPECT through staged proxy: DCD loss, redial, exact retry.

DOSBox's built-in modem owns Hayes/UART/DCD; actual SynthModem owns Telnet.
No physical Boca/SPA2102/SIP/DSP acceptance.
"""
import argparse
import asyncio
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import time
import traceback
from product_inputs import ROOT,select_product,sha,stage_companions
from proxy_carrier_relay import carrier_relay
from test_transfer_dos import timestamp,offset_after
from audit_zmodem import scan,packet,metadata,audit_batch,audit_controls
from audit_size_probe_screen import telnet
from enigma import SOURCE,process_pid
from bbs_log_capture import begin as begin_log,collect as collect_log
from test_proxy_transfer_dos import post_count
from enigma_script_login import source as login_source
from paced_bios_keys import source as paced_source
from carrier_notice_watch import SAMPLER
from directory_fixtures import prm,directory
from directory_test_support import accounting_check
sys.path.insert(0,str(ROOT/'src/aspect'))
from compiler import compile_source


def keyboard_source(recipe,upper_memory=False):
    # Only data changes: browser key60h/scan29h uses the proven paced ISR.
    # This recipe has no literal exclamation key; ASPECT supplies its password.
    assert '!' not in recipe.split()
    text=paced_source(recipe.replace('browser','!'))
    assert text.count(',545\n')==recipe.split().count('browser')
    text=text.replace(',545\n',',10592\n')
    if upper_memory:
        marker='install:\n';assert text.count(marker)==1
        text=text.replace(marker,marker+' mov ax,[0x2c]\n or ax,ax\n jz .no_env\n mov es,ax\n mov ah,49h\n int 21h\n jc .failed\n mov word [0x2c],0\n.no_env:\n',1)
        text+='\n.failed:\n mov ax,4c01h\n int 21h\n'
    return text


def sampler_source(upper_memory=False):
    text=SAMPLER.replace('mov cx,4000','mov cx,8000')
    if upper_memory:
        marker='install:\n';assert text.count(marker)==1
        text=text.replace(marker,marker+' mov ax,[0x2c]\n or ax,ax\n jz .no_env\n mov es,ax\n mov ah,49h\n int 21h\n jc failed\n mov word [0x2c],0\n.no_env:\n',1)
    for off in (0,1,3,4):text=text.replace(hex(0x3f8+off),hex(0x3e8+off))
    return text


async def run(a):
    assert re.fullmatch('[a-z0-9-]+',a.label) and re.fullmatch(r'P[A-F0-9]{6}\.BIN',a.file)
    assert process_pid(),'Owned stock Enigma must already run'
    runtime=a.runtime.resolve();assert runtime.is_relative_to(ROOT/'build')
    lock=(ROOT/'build/bbs-lab/enigma/.dos-integration.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    out=ROOT/'build/bbs-lab/results/enigma'/a.label;out.mkdir(parents=True,exist_ok=False)
    stage=out/'program';stage.mkdir();recv=out/'RECV';recv.mkdir();inputs=[];products={}
    for leaf,path in [('TERMINAL.EXE',a.terminal),('ASPECT.EXE',a.runner),('ASPCOMP.EXE',a.compiler)]:
        binary,sources=select_product(path,leaf);inputs+=sources+[binary]
        shutil.copyfile(binary,stage/leaf);inputs.append(stage/leaf)
        staged=stage_companions(binary,stage);inputs+=staged
        # Help bundles add their own declared source closure; count actual unique
        # source paths, rather than treating repeated manifest entries as files.
        source_names={str(p.relative_to(ROOT)) for p in sources if p.relative_to(ROOT).parts[0]!='build'}
        declared=json.loads(binary.with_name('manifest.json').read_text())
        products[leaf]=dict(path=str(binary.relative_to(ROOT)),sha256=sha(binary),source_files=len(source_names),
            declared_source_files=len(declared['sources']),bound_files=len({str(p) for p in sources}))
    help_file=a.runner.resolve().parent/'LOCHELP.HLP'
    if help_file.exists():shutil.copyfile(help_file,stage/help_file.name);inputs += [help_file,stage/help_file.name]
    script=login_source().replace('fputs 5 "START"\n','fputs 5 "START"\ntransmit "loc^M"\n',1)
    (stage/'LOGON.ASP').write_bytes(script.replace('\n','\r\n').encode('ascii'));inputs.append(stage/'LOGON.ASP')
    initial_asx_absent=not (stage/'LOGON.ASX').exists();assert initial_asx_absent
    if a.live_source:
        parent_manifest=json.loads(a.terminal.resolve().with_name('manifest.json').read_text())
        child_manifest=json.loads(a.runner.resolve().with_name('manifest.json').read_text())
        assert parent_manifest['experimental_compiler_lease_bridge'] and child_manifest['experimental_compiler_parent_lease']
        assert (stage/'PCCOMP.OVL').is_file()
    startup=dict(live_source=a.live_source,initial_ASX_absent=initial_asx_absent,source_sha256=sha(stage/'LOGON.ASP'),compile_before_parent=not a.live_source)
    (out/'startup-source.json').write_text(json.dumps(startup,indent=2)+'\n');inputs.append(out/'startup-source.json')
    payload_path=SOURCE/'file_base/pcplus_transfer'/a.file;payload=payload_path.read_bytes()
    assert len(payload)==65539 and set(payload)==set(range(256));inputs.append(payload_path)
    filename=' '.join(a.file)
    menu='F enter p2000 S enter p2000 '+filename+' enter p1500 enter p2000 t p1500 q p1500 escape p1000 D enter p2000 a p1500 enter '
    recipe=('p900 enter p85000 c-y '+menu+'p20000 enter p2000 browser tab D '+
        'p85000 '+menu+'p'+str(a.transfer_wait_ms)+' enter p2000 L enter p1500 escape p1500 escape p1500 S enter p1500 '+
        filename+' enter p1500 enter p6000 q p3000 escape p3000 G enter p3000 Y p5000 enter p8000 '+
        'Q U I T enter p10000 a-x')
    if a.startup_probe:
        assert a.exec_probe
        recipe='p900 enter p20000 space p4000 a-x'
    (out/'recipe.json').write_text(json.dumps(dict(recipe=recipe),indent=2)+'\n')
    guard_observer=None
    sampler_text=sampler_source(a.umb)
    if getattr(a,'guard_observer_check',None):
        from carrier_key_observer import build
        sampler_text,guard_observer=build(a.terminal,out/'guard-observer')
        proof=a.guard_observer_check.resolve();assert proof.is_relative_to(ROOT/'build')
        control=json.loads(proof.read_text());assert control['passed']
        assert control['observer']['observer_sha256']==guard_observer['observer_sha256']
        assert control['observer']['binary_sha256']==sha(a.terminal)
        for name,digest in control['sources'].items():assert sha(ROOT/name)==digest,name
        guard_observer['transparency_report']=dict(path=str(proof.relative_to(ROOT)),sha256=sha(proof))
        inputs += [proof,ROOT/'lab/bbs/carrier_key_observer.py']+[p for p in (out/'guard-observer').iterdir() if p.is_file()]
    (out/'KEYS.ASM').write_text(keyboard_source(recipe,upper_memory=a.umb));(out/'sampler.asm').write_text(sampler_text)
    # COM3, IRQ5; passive sampler uses the actual configured UART addresses.
    sampler=(out/'sampler.asm').read_text()
    for off in (0,1,3,4):sampler=sampler.replace(hex(0x3f8+off),hex(0x3e8+off))
    (out/'sampler.asm').write_text(sampler)
    for asm,leaf in [(out/'KEYS.ASM','PACED.COM'),(out/'sampler.asm','SNAP.COM'),(ROOT/'standalone/display_startup_geometry.asm','GEOM.COM')]:
        subprocess.run(['nasm','-fbin',str(asm),'-o',str(out/leaf)],check=True)
    inputs += [out/n for n in ['recipe.json','KEYS.ASM','sampler.asm','PACED.COM','SNAP.COM','GEOM.COM']]
    if a.exec_probe:
        observer=(ROOT/'standalone/help_exec_watch.asm').read_text()
        marker=' mov [old21+2],es\n';assert observer.count(marker)==1
        observer=observer.replace(marker,marker+' mov ax,[0x2c]\n or ax,ax\n jz .probe_no_env\n mov es,ax\n mov ah,49h\n int 21h\n jc failed\n mov word [0x2c],0\n.probe_no_env:\n',1)
        marker='records: times 16*24 db 0';assert observer.count(marker)==1
        observer=observer.replace(marker,marker+'\nmemsamples: times 16 dw 0\nmcbsamples: times 16*50 dw 0',1).replace('390','2022')
        marker='.captured:\n';assert observer.count(marker)==1
        observer=observer.replace(marker,marker+' cmp word [ss:bp-6],4b00h\n jne .memory_done\n push bx\n mov ah,48h\n mov bx,0ffffh\n pushf\n call far [cs:old21]\n mov di,[cs:state+2]\n dec di\n shl di,1\n mov [cs:memsamples+di],bx\n mov ax,di\n mov cx,50\n mul cx\n mov di,ax\n mov ah,62h\n pushf\n call far [cs:old21]\n mov [cs:mcbsamples+di],bx\n mov es,bx\n mov ax,[es:2ch]\n mov [cs:mcbsamples+di+2],ax\n add di,4\n dec bx\n mov cx,16\n.mcb_loop:\n cmp bx,0a000h\n jae .mcb_done\n mov es,bx\n mov al,[es:0]\n cmp al,4dh\n je .mcb_valid\n cmp al,5ah\n jne .mcb_done\n.mcb_valid:\n mov [cs:mcbsamples+di],bx\n mov ax,[es:1]\n mov [cs:mcbsamples+di+2],ax\n mov ax,[es:3]\n mov [cs:mcbsamples+di+4],ax\n add di,6\n add bx,ax\n jc .mcb_done\n inc bx\n loop .mcb_loop\n.mcb_done:\n pop bx\n.memory_done:\n',1)
        (out/'EXECW.ASM').write_text(observer)
        subprocess.run(['nasm','-fbin',str(out/'EXECW.ASM'),'-o',str(out/'EXECW.COM')],check=True)
        inputs += [ROOT/'standalone/help_exec_watch.asm',out/'EXECW.ASM',out/'EXECW.COM']

    names=['test_proxy_carrier_dos','proxy_carrier_relay','paced_bios_keys','carrier_notice_watch','zmodem_label_watch',
        'test_transfer_dos','modem','audit_zmodem','audit_size_probe_screen','enigma_script_login','test_proxy_transfer_dos','bbs_log_capture']
    inputs += [ROOT/'lab/bbs'/(n+'.py') for n in names]
    inputs += [ROOT/'lab/bbs/synthmodem_proxy_serial.js',ROOT/'standalone/test_terminal.py',
        ROOT/'standalone/display_startup_geometry.asm',ROOT/'standalone/directory_fixtures.py',ROOT/'standalone/directory_test_support.py',
        ROOT/'src/aspect/compiler.py']
    inputs += [SOURCE/n for n in ['main.js','core/client.js','core/file_transfer.js','core/file_entry.js',
        'core/file_area_list.js','core/file_base_search.js','core/download_queue.js','core/menu_module.js','core/system_menu_method.js',
        'config/config.hjson','config/menus/loc-file_base.hjson','config/menus/loc-main.hjson','package-lock.json']]+[SOURCE.parent/'helpers/sexyz']
    if a.witness:
        from carrier_fault_witness import build
        build(a.terminal.resolve(),out)
        inputs += [ROOT/'lab/bbs/carrier_fault_witness.py',ROOT/'standalone/phone_log_events_watch.asm',
                   out/'WITNESS.ASM',out/'WITNESS.COM',out/'KEYWAIT.ASM',out/'KEYWAIT.COM']
    posts=post_count();log=SOURCE/'logs/enigma-bbs.log'
    begin_log(log,out/'server-log-start.json')
    bridge=ROOT/'build/bbs-lab'/(a.label+'-proxy')
    proxy=subprocess.Popen(['node',str(ROOT/'lab/bbs/synthmodem_proxy_serial.js'),'--runtime',str(runtime),
        '--output',str(bridge),'--bbs-port','23233','--framing-ms','250','--byte-delay-ms','0',
        '--terminal-rows','24','--probe-terminal-size','--disconnect-on-quit'],stdout=subprocess.DEVNULL,stderr=(out/'proxy.log').open('w'))
    finished=asyncio.Event();snapshots=[];sessions=[]
    try:
        deadline=time.monotonic()+15
        while not (bridge/'ready.json').exists():
            assert proxy.poll() is None and time.monotonic()<deadline
            await asyncio.sleep(.05)
        ready=json.loads((bridge/'ready.json').read_text())
        for name,h in ready['installed_sources'].items():assert sha(runtime/name)==h;inputs.append(runtime/name)
        async with carrier_relay(ready['endpoint']['port']) as (port,sessions):
            image=bytearray(prm(port=3,baud=5,soft=0,hard=1))
            for at,value in [(0x188,5),(0x42c,1),(0x1c2,0),(0x1c8,2),(0x1ca,25),(0x4ec,0),(0x1e6,0),(0x4e4,8),(0x4e6,4)]:struct.pack_into('<H',image,at,value)
            # Fixture-only escape guard matches the parent's post-escape pause.
            # No assertion is made about the physical Boca's S12 setting.
            image[0x18:0x47]=b'AT&K3S12=25^M'.ljust(47,b'\0');path=b'D:\\RECV\\\0';image[0x31c:0x31c+len(path)]=path
            book=bytearray(directory(entry=3,target=f'127.0.0.1:{port}'.encode(),port=3,baud=5))
            at=250+2*114;book[at+52:at+61]=b'LOGON\0\0\0\0'
            for name,data in [('TEST.PRM',image),('START.PRM',image),('TEST.DIR',book),('START.DIR',book)]:
                (out/name).write_bytes(data)
            inputs += [out/'START.PRM',out/'START.DIR']
            frozen={str(p.relative_to(ROOT)):sha(p) for p in inputs}
            async def watch():
                while not finished.is_set():
                    partial=recv/'PCRX.$$$'
                    if len(sessions)==1 and not sessions[0].interrupted and partial.exists():
                        data=partial.read_bytes()
                        if len(data)>=4096:
                            assert data==payload[:len(data)] and len(data)<len(payload)
                            snapshots.append(dict(kind='partial-before-drop',bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),
                                relay_seconds=time.monotonic()-sessions[0].start,first_login_trace=(stage/'LOGIN.LOG').read_text()))
                            sessions[0].interrupt()
                    if len(sessions)>=2 and len(snapshots)==1:
                        snapshots.append(dict(kind='before-second-login',files=sorted(p.name for p in recv.iterdir())))
                    await asyncio.sleep(.01)
            watcher=asyncio.create_task(watch())
            (out/'dosbox.conf').write_text(f'''[sdl]
output=surface
[dosbox]
memsize=8
[cpu]
core=normal
cputype={a.cpu}
cycles=fixed 6000
[mixer]
nosound=true
{('[dos]'+chr(10)+'xms=true'+chr(10)+'ems=false'+chr(10)+'umb=true') if a.umb else ''}
[serial]
serial1=disabled
serial2=disabled
serial3=modem irq:5 listenport:0
serial4=disabled
[autoexec]
@echo off
mount c "{stage}"
mount d "{out}"
c:
{('rem Compile source inside the attached ASPECT interpreter' if a.live_source else 'ASPCOMP LOGON.ASP LOGON.ASX >D:'+chr(92)+'COMPILE.TXT'+chr(10)+'if errorlevel 1 goto failed')}
{('LH D:'+chr(92)+'SNAP B') if a.umb else ('D:'+chr(92)+'SNAP B')}
{(('LH ' if a.umb else '')+'D:'+chr(92)+'EXECW T') if a.exec_probe else ''}
{('D:'+chr(92)+'WITNESS T') if a.witness else ''}
{('LH D:'+chr(92)+'PACED') if a.umb else ('D:'+chr(92)+'PACED')}
if errorlevel 1 goto failed
TERMINAL @D:\\TEST.PRM /E:D:\\TEST.DIR /N:3
if errorlevel 1 goto failed
echo PASS>D:\\PASS.TXT
goto capture
:failed
echo FAIL>D:\\FAIL.TXT
{('D:'+chr(92)+'KEYWAIT') if a.witness else ''}
:capture
{('D:'+chr(92)+'EXECW') if a.exec_probe else ''}
{('D:'+chr(92)+'WITNESS') if a.witness else ''}
D:\\GEOM
D:\\SNAP S
D:\\SNAP A
exit
''')
            try:
                with (out/'dosbox.log').open('w') as capture:
                    process=await asyncio.create_subprocess_exec('dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf'),cwd=out,
                        env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=capture,stderr=capture)
                    try:code=await asyncio.wait_for(process.wait(),330+a.transfer_wait_ms/1000)
                    except asyncio.TimeoutError:
                        process.terminate()
                        try:await asyncio.wait_for(process.wait(),5)
                        except asyncio.TimeoutError:process.kill();await process.wait()
                        code=-1
            finally:finished.set();await watcher
        for session in sessions:session.save(out/('connection-'+str(session.index)))
        (out/'snapshots.json').write_text(json.dumps(snapshots,indent=2)+'\n')
        deadline=time.monotonic()+5
        while not (bridge/'2-closed.json').exists() and time.monotonic()<deadline:await asyncio.sleep(.05)
        labels=(out/'LABELS.BIN').read_bytes() if (out/'LABELS.BIN').exists() else b'';notices=[]
        if len(labels)==2566:
            magic,count,ticks=struct.unpack_from('<3H',labels)
            if magic==0x4e5a and 0<count<=16:notices=[labels[6+i*160:6+(i+1)*160:2].decode('cp437') for i in range(count)]
        before=(out/'BEFORE.BIN').read_bytes() if (out/'BEFORE.BIN').exists() else b''
        after=(out/'AFTER.BIN').read_bytes() if (out/'AFTER.BIN').exists() else b''
        checks=dict(DOS_normal_exit=code==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),
            hardware_restored=len(before)==42 and before==after,sources_unchanged=all(sha(ROOT/n)==h for n,h in frozen.items()),
            PRM_unchanged=(out/'TEST.PRM').read_bytes()==image,DOS_compiler_exact=(stage/'LOGON.ASX').exists() and (stage/'LOGON.ASX').read_bytes()==compile_source(script),
            both_script_logins=bool(snapshots) and snapshots[0]['first_login_trace']=='STARTAUTHREADY' and (stage/'LOGIN.LOG').read_bytes()==b'STARTAUTHREADY',
            two_connections=len(sessions)==2 and sessions[0].interrupted and not sessions[1].interrupted and all(s.done and not s.errors for s in sessions),
            stage_clean_before_second_login=len(snapshots)==2 and snapshots[1]['files']==[],
            real_carrier_notice=any('carrier lost' in n.lower() for n in notices),RX_complete_notice=any('RX complete' in n for n in notices),
            exact_retry=(recv/a.file).exists() and (recv/a.file).read_bytes()==payload,only_expected_file={p.name for p in recv.iterdir()}=={a.file},
            directory_two_connections=accounting_check(bytes(book),(out/'TEST.DIR').read_bytes(),3,2),no_post_saved=posts==post_count())
        if a.live_source:
            checks['runtime_source_only_startup']=initial_asx_absent and 'ASPCOMP LOGON.ASP LOGON.ASX' not in (out/'dosbox.conf').read_text() and not (out/'COMPILE.TXT').exists()
            checks['runtime_compile_files_retired']=not list(stage.glob('LPM*.TMP')) and not list(stage.glob('LPC*.*'))
        if guard_observer:
            from carrier_key_observer import decode
            try:
                guard_observer['trace']=decode(out/'LABELS.BIN')
                checks['guard_keyboard_vector_restored']=guard_observer['trace']['int16_restored']
            except (AssertionError,ValueError,FileNotFoundError,struct.error) as error:
                guard_observer['trace_error']=str(error)
                checks['guard_keyboard_vector_restored']=False
        errors=[];protocol={}
        try:
            assert len(sessions)==2,'Expected interrupted connection and redial'
            first,second=sessions
            offers=[h for h in scan(first.display) if h['type']==4];assert offers
            assert metadata(packet(first.display,offers[0]['end'],offers[0]['format'])['payload'])==(a.file,len(payload))
            assert not any(h['type']==11 for h in scan(first.display)),'First transfer reached EOF before deliberate loss'
            assert snapshots[0]['relay_seconds']<=first.interrupted_at
            retry=audit_batch(bytes(second.display),{a.file:payload})
            end_time=timestamp(second.trace,'bbs',retry['end']-1);cut=offset_after(second.trace,'dos',end_time);assert cut is not None
            post=bytes(second.keyboard).index(b'\x1b\x1bS\r',cut)+2;when=timestamp(second.trace,'dos',post)
            retry['controls']=audit_controls(retry,bytes(second.keyboard),second.trace,'bbs',when,False)
            after=offset_after(second.trace,'bbs',when);assert after is not None and (a.file+' ').encode() in second.display[after:]
            wire_evidence=[]
            for s in sessions:
                prefix=b'loc\r\x1b[8;24;80t';online=(bridge/(str(s.index)+'-serial-input.bin')).read_bytes();output=(bridge/(str(s.index)+'-serial-output.bin')).read_bytes()
                if s.interrupted:assert online.startswith(s.keyboard) and output.startswith(s.wire) and s.wire.startswith(s.display)
                else:assert online==s.keyboard and output==s.wire==s.display
                client,subs,_=telnet((bridge/(str(s.index)+'-telnet-input.bin')).read_bytes())
                assert online.startswith(prefix)
                if s.interrupted:assert client==online[len(prefix):]
                else:
                    # Remote logoff returns to the bridge's local menu. Its
                    # final QUIT requests hangup and must never reach the BBS.
                    assert online.endswith(b'QUIT\r') and client==online[len(prefix):-5]
                    returned=s.display.index(b'Connection closed by remote host.')
                    assert b'CONNECT> ' in s.display[returned:] and b'Goodbye.' in s.display[returned:]
                    assert timestamp(s.trace,'bbs',returned)<timestamp(s.trace,'dos',len(s.keyboard)-5)
                    assert b'+++ATH\r' not in s.keyboard
                assert [list(struct.unpack('>HH',sub[1:])) for sub in subs if sub[0]==31]==[[80,24]]
                assert json.loads((bridge/(str(s.index)+'-closed.json')).read_text())['source_unchanged']
                wire_evidence.append(dict(index=s.index,serial_received=len(s.keyboard),serial_delivered=len(s.display),upstream_read=len(s.wire),proxy_output=len(output),interrupted=s.interrupted))
            for item in retry['files']:item.pop('source')
            protocol=retry;checks['source_matching_retry_finish_search_raw_proxy']=True
        except (AssertionError,ValueError,TypeError,KeyError,FileNotFoundError) as error:
            site=traceback.extract_tb(error.__traceback__)[-1]
            errors.append(f'{type(error).__name__} at {Path(site.filename).name}:{site.lineno}: {error}')
            checks['source_matching_retry_finish_search_raw_proxy']=False;wire_evidence=[]
        rows=collect_log(out/'server-log-start.json',out/'server-log-capture')
        authenticated={r['sessionId'] for r in rows if r.get('msg')=='User "loclab" successfully logged in'}
        own=[r for r in rows if r.get('sessionId') in authenticated];(out/'server-session.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in own))
        checks['two_authenticated_sessions']=len(authenticated)==2
        result=dict(passed=all(checks.values()) and not errors,checks=checks,errors=errors,notices=notices,snapshots=snapshots,
            products=products,sources=frozen,runtime=str(runtime.relative_to(ROOT)),proxy=ready,payload_name=a.file,payload_bytes=len(payload),payload_sha256=sha(payload_path),
            protocol=protocol,wire_evidence=wire_evidence,scope=__doc__+' Actual DOS'+a.cpu+' COM3/IRQ5,19200/HARD,source-built ASPECT/compiler,stock owned helper; one parent two automatic script logins. Fixture S12=25,not physical modem configuration.')
        result['transfer_wait_ms']=a.transfer_wait_ms
        result['startup_probe']=a.startup_probe
        result['exec_probe']=a.exec_probe
        if a.exec_probe:
            path=out/'EXECTRAC.BIN'
            if path.exists():
                raw=path.read_bytes();magic,count,restored=struct.unpack_from('<3H',raw);assert magic==0x4b48 and count<=16
                result['exec_trace']=dict(restored=restored,records=[dict(largest_free_paragraphs=struct.unpack_from('<H',raw,390+i*2)[0],psp=struct.unpack_from('<H',raw,422+i*100)[0],environment=struct.unpack_from('<H',raw,424+i*100)[0],mcbs=[struct.unpack_from('<3H',raw,426+i*100+j*6) for j in range(16)],function=struct.unpack_from('<H',raw,6+i*24)[0],AX=struct.unpack_from('<H',raw,8+i*24)[0],carry=struct.unpack_from('<H',raw,10+i*24)[0],name=raw[12+i*24:30+i*24].split(b'\0',1)[0].decode('cp437')) for i in range(count)])
        result['cpu']=a.cpu
        result['explicit_UMB']=a.umb
        result['live_source']=a.live_source
        result['startup_source']=startup
        if guard_observer:result['guard_observer']=guard_observer
        (out/'carrier-checks.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(dict(passed=result['passed'],checks=checks,errors=errors,notices=notices),indent=2))
        return 0 if result['passed'] else 1
    finally:
        proxy.terminate()
        try:proxy.wait(timeout=5)
        except subprocess.TimeoutExpired:proxy.kill();proxy.wait()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['runtime','terminal','runner','compiler']:p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--exec-probe',action='store_true',help='Owned passive real DOS EXEC/result diagnostic; not ordinary acceptance')
    p.add_argument('--startup-probe',action='store_true',help='Diagnostic first startup only; does not satisfy carrier/retry gates')
    p.add_argument('--cpu',choices=['8086','386'],default='8086')
    p.add_argument('--umb',action='store_true',help='Use explicit XMS/no-EMS/UMB DOS layout for interpreter memory admission')
    p.add_argument('--live-source',action='store_true',help='Omit bootstrap ASX compilation; require attached ASPECT to compile source while the full parent runs')
    p.add_argument('--file',required=True);p.add_argument('--label',required=True);p.add_argument('--witness',action='store_true')
    p.add_argument('--transfer-wait-ms',type=int,choices=[60000,150000],default=60000)
    p.add_argument('--guard-observer-check',type=Path,help='Explicit passive diagnostic; require matching current transparency report and identical TSR footprint')
    raise SystemExit(asyncio.run(run(p.parse_args())))
