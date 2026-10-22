#!/usr/bin/env python3
"""Build a separate ASPECT observer of matcher input and script/keyboard TX.

Generated adapters instrument source functions only. The production runner and
its manifest are neither rebuilt nor replaced. Trace IO can affect timing.
"""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/aspect-match-trace'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    baseline={n:sha(ROOT/'build/aspect-runner'/n) for n in ('ASPECT.EXE','manifest.json')}
    OUT.mkdir(parents=True,exist_ok=True)
    header='void match_trace(unsigned kind,unsigned value);\nvoid match_trace_close(unsigned result);\n'
    (OUT/'match_trace.h').write_text(header)
    logger=r'''
#include <stdio.h>
#include "runtime.h"
#include "serial.h"
extern unsigned runtime_serial_wait_result,runtime_receive_display;
static FILE *match_file;
static unsigned match_buffer[64][7],match_count,match_failed;
static void match_flush(void)
{
 unsigned n;
 if(!match_file || match_failed || !match_count)return;
 n=match_count;match_count=0;
 if(fwrite(match_buffer,14,n,match_file)!=n || fflush(match_file))match_failed=1;
}
void match_trace(unsigned kind,unsigned value)
{
 unsigned *record;
 if(match_failed)return;
 if(!match_file){match_file=fopen("MATCH.BIN","wb");if(!match_file){match_failed=1;return;}}
 record=match_buffer[match_count++];record[0]=kind;record[1]=value;
 record[2]=runtime_steps;record[3]=runtime_last_opcode;record[4]=runtime_serial_wait_result;
 record[5]=(unsigned)aspect_serial_ticks();record[6]=runtime_receive_display;
 if(match_count==64 || kind!=1)match_flush();
}
void match_trace_close(unsigned result)
{
 match_trace(3,result);match_flush();if(match_file){fclose(match_file);match_file=0;}
}
'''
    (OUT/'match_trace.c').write_text(logger)
    receive=(ROOT/'src/aspect/receive_runtime.c').read_text()
    marker=' runtime_receive_note_byte(value);'
    assert receive.count(marker)==1
    receive=receive.replace(marker,' if(value!=65535U)match_trace(1,value);\n'+marker)
    (OUT/'receive_runtime.c').write_text('#include "match_trace.c"\n'+receive)
    serial=(ROOT/'src/aspect/serial_runtime.c').read_text()
    marker='unsigned runtime_serial_send(unsigned byte)\n{'
    assert serial.count(marker)==1
    serial=serial.replace(marker,marker+'\n match_trace(2,byte);')
    (OUT/'serial_runtime.c').write_text('#include "match_trace.h"\n'+serial)
    runner=(ROOT/'src/aspect/runner.c').read_text()
    assert runner.count('int main(int argc,char **argv)')==1
    runner=runner.replace('int main(int argc,char **argv)','static int observed_main(int argc,char **argv)')
    (OUT/'runner.c').write_text('#include "match_trace.h"\n'+runner+'\nint main(int argc,char **argv){int result=observed_main(argc,argv);match_trace_close((unsigned)result);return result;}\n')
    builder=ROOT/'standalone/build_aspect_runner.py';source=builder.read_text()
    replacements={"OUT = ROOT / 'build/aspect-runner'":"OUT = TRACE_OUT",
        "if extension else ROOT/'src/aspect/runner.c'":"if extension else TRACE_OUT/'runner.c'",
        "str(ROOT/'src/aspect/serial_runtime.c')":"str(TRACE_OUT/'serial_runtime.c')",
        "str(ROOT/'src/aspect/receive_runtime.c')":"str(TRACE_OUT/'receive_runtime.c')"}
    for old,new in replacements.items():
        assert source.count(old)==1,old
        source=source.replace(old,new)
    scope=dict(__file__=str(builder),__name__='match_trace_build',TRACE_OUT=OUT)
    exec(compile(source,str(builder),'exec'),scope);scope['main']()
    manifest=json.loads((OUT/'manifest.json').read_text())
    for path in (Path(__file__).resolve(),*(OUT/p for p in ('match_trace.h','match_trace.c','runner.c','serial_runtime.c','receive_runtime.c'))):
        manifest['sources'][str(path.relative_to(ROOT))]=sha(path)
    manifest.update(diagnostic_build=True,production_baseline=baseline,
        trace_format='Little endian seven uint16: kind(1=mapped receive,2=send,3=runner return), value, runtime_steps, runtime_last_opcode, WAITFOR result, BIOS tick low, display selector.',
        scope='Diagnostic source observer only; MATCH.BIN records mapped receives after actual policy/render callback, UART send attempts and final runner status. 64 records per receive flush; every send/return flushes. Logging changes timing. Does not accept production BBS compatibility.')
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    assert baseline=={n:sha(ROOT/'build/aspect-runner'/n) for n in baseline}
    print('Diagnostic build only',manifest['binary_sha256'])


if __name__=='__main__':main()
