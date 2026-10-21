#!/usr/bin/env python3
"""Actual DOS test of upload-helper BIOS phases, cursor focus and failure exit."""
import argparse,json,os,struct,subprocess
from pathlib import Path
from synthmodem_vm_control import ROOT,sha

FILE_KEYS=[0x3c00,0x3c00,0x2044,0x273a,0x2b5c,0x1f53,0x1245,0x314e,0x2044,0x2b5c,
           0x1e41,0x1655,0x2044,0x1749,0x184f,0x1655,0x1950,0x342e,0x3042,0x1749,0x314e,0x1c0d]
QUERY=[0x1e41,0x1655,0x2044,0x1749,0x184f,0x1655,0x1950,0x342e,0x3042,0x1749,0x314e,0x1c0d,0x1c0d]


def run(out,failure,cancel=False,retry=False):
    out.mkdir()
    expected=[0x1f00,*FILE_KEYS]
    if cancel:
        phases='mov ax,0b800h\nmov es,ax\nmov word [es:3680+70*2],1f31h\nmov cx,1\ncall keys\nmov si,canceled\ncall screen\nmov cx,1\ncall keys\nmov si,menu\ncall screen\nmov cx,2\ncall keys\nmov si,search\ncall screen\nmov cx,13\ncall keys\nmov si,cancel_list\ncall screen\nmov cx,1\ncall keys\n'
        expected+=[0x011b,0x011b,0x1f53,0x1c0d,0x1950,0x2e43,0x2d58,0x1454,0x1245,0x1f53,0x1454,0x342e,0x3042,0x1749,0x314e,0x1c0d,0x1c0d,0x2d00]
    elif failure:
        phases='mov si,failed\ncall screen\nmov cx,1\ncall keys\n'
        expected+=[0x2d00]
    else:
        phases='''mov si,checker
call screen
mov cx,1
call keys
mov si,details
call screen
mov dx,0505h
call cursor
mov cx,1
call keys
mov dx,0833h
call cursor
mov cx,1
call keys
mov dx,0841h
call cursor
mov cx,1
call keys
mov dx,0d37h
call cursor
mov cx,1
call keys
mov si,pause
call screen
mov cx,1
call keys
mov si,menu
call screen
mov cx,2
call keys
mov si,search
call screen
mov cx,13
call keys
mov si,list
call screen
mov cx,1
call keys
'''
        expected+=[0x1c0d,0x0f09,0x0f09,0x0f09,0x1c0d,0x1c0d,0x1f53,0x1c0d,*QUERY,0x2d00]
    if retry:
        phases='mov ax,0b800h\nmov es,ax\nmov word [es:3680+70*2],1f31h\nmov cx,1\ncall keys\nmov si,canceled\ncall screen\nmov cx,1\ncall keys\nmov si,menu\ncall screen\nmov cx,2\ncall keys\nmov si,options\ncall screen\nmov cx,4\ncall keys\nmov si,protocol\ncall screen\nmov cx,1\ncall keys\nmov si,banner\ncall screen\nmov cx,1\ncall keys\nmov si,retry_local\ncall screen\nmov cx,20\ncall keys\nmov si,sending\ncall screen\ncall quiet\n'+phases
        prefix=1+len(FILE_KEYS)
        expected=expected[:prefix]+[0x011b,0x011b,0x1655,0x1c0d,0x0f09,0x0f09,0x0f09,0x1c0d,0x1c0d,0x1f00,*FILE_KEYS[2:]]+expected[prefix:]
    count=len(expected)*2
    code='''bits 16
cpu 8086
org 100h
mov ax,3
int 10h
mov si,login
call screen
call quiet
mov si,banner
call screen
mov cx,1
call keys
mov si,local
call screen
mov cx,22
call keys
mov si,sending
call screen
call quiet
'''+phases+f'''mov ah,3ch
xor cx,cx
mov dx,filename
int 21h
jc fail
mov bx,ax
mov ah,40h
mov cx,{count}
mov dx,values
int 21h
cmp ax,{count}
jne fail
mov ah,3eh
int 21h
mov ax,4c00h
int 21h
fail: mov ax,4c01h
int 21h
keys:
xor ah,ah
int 16h
mov bx,[key_cursor]
mov [bx],ax
add word [key_cursor],2
loop keys
ret
quiet:
mov ax,40h
mov es,ax
mov dx,[es:6ch]
.wait:
mov ax,[es:6ch]
sub ax,dx
cmp ax,6
jb .wait
mov ah,1
int 16h
jnz fail
ret
cursor:
mov ah,2
xor bh,bh
int 10h
ret
screen:
mov ax,0b800h
mov es,ax
xor di,di
mov ax,0720h
mov cx,2000
rep stosw
xor di,di
.text:
lodsb
or al,al
jz .done
mov ah,7
stosw
jmp .text
.done: ret
login: db 'LOGIN',0
banner: db 'No socket descriptor specified, using STDIO',0
local: db 'Upload: XMODEM/1K',0
sending: db 'Sending ZMODEM',0
checker: db 'UPLOAD CHECKER >> smash your keyboard <<',0
details: db 'UPLOAD DETAILS - AUDIOUP.BIN continue',0
pause: db 'Achievement >> smash your keyboard <<',0
menu: db 'File Base ...cmd:',0
search: db 'FILE SEARCH ESC : cancel',0
list: db 'QUEUED AUDIOUP.BIN',0
failed: db 'TX timeout',0
canceled: db 'TX canceled',0
cancel_list: db 'QUEUED PCXTEST.BIN',0
options: db '(blind - filename ignored)',0
protocol: db 'PROTOCOL SELECTION',0
retry_local: db 'ZMODEM filespec:',0
filename: db 'KEYS.BIN',0
key_cursor: dw values
values: times {count} db 0
'''
    (out/'probe.asm').write_text(code)
    for flags,source,name in [(['-DAUDIO_UPLOAD_FAST_TEST=1']+(['-DAUDIO_UPLOAD_CANCEL=1'] if cancel or retry else [])+(['-DAUDIO_UPLOAD_RETRY=1'] if retry else []),ROOT/'lab/bbs/audio_upload_keys.asm','EXITKEY.COM'),
                              ([],out/'probe.asm','PROBE.COM'),([],ROOT/'lab/bbs/audio_get_vector.asm','KEYVEC.COM')]:
        subprocess.run(['nasm','-fbin',*flags,str(source),'-o',str(out/name)],check=True)
    (out/'dosbox.conf').write_text(f'''[sdl]
output=surface
[cpu]
core=normal
cputype=8086
cycles=fixed 6000
[autoexec]
@echo off
mount c "{out}"
mount d "{out}"
c:
EXITKEY
PROBE
if errorlevel 1 goto fail
echo PASS>PASS.TXT
goto done
:fail
echo FAIL>FAIL.TXT
:done
KEYVEC
exit
''')
    with (out/'dosbox.log').open('w') as log:
        result=subprocess.run(['dosbox-x','-fastlaunch','-nogui','-conf',str(out/'dosbox.conf')],stdout=log,stderr=log,
            timeout=25,env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'))
    read=lambda name:(out/name).read_bytes() if (out/name).exists() else b''
    checks={'probe_normal_exit':result.returncode==0 and (out/'PASS.TXT').exists() and not (out/'FAIL.TXT').exists(),
        'exact_phased_BIOS_keys':read('KEYS.BIN')==struct.pack('<'+'H'*len(expected),*expected),
        'timer_vector_restored':len(read('KEYOLD.BIN'))==4 and read('KEYOLD.BIN')==read('KEYNEW.BIN')}
    return {'mode':'retry' if retry else 'cancel' if cancel else 'failure' if failure else 'success','passed':all(checks.values()),'checks':checks,
        'expected_words':len(expected),'probe_source_sha256':sha(out/'probe.asm')}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
    rows=[run(out/label,failure) for label,failure in [('success',False),('failure',True)]]
    rows.append(run(out/'cancel',False,cancel=True))
    rows.append(run(out/'retry',False,retry=True))
    result={'passed':all(r['passed'] for r in rows),'cases':rows,
        'inputs':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__).resolve(),ROOT/'lab/bbs/audio_upload_keys.asm',ROOT/'lab/bbs/audio_get_vector.asm']},
        'scope':'Actual DOS BIOS-only observer test with independent synthetic visible phases/cursor and shortened test-only delays. No premature login/active-transfer keys, exact local selection/form/post-search sequence, bounded visible-failure exit and timer restoration. No product-state access, real upload, BBS/audio or physical acceptance.'}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert result['passed']


if __name__=='__main__':main()
