#!/usr/bin/env python3
"""Real selected SEXYZ receiver: absent versus explicit unknown ZFILE time.

Host callbacks use generated files; this does not establish DOS/UART behavior.
Only the offer's metadata is replaced, with a freshly calculated wire CRC.
The same engine, receiver and file bytes are used for both variants.
"""
import argparse,ctypes as C,hashlib,json,subprocess,time
from pathlib import Path
from check_zmodem import Fixture,ROOT,packet


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sexyz',type=Path,required=True)
    p.add_argument('--label',required=True)
    p.add_argument('--engine',action='store_true',help='Also require unchanged engine output to carry explicit unknown time')
    args=p.parse_args();assert args.label.replace('-','').replace('_','').isalnum()
    peer_path=args.sexyz.resolve();assert peer_path.is_relative_to(ROOT/'build') and peer_path.is_file()
    out=ROOT/'build/zmodem-timestamp'/args.label;out.mkdir(parents=True,exist_ok=False)
    sources=[ROOT/'src/transfer'/n for n in ('zmodem.c','zmodem.h','zmodem_wire.c','zmodem_wire.h','zmodem_name.c','zmodem_name.h','batch_header.c','batch_header.h')]
    inputs={str(f.relative_to(ROOT)):sha(f) for f in sources+[Path(__file__),ROOT/'standalone/check_zmodem.py',ROOT/'standalone/check_zmodem_wire.py']}
    peer_hash=sha(peer_path)
    subprocess.run(['gcc','-std=c89','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-shared','-fPIC',*[str(f) for f in sources if f.suffix=='.c'],'-o',str(out/'session.so')],check=True)
    lib=C.CDLL(str(out/'session.so'));lib.zm_run.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint]
    cases=[]
    for variant in (('absent','unknown','engine') if args.engine else ('absent','unknown')):
      unknown=variant!='absent'
      for empty_first in (False,True):
        label=variant+('-empty-first' if empty_first else '-empty-last')
        folder=out/label;folder.mkdir();offers=[]
        files=[('PCUP01.BIN',bytes((i*73+(i>>8)*19)&255 for i in range(1501))),('EMPTY.BIN',b'')]
        if empty_first:files.reverse()
        class MetadataFixture(Fixture):
            def write(self,ctx,data,n):
                value=C.string_at(data,n)
                if self.session.phase==0:
                    raw=bytes(self.session.data[:128])
                    if value==packet(raw,self.session.format,107,self.session.control):
                        name=raw.split(b'\0',1)[0];size=str(len(dict(files)[name.decode()])).encode()
                        payload=(name+b'\0'+size+(b' 0' if unknown else b'')+b'\0').ljust(128,b'\0')
                        offers.append(payload.hex())
                        if variant=='engine':assert raw==payload,'Unmodified sender omitted explicit unknown time'
                        else:value=packet(payload,self.session.format,107,self.session.control)
                buf=C.create_string_buffer(value)
                return super().write(ctx,buf,len(value))
        started=time.time_ns()
        with (folder/'stderr.log').open('wb') as log:
            peer=subprocess.Popen([str(peer_path),'-raw','rz'],cwd=folder,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,bufsize=0)
            try:
                f=MetadataFixture(lib,sources=files,peer=peer);status=f.run(True)
                peer.wait(timeout=10);ended=time.time_ns()
                actual={name:(folder/name).read_bytes() for name,_ in files}
                dates={name:(folder/name).stat().st_mtime_ns for name,_ in files}
                sane={name:started-2_000_000_000<=value<=ended+2_000_000_000 for name,value in dates.items()}
                assert status==0 and peer.returncode==0 and actual==dict(files) and len(offers)==2
                if unknown:assert all(sane.values()),(label,dates,started,ended)
                (folder/'engine-output.bin').write_bytes(f.tx)
                (folder/'peer-output.bin').write_bytes(f.peer_wire)
                cases.append(dict(case=label,explicit_unknown_time=unknown,bytes_exact=True,receiver_exit=peer.returncode,
                    current_creation_dates=sane,mtime_ns={name:str(value) for name,value in dates.items()},
                    offers=offers,wire_sha256=sha(folder/'engine-output.bin')))
            finally:
                if peer.poll() is None:peer.kill();peer.wait()
                peer.stdin.close();peer.stdout.close()
    reproduced=any(not all(c['current_creation_dates'].values()) for c in cases if not c['explicit_unknown_time'])
    assert peer_hash==sha(peer_path) and inputs=={name:sha(ROOT/name) for name in inputs}
    result=dict(passed=all(all(c['current_creation_dates'].values()) for c in cases if c['explicit_unknown_time']),
        absent_time_bad_date_reproduced=reproduced,cases=cases,sources=inputs,peer_sha256=peer_hash,
        scope='Actual isolated SEXYZ stdio receiver, generated binary+empty batch in both orders. Unknown time means receiver creation date; source-date preservation is not implemented. No DOS/UART/live-board claim.')
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=result['passed'],absent_time_bad_date_reproduced=reproduced,cases=[dict(case=c['case'],dates_sane=c['current_creation_dates']) for c in cases]),indent=2))


if __name__=='__main__':main()
