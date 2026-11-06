#!/usr/bin/env python3
"""Normal DOS8086 native-echo wait with real BIOS typeahead/cancellation keys."""
import argparse,json,re,shutil,struct,subprocess
from pathlib import Path
import test_connection_dos as harness
from directory_fixtures import prm
from build_path_session import ROOT,sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('terminal','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--queued',action='store_true',help='Put ordinary X ahead of cancellation in the real BIOS queue')
    p.add_argument('--pressure',type=int,choices=[0,32,40],default=0,help='Burst ordinary BIOS keys before Escape; require the32-key FIFO limit to be observed')
    a=p.parse_args();binary=a.terminal.resolve();out=a.output.resolve()
    assert out.is_relative_to(ROOT/'build') and not out.exists()
    m=json.loads(binary.with_name('manifest.json').read_text())
    assert m['experimental_chat_foreground_text'] and sha(binary)==m['binary_sha256']
    names=('standalone/test_chat_busy_keys_dos.py','standalone/chat_busy_watch.asm',
           'standalone/test_connection_dos.py','standalone/directory_fixtures.py',
           'standalone/modem_fixtures.py','standalone/terminal_config_fixtures.py',
           'standalone/test_terminal.py','standalone/directory_test_support.py','standalone/build_path_session.py')
    sources={**m['sources'],**{n:sha(ROOT/n) for n in names}}
    for n,h in sources.items():assert sha(ROOT/n)==h,n
    listing=binary.with_name('terminal.map').read_text()
    symbols={n:(int(seg,16),int(off,16)) for seg,off,n in re.findall(
        r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing,re.M|re.I)}
    ds=int(re.search(r'^DGROUP\s+([0-9a-f]+):0000',listing,re.M|re.I)[1],16)
    constants={'FROZEN_DELTA':symbols['redisplay_snapshot'][0]-ds}
    assert symbols['redisplay_snapshot'][1]==0
    for label,name in [('OWNER_OFF','_redisplay_active'),('PARSER_OFF','terminal_parser_active'),('WAIT_OFF','terminal_ansi_wait_active'),('DEFERRED_OFF','terminal_deferred_count'),('STATUS_OFF','terminal_macro_status')]:
        seg,off=symbols[name];assert seg==ds;constants[label]=off
    out.mkdir();stage=out/'program';stage.mkdir()
    shutil.copyfile(binary,stage/'TERMINAL.EXE');shutil.copyfile(binary.parent/'PCCHAT.OVL',stage/'PCCHAT.OVL')
    observer=out/'BUSYW.COM'
    subprocess.run(['nasm','-fbin',*['-D'+k+'='+str(v) for k,v in constants.items()],str(ROOT/'standalone/chat_busy_watch.asm'),'-o',str(observer)],check=True)
    settings=bytearray(prm(port=3,baud=5))
    for off,value in [(0x188,5),(0x4e4,8),(0x4e6,4),(0x1c2,0),(0x1c8,2),
                      (0x1ca,25),(0x4ec,0),(0x1bc,0),(0x1be,0),(0x1e6,0),(0x1e4,0)]:
        struct.pack_into('<H',settings,off,value)
    settings[0x1e2]=ord('~')
    records=struct.pack('<H',3)+b'GO^[TAIL^M'.ljust(52,b'\0')+bytes(54*9)
    prefix='p900 enter p5000 a-e p500 a-o p1800 a-1 '
    recipes={
        'complete':prefix+'p200 X enter p1900 escape p800 N O R M A L p1000 a-x',
        'escape':prefix+'p400 escape p1000 N O R M A L p1000 a-x',
        'hangup':prefix+'p400 a-h p2200 a-x',
        'quit':prefix+'p400 a-x'}
    if a.queued:
        for case in ('escape','hangup','quit'):
            recipes[case]=recipes[case].replace('p400 ','p200 X p200 ',1)
    if a.pressure:
        a.queued=True
        burst='p100 '+'X '*a.pressure
        # Complete two sessions in one process: the overflow bell latch must
        # reset on the second successful claim, with the same retained prefix.
        completion=burst+'p1000 enter p1000 escape '
        recipes={
            'complete':prefix+completion+'p500 a-o p1800 a-1 '+completion+'p800 N O R M A L p1000 a-x',
            'escape':prefix+burst+'p100 escape p1500 N O R M A L p1000 a-x',
            'hangup':prefix+burst+'p100 a-h p2200 a-x',
            'quit':prefix+burst+'p100 a-x'}
    results=[]
    for case,keys in recipes.items():
        harness.BINARY=stage/'TERMINAL.EXE';name=out.name+'-'+case;capture=ROOT/'build/connection-dos'/name
        assert not capture.exists()
        triggers=[]
        if case=='complete':
            triggers.extend([(b'GO',[(.6,b'[31m')])])
            if a.pressure:triggers.append((b'GO',[(.6,b'[31m')]))
        if case in ('complete','escape'):triggers.append((b'NORMAL',[(0,b'BACK\x1b[6n')]))
        r=harness.run(name,'hangup' if case=='hangup' else 'success',keys,
            prm=bytes(settings),com=3,irq=5,cpu='8086',working_drive='d',timeout=40,
            arguments='@TEST.PRM /D:CaseTest:23 /T:D:\\ACTIONS.KEY',
            files={'ACTIONS.KEY':records,'BUSYW.COM':observer.read_bytes()},observer='BUSYW',online_triggers=triggers)
        wire=(capture/'serial.bin').read_bytes();screen=(capture/'SCREEN.BIN').read_bytes()[::2]
        view=(capture/'BUSYVIEW.BIN').read_bytes();words=struct.unpack('<14H',view);flags=words[1]
        checks=dict(harness=r['passed'],observer_identity=words[0]==0x4257,
                    native_wait_observed=bool(flags&1) and words[2]>0,
                    initial_text_prefix=b'GO' in wire)
        if case=='complete':
            checks.update(BIOS_X_observed_before_dequeue=bool(flags&2) and words[3]>0 and words[5]!=words[6],
                          TEXT_then_queued_input=(b'GO\x1bTAIL\r'+b'X'*(32 if a.pressure else 1)+b'\r') in wire)
            if a.pressure:
                checks['both_retained_prefixes_exact']=wire.count(b'GO\x1bTAIL\r'+b'X'*32+b'\r')==2 and wire.count(b'X')==64
        else:checks['cancelled_before_ESC_TX']=b'TAIL' not in wire and b'GO\x1b' not in wire
        if case!='quit' or a.queued:checks['owner_and_wait_unwound']=bool(flags&4) and words[4]>0
        if case in ('escape','hangup') or (case=='quit' and a.queued):
            checks['prompt_cancel_before_deadline']=((words[9]-words[7])&65535)<18
        if a.queued and case!='complete':
            checks['X_was_queued_during_wait']=bool(flags&2) and words[3]>0
            checks['cancelled_typeahead_does_not_leak']=b'GOX' not in wire
        if a.queued or case=='complete':
            checks['owned_FIFO_retains_typeahead']=bool(flags&8) and (2 if case=='complete' else 1)<=words[11]<=32
        if a.pressure:checks['FIFO_capacity_observed']=words[11]==32
        checks['overflow_bell_request_and_status']=(words[12]==(2 if case=='complete' else 1) and words[13]==7) if a.pressure>32 else words[12]==0
        if flags&4:checks['retired_FIFO_empty']=words[10]==0
        if case in ('complete','escape'):
            checks.update(normal_input_resumes=b'NORMAL' in wire and b'BACK' in screen,
                          ordinary_CPR_after_return=len(re.findall(rb'\x1b\[\d+;\d+R',wire))==2)
        results.append(dict(case=case,passed=all(checks.values()),checks=checks,
                            observer_words=words,capture=str(capture.relative_to(ROOT))))
    checks=dict(cases=all(r['passed'] for r in results),sources_unchanged=all(sha(ROOT/n)==h for n,h in sources.items()),
                module_unchanged=sha(stage/'PCCHAT.OVL')==m['chat_loader']['module']['binary_sha256'])
    report=dict(passed=all(checks.values()),checks=checks,cases=results,binary_sha256=sha(binary),
                module_sha256=sha(stage/'PCCHAT.OVL'),sources=sources,observer_constants=constants,observer_sha256=sha(observer),
                queued_cancellation=a.queued,
                pressure_keys=a.pressure,
                scope=__doc__+' Actual main and loaded module/native parser, real BIOS keys and synthetic physical UART. Passive INT16 observer validates DS=SS, exact module header/API, STEP/TEXT/owner/parser/wait state, queued X before BIOS dequeue and later owner/parser/wait retirement. Observer only reads product/BIOS memory and chains original BIOS provider. Delayed CSI completes one wait; Escape/AltH/AltX cancel others without later TEXT emission. Optional queued case places X before each cancellation and checks prompt return without transmitting abandoned typeahead. No injected product state, substituted native routines, physical modem/SIP/audio, broad geometry/failure or full original controller acceptance.')
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    assert report['passed'],results
    print('PASS DOS native-parser wait: BIOS X retained, real continuation and Escape/AltH/AltX unwind')


if __name__=='__main__':main()
