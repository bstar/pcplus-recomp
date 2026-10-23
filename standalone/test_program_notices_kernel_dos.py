#!/usr/bin/env python3
"""Boot pinned FreeDOS and check natural EXEC rejection, notices and later reuse."""
import argparse,hashlib,json,os,re,shutil,socket,struct,subprocess,threading,zipfile
from pathlib import Path
from test_kernel_critical_dos import ARCHIVE_SHA,URL
from test_program_notices_dos import ROOT,PAYLOAD,scripts

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',required=True)
    args=parser.parse_args();assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    out=ROOT/'build/program-notices-kernel'/args.label;out.mkdir(parents=True,exist_ok=False)
    archive=ROOT/'build/freedos-kernel-lab/FD14-FloppyEdition.zip';assert sha(archive)==ARCHIVE_SHA
    binary=ROOT/'build/aspect-notice-fault/ASPECT.EXE';manifest=json.loads((binary.parent/'manifest.json').read_text())
    assert sha(binary)==manifest['binary_sha256'] and not manifest['original_inputs']
    sources={**manifest['sources'],**{name:sha(ROOT/name) for name in ['standalone/test_program_notices_kernel_dos.py','standalone/test_kernel_critical_dos.py','standalone/test_program_notices_dos.py','standalone/notice_success_child.asm','src/aspect/compiler.py']}}
    for name,digest in sources.items():
        assert sha(ROOT/name)==digest,name
        dest=out/'sources'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dest)
    from compiler import compile_source
    first,second=scripts(success=True);first=first.replace('run "ABSENT.COM"','run "BADMZ.EXE"')
    for name,source in [('FIRST',first),('RECOVER',second)]:
        (out/(name+'.ASP')).write_text(source);(out/(name+'.ASX')).write_bytes(compile_source(source))
    shutil.copyfile(binary,out/'ASPECT.EXE');# A safe exit99 body is unreachable when the missing relocation is rejected.
    malformed=struct.pack('<14H',0x5a4d,38,1,1,2,0,0xffff,0,0x100,0,0,0,0x1000,0)+bytes(4)+bytes.fromhex('b8634ccd21')+b'\x90'
    (out/'BADMZ.EXE').write_bytes(malformed)
    valid=bytearray(malformed);struct.pack_into('<H',valid,6,0)
    (out/'VALID.EXE').write_bytes(valid)
    for i in range(5):(out/f'SLOT{i}.BIN').write_bytes(b'SEED0')
    subprocess.run(['nasm','-fbin',str(out/'sources/standalone/notice_success_child.asm'),'-o',str(out/'SUCCESS.COM')],check=True)
    # This independent real DOS witness runs before the application and records
    # both reported DOS version and the kernel's true-version API unchanged.
    version=r'''BITS 16
CPU 8086
ORG 100h
mov ax,0x3000
int 0x21
mov [data],ax
mov [data+2],bx
mov ax,0x3306
int 0x21
mov [data+4],bx
mov [data+6],dx
mov dx,name
xor cx,cx
mov ah,0x3c
int 0x21
jc failed
mov bx,ax
mov dx,data
mov cx,8
mov ah,0x40
int 0x21
jc failed
cmp ax,8
jne failed
mov ah,0x3e
int 0x21
jc failed
mov ax,0x4c00
int 0x21
failed: mov ax,0x4c63
int 0x21
data: times 8 db 0
name: db 'VERSION.BIN',0
'''
    (out/'version.asm').write_text(version);subprocess.run(['nasm','-fbin',str(out/'version.asm'),'-o',str(out/'VERSION.COM')],check=True)
    boot=out/'boot.img'
    with zipfile.ZipFile(archive) as z:boot.write_bytes(z.read('144m/x86BOOT.img'))
    template=sha(boot)
    config='DOS=LOW\r\nFILES=30\r\nBUFFERS=20\r\nLASTDRIVE=A\r\nSHELL=A:\\FREEDOS\\BIN\\COMMAND.COM A:\\FREEDOS\\BIN /E:2048 /P=A:\\FDAUTO.BAT\r\n'
    auto='@echo off\r\nA:\\VERSION\r\nset PCPNOTICE=0N1NN\r\nA:\\ASPECT FIRST.ASX 60000 /S1:0003:03:H >OUTPUT.TXT\r\nif errorlevel 1 goto fail\r\nA:\\VALID.EXE\r\nif errorlevel 100 goto fail\r\nif not errorlevel 99 goto fail\r\necho VALID>VALID.OK\r\necho PASS>PASS.TXT\r\ngoto done\r\n:fail\r\necho FAIL>FAIL.TXT\r\n:done\r\nA:\\FREEDOS\\BIN\\FDAPM.COM POWEROFF\r\n'
    (out/'FDCONFIG.SYS').write_bytes(config.encode());(out/'FDAUTO.BAT').write_bytes(auto.encode())
    names=['ASPECT.EXE','VALID.EXE','BADMZ.EXE','SUCCESS.COM','VERSION.COM','FIRST.ASX','RECOVER.ASX','FDCONFIG.SYS','FDAUTO.BAT']+[f'SLOT{i}.BIN' for i in range(5)]
    for name in names:subprocess.run(['mcopy','-o','-i',str(boot),str(out/name),'::'+name],check=True)
    server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);server.settimeout(.2)
    stop=threading.Event();wire=bytearray();errors=[];sent=[]
    def peer():
        try:
            connection=None
            while not stop.is_set():
                try:connection,_=server.accept();break
                except socket.timeout:continue
            if connection is None:return
            with connection:
                connection.settimeout(.1)
                while not stop.is_set():
                    try:data=connection.recv(4096)
                    except socket.timeout:continue
                    if not data:break
                    wire.extend(data)
                    for trigger,packet in [(b'R',PAYLOAD),(b'P',b'READY!'),(b'F',b'END')]:
                        if trigger in wire and trigger not in sent:connection.sendall(packet);sent.append(trigger)
        except OSError as error:
            if not stop.is_set():errors.append(str(error))
    thread=threading.Thread(target=peer,daemon=True);thread.start()
    cfg=f'''[sdl]
output=surface
[dosbox]
memsize=8
apmbios=true
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[mixer]
nosound=true
[serial]
serial1=nullmodem server:127.0.0.1 port:{server.getsockname()[1]} transparent:1 rxdelay:200 txdelay:1
serial2=disabled
serial3=disabled
serial4=disabled
[autoexec]
imgmount a "{boot}" -t floppy
boot -l a
'''
    (out/'dosbox.conf').write_text(cfg);code=None;timeout=False
    try:
        with (out/'dosbox.log').open('w') as log:
            try:code=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],cwd=out,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),stdout=log,stderr=log,timeout=45).returncode
            except subprocess.TimeoutExpired:timeout=True
    finally:stop.set();server.close();thread.join(2)
    (out/'wire.bin').write_bytes(wire)
    for name in ['NOTICE.BIN','VERSION.BIN','PASS.TXT','FAIL.TXT','SUCCESS.OK','VALID.OK','VALID.EXE','WRITE.BIN','OUTPUT.TXT','ASPECT.EXE','BADMZ.EXE']:
        subprocess.run(['mcopy','-o','-i',str(boot),'::'+name,str(out/name)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    raw=(out/'NOTICE.BIN').read_bytes() if (out/'NOTICE.BIN').exists() else b'';w=struct.unpack('<62H',raw) if len(raw)==124 else ()
    raw=(out/'VERSION.BIN').read_bytes() if (out/'VERSION.BIN').exists() else b'';v=struct.unpack('<4H',raw) if len(raw)==8 else ()
    checks=dict(emulator_exit=code==0 and not timeout,real_FreeDOS=bool(v) and v[0]==v[2]==0x0a07 and v[1]>>8==0xfd,
        DOS_success=(out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),report=bool(w),natural_malformed_rejection=bool(w) and w[4:7]==(0,1,22) and w[31]==13,
        normal_EXEC_route=bool(w) and w[32:37]==(0,0,0,1,3),actual_popup=bool(w) and w[11]==1 and w[7] in (0,1,2),
        first_cleanup=bool(w) and w[8:11]==(0,1,1) and w[14:18]==(1,65535,0,1),
        recovery_VM=bool(w) and w[18:20]==(0,2) and w[20] in (0,1,2) and w[21:31]==(0,1,1,1,0,0,1,0,0,0),
        exact_queued_input=bool(w) and w[12:14]==(508,508) and bytes(wire)==b'RPF',all_peer_stages=sent==[b'R',b'P',b'F'] and not errors,
        retained_streams=(out/'WRITE.BIN').exists() and (out/'WRITE.BIN').read_bytes()==b'FIRSTSECOND',
        later_success_child=(out/'SUCCESS.OK').exists() and (out/'SUCCESS.OK').read_bytes()==b'OK',
        balanced_windows=bool(w) and w[59:62]==(2,2,0),binary_unchanged=sha(out/'ASPECT.EXE')==manifest['binary_sha256'],malformed_fixture_unchanged=(out/'BADMZ.EXE').read_bytes()==malformed,
        valid_control=(out/'VALID.OK').exists() and (out/'VALID.EXE').read_bytes()==valid)
    for name,digest in sources.items():assert sha(ROOT/name)==digest,name
    report=dict(passed=all(checks.values()),checks=checks,notice_words=w,DOS_version=v,archive_url=URL,archive_sha256=ARCHIVE_SHA,boot_template_sha256=template,binary_sha256=manifest['binary_sha256'],sources=sources,peer_errors=errors,
        captures_sha256={p.name:sha(p) for p in out.iterdir() if p.is_file() and p.suffix!='.img'},
        scope='Booted pinned FreeDOS1.4/7.10 kernel, ordinary EXEC mode0, MZ executable with a missing relocation entry rejected as DOS13/CRT22; identical executable with zero relocations exits99. No unsupported EXEC mode, patched kernel or original PCPlus input. Raw CLI with actual popup,508 peer bytes, second VM/error and successful child. Natural DOS11/CRT8, other malformed headers, DOS kernels, attached parent and physical modem are not established.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],checks=checks,words=w,version=v)),flush=True)
    return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
