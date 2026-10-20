#!/usr/bin/env python3
"""Real DOS timeout with an accepted nullmodem socket must return a failure."""
import argparse,asyncio,contextlib,json,re,struct,time
from pathlib import Path
import test_dos
from enigma_notes_dos import sha


async def main(args):
    assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label)
    out=test_dos.ROOT/'build/bbs-lab/results/harness'/args.label
    out.mkdir(parents=True,exist_ok=False)
    # Authored MZ with one infinite jump. It never exits or accesses the UART;
    # DOSBox itself opens the configured nullmodem connection before execution.
    header=struct.pack('<14H',0x5a4d,34,1,0,2,64,64,0,1024,0,0,0,28,0)+bytes(4)
    binary=out/'TERMINAL.EXE';binary.write_bytes(header+b'\xeb\xfe')
    opts=argparse.Namespace(name='harness',label=args.label,binary=binary,port=1,com=2,baud=19200,flow='HARD',
        packet_delay_ms=0,dial_fixture=False,directory_fixture=False,directory_browser=False,entry=3,
        config_fixture=False,keymap_fixture=None,server_log=None,keys='',wait=1,timeout=3)
    start=time.monotonic()
    with (out/'harness.log').open('w') as log,contextlib.redirect_stdout(log):
        code=await asyncio.wait_for(test_dos.run(opts),15)
    elapsed=time.monotonic()-start
    result=json.loads((out/'result.json').read_text());modem=json.loads((out/'modem.json').read_text())
    checks=dict(actual_serial_connection=any(e['kind']=='serial-connected' for e in modem['events']),
        timeout_rejected=code==1 and not result['passed'] and not result['checks']['dos_normal_exit'],
        emulator_terminated_and_cleanup_returned=elapsed<12,
        no_false_BBS_success=not result['checks']['bbs_connected'],authored_input_unchanged=binary.read_bytes()==header+b'\xeb\xfe')
    report=dict(passed=all(checks.values()),checks=checks,seconds=elapsed,
        harness_sha256=sha(Path(test_dos.__file__)),checker_sha256=sha(Path(__file__)),binary_sha256=sha(binary),
        scope='Actual DOSBox-X and nullmodem accepted socket; authored infinite DOS program intentionally times out. Checks bounded harness failure, not product compatibility.')
    (out/'timeout-checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));return 0 if report['passed'] else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--label',required=True)
    raise SystemExit(asyncio.run(main(parser.parse_args())))
