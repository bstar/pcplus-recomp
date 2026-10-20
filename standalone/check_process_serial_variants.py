#!/usr/bin/env python3
"""Verify mixed guarded/ordinary serial objects cannot link the process owner."""
import json,subprocess
from pathlib import Path
from build_process_serial import ROOT,OUT,sha


def main():
    destination=OUT/'variant-check';destination.mkdir(exist_ok=True)
    subprocess.run(['wcc','-q','-bt=dos','-0','-ms','-ecc','-s','-w4','-we',
        '-i='+str(ROOT/'src/aspect'),'-fo='+str(destination/'serial_normal.o'),
        str(ROOT/'src/aspect/serial.c')],cwd=destination,check=True)
    subprocess.run(['nasm','-fobj','-I'+str(ROOT/'reconstruction/uart')+'/',
        str(ROOT/'src/aspect/serial_backend.asm'),'-o',str(destination/'serial_backend_normal.obj')],check=True)
    manifest=json.loads((ROOT/'build/native-process/manifest.json').read_text())
    linked=[OUT/'serial.o',OUT/'process_serial.o',OUT/'native_process.o',OUT/'process_serial_diagnostic.o',
        OUT/'uart.obj',OUT/'api.obj',OUT/'serial_backend.obj',OUT/'process_serial.obj']
    linked += [ROOT/'build/native-process'/(Path(u['file']).stem+'.obj') for u in manifest['units']]
    linked.append(ROOT/'build/native-process/native_process_state.obj')
    reports=[]
    for label,old,new,symbol in [('C-guard',OUT/'serial.o',destination/'serial_normal.o','aspect_process_serial_c_guards'),
            ('ASM-guard',OUT/'serial_backend.obj',destination/'serial_backend_normal.obj','serial_process_guard_level')]:
        objects=[new if p==old else p for p in linked]
        result=subprocess.run(['wcl','-q','-bt=dos','-0','-ms','-ecc','-s','-k8192',
            '-fe='+str(destination/(label+'.EXE')),*map(str,objects)],cwd=destination,capture_output=True,text=True)
        log=destination/(label+'.log');log.write_text(result.stdout+result.stderr)
        assert result.returncode!=0 and symbol in log.read_text(),log.read_text()
        reports.append(dict(case=label,rejected=True,missing_symbol=symbol,exit_code=result.returncode,
            log_sha256=sha(log),object_sha256=sha(new)))
    report=dict(passed=True,cases=reports,binary_sha256=sha(OUT/'PSERIAL.EXE'),
        checker_sha256=sha(Path(__file__)),scope='Actual linker rejects mixed old/new C and ASM serial variants. No DOS executable is launched.')
    (destination/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Mixed serial variants: both expected link rejections PASS')


if __name__=='__main__':main()
