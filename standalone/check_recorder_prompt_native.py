#!/usr/bin/env python3
"""Execute generated prompts in native WAITFOR, including a real BBS stream."""
import argparse,ctypes as C,hashlib,json,re,subprocess
from pathlib import Path
from check_aspect_recorder import Session,Ops,WRITE,CLOSE,U,P
from check_aspect_serial_commands import Machine,DATA,RESULT,timeout,decode
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--trace',type=Path,help='Optional owned diagnostic BBS stage with MATCH.BIN and PCPLUS.ASP')
    args=p.parse_args();out=args.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists();out.mkdir(parents=True)
    subprocess.run(['gcc','-std=c89','-Wall','-Wextra','-Werror','-shared','-fPIC',
        str(ROOT/'src/aspect/recorder.c'),'-o',str(out/'recorder.so')],check=True)
    lib=C.CDLL(str(out/'recorder.so'));lib.aspect_recorder_start.argtypes=[P,P,P,U]
    for name in ('receive','transmit'):getattr(lib,'aspect_recorder_'+name).argtypes=[P,P,U]
    lib.aspect_recorder_stop.argtypes=[P]
    base=ROOT/'build/aspect-serial-commands';manifest=json.loads((base/'manifest.json').read_text())
    images=[]
    for u in manifest['units']:
        assert sha(base/u['name'])==u['sha256']
        images.append((u['start'],u['end_exclusive'],(base/u['name']).read_bytes()))
    def source(prompt,send=True):
        data=bytearray();s=Session()
        def write(ctx,ptr,count,result):
            data.extend(C.string_at(ptr,count));C.cast(result,C.POINTER(U))[0]=count;return 0
        writer=WRITE(write);closer=CLOSE(lambda ctx:0);ops=Ops(writer,closer)
        assert lib.aspect_recorder_start(C.byref(s),C.byref(ops),None,30)==0
        assert lib.aspect_recorder_receive(C.byref(s),C.create_string_buffer(prompt),len(prompt))==0
        if send:assert lib.aspect_recorder_transmit(C.byref(s),C.create_string_buffer(b'X'),1)==0
        assert lib.aspect_recorder_stop(C.byref(s))==0
        return bytes(data)
    def encoded(script):
        pattern=bytearray(re.findall(rb'^strcpy loc_prompt "(.*)"\r?$',script,re.M)[0])
        for at,value in re.findall(rb'^strpoke loc_prompt (\d+) (\d+)\r?$',script,re.M):pattern[int(at)]=int(value)
        return bytes(pattern)
    def native(pattern,stream):
        m=Machine(images,b'\x64\0'+timeout(0));m.cancel_after=1000
        m.write(DATA['bank'],pattern+b'\0');m.queued(stream);m.invoke('wait_for')
        return m.word(RESULT),m.rx_head
    cases=[]
    patterns=[b'AAB',b'ABABAC',b'A'*16,b'aAaB',b' '*13+b'\x1b'*3,
        b'ABABA',b'AAAABAAAAC',b'"^> \xff',b'Login: ',b'No carrier',bytes(range(1,17))]
    for i,prompt in enumerate(patterns):
        script=source(prompt);pattern=encoded(script);(out/('P%02d.ASP'%i)).write_bytes(script)
        for prefix in (b'',b' '*32,b'A'*32,b'AB'*20,b'ABA'*12,b'a'*30):
            # Include original observed prompt; the native routine must find
            # the generated suffix regardless of the preceding overlap.
            stream=prefix+prompt;matched,consumed=native(pattern,stream)
            assert matched and decode(pattern).upper() in stream.upper(),(prompt,prefix,pattern)
            cases.append(dict(prompt_hex=prompt.hex(),pattern_hex=pattern.hex(),prefix_hex=prefix.hex(),passed=True,consumed=consumed))
        if prompt==b'A'*16:assert decode(pattern)==prompt
        assert b'waitfor' not in source(prompt,False),'No action depends on the stop-only RX tail'
    # Captured actual translated input, not reconstructed from ANSI wire text.
    real=None;trace_inputs=[]
    if args.trace:
        import struct
        trace=args.trace.resolve();assert trace.is_relative_to(ROOT/'build')
        rows=list(struct.iter_unpack('<7H',(trace/'MATCH.BIN').read_bytes()))
        stream=bytes(r[1] for r in rows if r[0]==1 and r[2]==9)
        old=re.findall(rb'^strcpy loc_prompt "(.*)"\r?$',(trace/'PCPLUS.ASP').read_bytes(),re.M)[1]
        assert decode(old) in stream and native(old,stream)[0]==0
        pattern=encoded(source(b' '*13+b'\x1b'*3));matched,consumed=native(pattern,stream)
        assert matched and decode(pattern)==b' \x1b\x1b\x1b'
        real=dict(stream_bytes=len(stream),old_occurrence_present=True,old_native_match=False,
            generated_pattern_hex=pattern.hex(),new_native_match=True,consumed=consumed)
        trace_inputs=[trace/'MATCH.BIN',trace/'PCPLUS.ASP']
    inputs={str(q.relative_to(ROOT)):sha(q) for q in (Path(__file__).resolve(),ROOT/'src/aspect/recorder.c',
        ROOT/'src/aspect/recorder.h',ROOT/'standalone/check_aspect_recorder.py',ROOT/'standalone/check_aspect_serial_commands.py',
        ROOT/'standalone/check_aspect_console.py',ROOT/'standalone/check_aspect_strings.py',base/'manifest.json',*trace_inputs)}
    result=dict(passed=True,cases=cases,native_cases=len(cases)+(2 if real else 0),
        real_ENiGMA=real,inputs=inputs,
        scope='Host C recorder output executed in unchanged native WAITFOR/decoder CPU instructions. Device, clock and cancellation callbacks modeled. Optional separately identified diagnostic DOS mapped-lead capture. No current production BBS/audio or full application acceptance.')
    for path,digest in inputs.items():
        target=out/'frozen-source'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/path).read_bytes());assert sha(target)==digest
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,native_cases=result['native_cases'],real_ENiGMA=result['real_ENiGMA'])))


if __name__=='__main__':main()
