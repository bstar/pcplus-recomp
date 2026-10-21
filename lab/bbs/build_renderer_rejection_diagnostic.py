#!/usr/bin/env python3
"""Build an isolated diagnostic terminal; preserve all renderer rejections.

Run inside tools/dev. No product worktree file is modified. RGUARD records
are foreground-only DOS file writes, so this binary is diagnostic evidence,
not a timing-equivalent or accepted production terminal.
"""
import argparse
import io
import json
import subprocess
import sys
import tarfile
from pathlib import Path
from audio_synchronet import ROOT, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', default='HEAD')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--boundary', action='store_true', help='Also record native unsupported-service boundaries as 0x8000 | service')
    parser.add_argument('--runner', action='store_true', help='Also build ASPECT with first-error state and command-line logging')
    parser.add_argument('--keys', action='store_true', help='Record raw keys dispatched by the child using 0x4000 | key')
    args = parser.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(ROOT / 'build') and not out.exists()
    commit = subprocess.check_output(
        ['git', 'rev-parse', args.revision + '^{commit}'], cwd=ROOT, text=True).strip()
    archive = subprocess.check_output(['git', 'archive', commit], cwd=ROOT)
    out.mkdir(parents=True)
    (out / 'source.tar').write_bytes(archive)
    source = out / 'source'
    source.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as files:
        files.extractall(source, filter='data')
    policy = source / 'src/aspect/renderer_policy.c'
    original = policy.read_text()
    assert original.count('#include <dos.h>') == 1
    assert 'aspect_render_diagnostic_reject' not in original
    guarded = original.replace('#include <dos.h>', '#include <dos.h>\nextern unsigned __cdecl aspect_render_diagnostic_reject(unsigned);')
    count = guarded.count('return 3;')
    assert count > 0
    policy.write_text(guarded.replace('return 3;', 'return aspect_render_diagnostic_reject(__LINE__);'))
    recorder = ROOT / 'lab/bbs/renderer_rejection_recorder.asm'
    assembly = source / 'src/terminal/aspect_renderer.asm'
    original_assembly = assembly.read_text()
    if args.boundary:
        marker = 'terminal_render_unsupported:\n mov [cs:render_unsupported],ax\n'
        assert original_assembly.count(marker) == 1
        original_assembly = original_assembly.replace(marker, marker + ''' push ax
 or ax,0x8000
 push ax
 call _aspect_render_diagnostic_reject
 add sp,2
 pop ax
''')
    if args.keys:
        marker = '.key:\n cmp word [_script_handoff+22],0\n jne .serial\n'
        assert original_assembly.count(marker) == 1
        original_assembly = original_assembly.replace(marker, marker + ''' push ax
 mov ax,bx
 or ax,0x4000
 push ax
 call _aspect_render_diagnostic_reject
 add sp,2
 pop ax
''')
    assembly.write_text(original_assembly + '\n' + recorder.read_text())
    with (out / 'build.log').open('wb') as log:
        subprocess.run([sys.executable, str(source / 'standalone/build_terminal.py')],
                       cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
    terminal = source / 'build/terminal/TERMINAL.EXE'
    instrumented = [policy, assembly]
    if args.runner:
        runtime = source / 'src/aspect/runtime.c'
        text = runtime.read_text()
        marker = 'void runtime_set_error(unsigned error)\n{\n'
        assert text.count(marker) == 1
        text = '#include <stdio.h>\n#include "serial.h"\n' + text
        text = text.replace(marker, marker + r'''
    if(!runtime_error && error){
        unsigned record[13];
        long ticks;
        FILE *probe;
        record[0]=0x4152;record[1]=error;record[2]=runtime_error;
        record[3]=runtime_last_opcode;record[4]=runtime_steps;
        record[5]=aspect_serial_active;record[6]=aspect_render_active();
        record[7]=runtime_serial_error;record[8]=runtime_serial_pacing_error;
        record[9]=aspect_serial_rx_count;
        record[10]=runtime_when_last_key;
        _bios_timeofday(_TIME_GETCLOCK,&ticks);
        record[11]=(unsigned)ticks;record[12]=(unsigned)(ticks>>16);
        probe=fopen("D:\\AERROR.BIN","ab");
        if(probe){fwrite(record,sizeof(record),1,probe);fclose(probe);}
    }
''')
        runtime.write_text(text)
        driver = source / 'src/aspect/runner.c'
        text = driver.read_text()
        marker = ' const char *serial_option=0;\n'
        assert text.count(marker) == 1
        text = text.replace(marker, marker + r'''
 {FILE *probe=fopen("D:\\AARGS.LOG","ab");
  if(probe){for(i=0;i<(unsigned)argc;++i)fprintf(probe,"ARG %u: %s\n",i,argv[i]);fclose(probe);}}
''')
        driver.write_text(text)
        with (out / 'runner-build.log').open('wb') as log:
            subprocess.run([sys.executable, str(source / 'standalone/build_aspect_runner.py')],
                           cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, check=True)
        instrumented += [runtime, driver]
    result = dict(base_commit=commit, terminal_sha256=sha(terminal), boundary_instrumented=args.boundary,key_instrumented=args.keys,
                  archive_sha256=sha(out / 'source.tar'), guard_sites=count,
                  instrumented_sources={str(p.relative_to(source)): sha(p) for p in instrumented},
                  inputs={str(p.relative_to(ROOT)): sha(p) for p in (Path(__file__).resolve(), recorder)},
                  scope='Isolated source-only renderer rejection diagnostic; guards still return 3. Foreground file I/O changes timing. No compatibility acceptance.')
    if args.runner:
        result['runner_sha256'] = sha(source / 'build/aspect-runner/ASPECT.EXE')
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
