#!/usr/bin/env python3
"""Real parent/child DOS keys must reach the peer before it releases WAITFOR."""
import inspect,json,struct,sys,types
from pathlib import Path
import test_aspect_renderer_dos as renderer
ROOT=renderer.ROOT;OUT=ROOT/'build/aspect-keys-dos'
FULL_WIRE=b'keys\x1b[H\x1b[F\x1b[2~\x1b[3~\x1b[5~\x1b[6~\t\x1b[Z\b\r\x1bOP\x1b[23~\x1b[24;5~done'
FULL_KEYS='k e y s p120 home p120 end p120 ins p120 del p120 pgup p120 pgdown p120 tab p120 s-tab p120 bs p120 enter p120 f1 p120 f11 p120 c-f12 p120 d o n e'
HALF_WIRE=b'\x1b[A\x1b[B\x1b[Akeys\x1b[D\x1b[C\bxdone'
HALF_KEYS='up p120 down p120 up p120 k e y s p120 left p120 right p120 bs p120 x d o n e'
CUSTOM_WIRE=b'keys\0KBDCUSTOMUPCUSTOMTAB\r\ndone'
def definitions():
 cases=[];header=renderer.ESC+b'[2J'+renderer.ESC+b'[HFIRST BYTE SAFE'+renderer.QUERY+renderer.DA+b'LOGIN:'
 for profile in (4,6):
  for kind in ('full','half','custom','halfhome','halfedit','halfcell'):
   half=kind.startswith('half');unsupported=kind=='halfedit'
   source='proc main\nwaitfor "LOGIN:" 5\nset duplex full\ntransmit "KEYREADY"\n'+('set duplex half\n' if half else '')+'waitfor "END" 12\nif waitfor\nset duplex full\ntransmit $D_PWORD\ntransmit "^M"\npause 1\nendif\nendproc\n'
   wire=b'' if unsupported else b'keys\x1b[Hkeydone' if kind=='halfhome' else HALF_WIRE if half else CUSTOM_WIRE if kind=='custom' else FULL_WIRE
   keys='s-tab' if unsupported else 'k e y s p120 home p120 k e y d o n e' if kind=='halfhome' else HALF_KEYS if half else 'k e y s p120 f1 p120 up p120 tab p120 enter p120 d o n e' if kind=='custom' else FULL_KEYS
   screen=[(0,0,'keydoneEND')] if kind=='halfhome' else [(0,0,'FIRST BYTE SAFE')]+([] if unsupported else [(0,21,'keyxdoneEND' if half else 'END')])
   reply=b'[1;11R' if kind=='halfhome' else b'[1;33R' if half else b'[1;25R'
   if kind=='halfcell':
    wire=b'keys\x1b[D\x1b[D\x1b[2~X\x1b[3~\x1b[Cdone'
    keys='k e y s p120 left p120 left p120 ins p120 X p120 del p120 right p120 d o n e'
    screen=[(0,0,'FIRST BYTE SAFE'),(0,21,'keXsdoneEND')]
   cases.append(dict(name='script-keys-%d-%s'%(profile,kind),source=source,banner=header,success=not unsupported,profile=profile,bios_policy='STANDARD' if kind=='halfhome' else 'ENHANCED',custom=kind=='custom',key_wire=wire,keys='p1800 '+keys+' p2500 space p700 r e a d y p700 a-x',post=renderer.QUERY,post_reply=renderer.ESC+reply,screen=screen))
 return cases
def encode(v):
 if isinstance(v,bytes):return dict(hex=v.hex())
 if isinstance(v,dict):return {k:encode(x) for k,x in v.items()}
 if isinstance(v,(tuple,list)):return [encode(x) for x in v]
 return v
