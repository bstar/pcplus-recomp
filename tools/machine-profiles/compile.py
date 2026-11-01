#!/usr/bin/env python3
"""Compile independent DOS machine configs into a two-level DOS6 boot menu."""
import argparse
import json
import re
from pathlib import Path

MACHINES = [('GREEN','G','GREENTREE - 386SX / AdLib / Cirrus'),('DTK','D','DTK - 386DX / Vibra16 / Cirrus'),('CHIPS','C','CHIPS - 386SX / AdLib / ET4000'),('ENOS','E','ENOS - 486DX4 / SB16 / ET6000'),('BAH','B','BAH - P75 / Vibra16 / Cirrus')]

def read_sections(path):
    sections=[]; name='COMMON'; lines=[]
    for line in path.read_bytes().decode('cp437').splitlines():
        match=re.fullmatch(r'\s*\[([^]]+)\]\s*',line)
        if match:
            if lines: sections.append((name,lines))
            name=match[1].upper();lines=[]
        else: lines.append(line)
    if lines:sections.append((name,lines))
    return sections

def compile_profiles(root,output,default='GREEN'):
    output.mkdir(parents=True,exist_ok=True)
    config=['REM Generated machine menu; edit per-machine CONFIG.SYS and rebuild.','[menu]']
    for machine,_,title in MACHINES:config.append(f'submenu={machine},{title}')
    config+= [f'menudefault={default},5','']
    routes=[]; bodies=[]; selected=[]
    for machine,prefix,title in MACHINES:
        directory=root/machine
        for name in ['CONFIG.SYS','AUTOEXEC.BAT','SYSTEM.INI']:
            if not (directory/name).is_file():raise ValueError(f'Missing {machine}/{name}')
        sections=read_sections(directory/'CONFIG.SYS')
        mapping={name:lines for name,lines in sections if name!='COMMON'}
        if 'MENU' not in mapping:raise ValueError(f'{machine} needs a [menu] section')
        modes=[]
        for line in mapping['MENU']:
            m=re.match(r'(?i)^\s*menuitem\s*=\s*([^,\s]+)\s*,(.*)',line)
            if m:modes.append((m[1].upper(),m[2].strip()))
        if not 1<=len(modes)<=9:raise ValueError('DOS menus support one to nine visible choices')
        mode_default='EM' if any(m[0]=='EM' for m in modes) else modes[0][0]
        config += [f'[{machine}]',f'REM {title}']
        for mode,label in modes:
            if mode not in mapping:raise ValueError(f'{machine}: missing [{mode}]')
            item=prefix+mode
            if len(item)>8:raise ValueError('Menu identifier exceeds DOS eight-character limit')
            config.append(f'menuitem={item},{label}')
            routes.append(f'IF "%CONFIG%"=="{item}" GOTO {item}')
            bodies += [f':{item}',f'SET MACHINE={machine}',f'SET CONFIG={mode}','GOTO END']
            def expand(lines,seen):
                result=[]
                for line in lines:
                    include=re.match(r'(?i)^\s*include\s*=\s*([^\s]+)\s*$',line)
                    if include:
                        target=include[1].upper()
                        if target in seen or target not in mapping:raise ValueError('Invalid or recursive INCLUDE')
                        result+=expand(mapping[target],seen|{target})
                    else:result.append(line)
                return result
            flattened=[]
            for name,lines in sections:
                if name=='COMMON' or name==mode:flattened+=expand(lines,{mode})
            selected += [f'[{item}]']+flattened+['']
        config += [f'menudefault={prefix+mode_default},10','']
    def write(name,lines):
        (output/name).write_bytes(('\r\n'.join(lines)+'\r\n').encode('cp437'))
    write('CONFIG.SYS',config+selected)
    legacy=[f'IF "%CONFIG%"=="{mode}" GOTO G{mode}' for mode in ['EM','XM','EMC','XMC','CM','E','X','C','N']]
    write('ROUTE.BAT',['@ECHO OFF','SET MACHINE=']+legacy+routes+['GOTO END']+bodies+[':END'])
    write('AUTOEXEC.BAT',[
        '@ECHO OFF','PROMPT $p$g','PATH C:\\WINDOWS;C:\\DOS','SET TEMP=C:\\DOS',
        'CALL C:\\BOOT\\ROUTE.BAT','IF "%MACHINE%"=="" GOTO BAD',
        'ECHO Machine: %MACHINE%   Boot mode: %CONFIG%',
        'CALL C:\\BOOT\\WINSEL.BAT','IF "%WINERR%"=="1" GOTO WINBAD',
        'CALL C:\\BOOT\\%MACHINE%\\AUTOEXEC.BAT','GOTO END',
        ':BAD','ECHO Unknown machine selection. Startup stopped.','GOTO END',
        ':WINBAD','ECHO Windows profile switch failed. Startup stopped; backups are in C:\\BOOT.',
        ':END'])
    # DOS COPY may preserve an earlier errorlevel; clear FC's mismatch result
    # with this owned five-byte DOS exit-status helper (mov ax,4c00h; int21h).
    (output/'ZERO.COM').write_bytes(bytes.fromhex('b8004ccd21'))
    write('WINSEL.BAT',[
        '@ECHO OFF','SET WINERR=1','SET WINMACH=','C:\\BOOT\\ZERO.COM',
        'IF EXIST C:\\BOOT\\WINCUR.BAT CALL C:\\BOOT\\WINCUR.BAT',
        'IF "%WINMACH%"=="%MACHINE%" GOTO SAME','GOTO SWITCH',
        ':SAME','C:\\DOS\\FC.EXE /B C:\\BOOT\\%MACHINE%\\SYSTEM.INI C:\\BOOT\\WINLAST.INI > NUL',
        'IF ERRORLEVEL 2 GOTO END','IF ERRORLEVEL 1 GOTO APPLY','GOTO READY',
        ':SWITCH','IF "%WINMACH%"=="" GOTO APPLY',
        'IF NOT EXIST C:\\BOOT\\%WINMACH%\\SYSTEM.INI GOTO END',
        'COPY /Y C:\\WINDOWS\\SYSTEM.INI C:\\BOOT\\%WINMACH%\\SYSTEM.INI > NUL',
        'IF ERRORLEVEL 1 GOTO END',
        ':APPLY','IF NOT EXIST C:\\BOOT\\%MACHINE%\\SYSTEM.INI GOTO END',
        'C:\\BOOT\\ZERO.COM',
        'COPY /Y C:\\WINDOWS\\SYSTEM.INI C:\\BOOT\\SYSBEFOR.INI > NUL',
        'IF ERRORLEVEL 1 GOTO END',
        'IF NOT EXIST C:\\BOOT\\%MACHINE%\\WINSYS\\*.* GOTO INI',
        'COPY /Y C:\\BOOT\\%MACHINE%\\WINSYS\\*.* C:\\WINDOWS\\SYSTEM\\ > NUL',
        'IF ERRORLEVEL 1 GOTO END',
        ':INI','COPY /Y C:\\BOOT\\%MACHINE%\\SYSTEM.INI C:\\WINDOWS\\SYSTEM.INI > NUL',
        'IF ERRORLEVEL 1 GOTO END',
        'COPY /Y C:\\BOOT\\%MACHINE%\\SYSTEM.INI C:\\BOOT\\WINLAST.INI > NUL',
        'IF ERRORLEVEL 1 GOTO END',
        'ECHO SET WINMACH=%MACHINE%>C:\\BOOT\\WINCUR.BAT',
        'IF ERRORLEVEL 1 GOTO END',
        ':READY','SET WINERR=',':END'])
    write('CHOOSE.BAT',['@ECHO OFF','ECHO Machine selection is now part of the DOS startup menu.',
                         'ECHO Reboot, choose the machine, then choose its boot mode.',
                         'ECHO Per-machine files are in C:\\BOOT\\GREEN, DTK, CHIPS, ENOS, BAH.',
                         'ECHO CONFIG.SYS changes require rebuilding the combined boot menu.'])
    (output/'menu-map.json').write_text(json.dumps({'default':default,'machines':[m[0] for m in MACHINES],'choices':len(routes)},indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('profiles',type=Path);p.add_argument('output',type=Path);p.add_argument('--default',choices=[m[0] for m in MACHINES],default='GREEN');a=p.parse_args();compile_profiles(a.profiles,a.output,a.default)
