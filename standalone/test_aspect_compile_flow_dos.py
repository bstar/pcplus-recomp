#!/usr/bin/env python3
"""Compiler flow bracket over real preloaded DOS UART/IRQ fixtures."""
import json
from pathlib import Path
import test_aspect_serial_preload_dos as fixture
def main():
 fixture.OUT=fixture.ROOT/'build/aspect-compile-flow-dos'
 fixture.PROBE=fixture.PROBE.replace('#include <stdlib.h>','#include <stdlib.h>\n#include <conio.h>\n#include <dos.h>\nstatic unsigned cpu_flags(void);\n#pragma aux cpu_flags = "pushf" "pop ax" value [ax] modify exact [ax];')
 old='for(i=0;i<count;++i){c=(i*37+128)&255;'
 new=('_disable();status=aspect_serial_compile_pause();'
      'if(status!=ASPECT_SERIAL_STATE){_enable();return 104;}'
      'if(cpu_flags()&512){_enable();return 105;}_enable();'
      'if(aspect_serial_compile_pause()!=0)return 96;'
      'if(aspect_serial_available()!=count)return 97;'
      'if(aspect_serial_compile_pause()!=ASPECT_SERIAL_BUSY)return 98;'
      'if(aspect_serial_available()!=count)return 99;'
      'if(aspect_serial_compile_resume()!=0)return 100;'
      '{unsigned lcr=argv[1][2]==\'1\'?0x3fb:0x2fb,old=inp(lcr);outp(lcr,old|0x40);'
      'if(aspect_serial_compile_pause()!=ASPECT_SERIAL_LINE)return 102;'
      'if(inp(lcr)!=(old|0x40))return 103;outp(lcr,old);}'
      'for(i=0;i<count;++i){c=(i*37+128)&255;')
 assert fixture.PROBE.count(old)==1;fixture.PROBE=fixture.PROBE.replace(old,new)
 old='if(aspect_serial_read()!=c)return 89;'
 new=old+'if(count-i-1==128 && argv[1][12]==\'B\' && !(inp(0x2fc)&2))return 101;'
 assert fixture.PROBE.count(old)==1;fixture.PROBE=fixture.PROBE.replace(old,new)
 fixture.main(expected_wire={'N':b'D','H':b'D','S':b'\x13\x11D\x13','B':b'\x13\x11D\x13'});path=fixture.OUT/'checks.json';r=json.loads(path.read_text())
 r.update(checker_sha256=fixture.sha(Path(__file__)),fixture_checker_sha256=fixture.sha(Path(fixture.__file__)),generated_probe_sha256=fixture.sha(fixture.OUT/'probe.c'),scope='Actual DOS COM1/COM2 compiler pause/resume with IRQ and wrapped/preloaded queues. Rejected nested pause preserves count/ownership; full combined-flow preload releases RTS at low water, then receives new live IRQ bytes and returns exact raw suffix. N/S/H/B across four established fixtures; physical flow timing remains unproved.')
 path.write_text(json.dumps(r,indent=2)+'\n')
if __name__=='__main__':main()