def adapter():
 path=ROOT/'standalone/test_connection_dos.py';source=path.read_text()
 old="out=ROOT/'build/connection-dos'/name";assert source.count(old)==1;source=source.replace(old,'out=KEY_OUT/name')
 old="checks['immediate_banner_not_dropped']=len(screen)==4000 and screen[:30:2]==b'FIRST BYTE SAFE'";assert source.count(old)==1;source=source.replace(old,"checks['actual_screen_snapshot']=len(screen)==4000")
 old='if online:\n       line.append(byte)'
 new=old+'''\n       if b'KEYREADY' in line and not checks.get('key_ready_seen'):
        checks['key_ready_seen']=True
       if b'done' in line and not checks.get('key_end_sent'):
        assert checks.get('key_ready_seen')
        conn.sendall(b'END');checks['key_end_sent']=True
       if b'Synth42\\r' in line and not checks.get('renderer_post_sent'):
        assert checks.get('key_end_sent')
        conn.sendall(RENDER_POST);checks['renderer_post_sent']=True'''
 assert source.count(old)==1;source=source.replace(old,new)
 module=types.ModuleType('aspect_key_peer');module.__file__=str(path);module.KEY_OUT=renderer.OUT;module.RENDER_POST=b''
 exec(compile(source,str(path),'exec'),module.__dict__);run=module.run
 def staged(name,*args,**kwargs):
  case=next(c for c in definitions() if c['name']==name)
  if case['custom']:
   data=bytearray(7*948)
   for profile in (4,6):
    for slot,value in {16:b'\xffKBD',50:b'CUSTOMUP',72:b'CUSTOMUP',6:b'CUSTOMTAB',78:b'\r\n'}.items():
     at=profile*948+slot*12;data[at:at+len(value)]=value
   kwargs['files']['TEST.KBD']=bytes(data);kwargs['arguments']+=' /K:D:\\TEST.KBD'
  return run(name,*args,**kwargs)
 module.run=staged;return module
def main():
 source=inspect.getsource(renderer.main)
 pairs={
  "expectations=[{k:(v.hex() if isinstance(v,bytes) else v) for k,v in c.items()} for c in cases]":"expectations=encode(cases)",
  'payload=bytearray(directory());':"payload=bytearray(directory(profile=case['profile']));",
  "settings=bytearray(prm());extra=' /A:NETWORK'":"settings=bytearray(prm());struct.pack_into('<H',settings,0x1d18-0x1b84,case['profile']);extra=' /A:NETWORK /B:'+case['bios_policy']",
  "files=files,banner=case['banner'],working_drive='d',observer='RENDER')":"files=files,banner=case['banner'],working_drive='d',observer='RENDER',profile=case['profile'])"}
 for old,new in pairs.items():assert source.count(old)==1,old;source=source.replace(old,new)
 start=source.index('  keys=(');end=source.index('\n  result=harness.run',start)
 source=source[:start]+"  keys=case['keys']"+source[end:]
 scope=dict(renderer.__dict__);scope.update(__file__=__file__,OUT=OUT,definitions=definitions,encode=encode)
 def labelled_adapter():
  previous=renderer.OUT;renderer.OUT=scope['OUT']
  try:return adapter()
  finally:renderer.OUT=previous
 def labelled_observer(offsets):
  previous=renderer.OUT;renderer.OUT=scope['OUT']
  try:return renderer.observer(offsets)
  finally:renderer.OUT=previous
 scope.update(adapter=labelled_adapter,observer=labelled_observer)
 exec(compile(source,__file__,'exec'),scope);scope['main']()
 folder=scope['OUT'];report=json.loads((folder/'checks.json').read_text())
 for case in report['cases']:
  spec=next(c for c in definitions() if c['name']==case['case']);wire=(folder/case['case']/'serial.bin').read_bytes()
  at=wire.find(b'KEYREADY');end=wire.find(b'Synth42\r')
  if spec['success']:
   case['checks'].update(keys_during_script_before_continuation=at>=0 and end>at and wire[at+8:end]==spec['key_wire'],peer_released_only_after_keys=case['checks'].get('key_end_sent',False))
  else:
   case['checks'].update(unsupported_before_wire=at>=0 and end<0 and wire[at+8:].split(b'ready')[0].strip(b' ')==b'',typed_key_error=case['passive_observer_header'][6]==3,peer_not_released=not case['checks'].get('key_end_sent',False))
  case['passed']=all(case['checks'].values());(folder/case['case']/'result.json').write_text(json.dumps(case,indent=2)+'\n')
 report.update(passed=all(c['passed'] for c in report['cases']),checker_sha256=renderer.sha(Path(__file__)),reused_renderer_checker_sha256=renderer.sha(Path(renderer.__file__)),scope='Actual DOS BIOS keys during ASPECT WAITFOR, shared selected parent profile bindings, child-owned UART and real renderer echo. Owned peer withholds END until typed done, then script sends its password marker and continues; later parent keys still work. ANSI/VT220 full/half and binary custom KBD. No physical modem or full local-key/UI/macro claim.')
 (folder/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
 print('ASPECT product keys',len(report['cases']),'cases',report['passed'])
 return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
