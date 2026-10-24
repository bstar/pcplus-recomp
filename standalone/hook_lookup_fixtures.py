"""Owned DOS helper locations and wrong-target controls for filename lookup."""
CASES=('exact-before-pcplus','pcplus-file','pcplus-stem','path-file','path-stem','com-priority','batch-collision','long-pcplus')
def fixture(case,helper):
 assert case in CASES
 bad=bytes.fromhex('b8634ccd21') # Wrong target exits99 without any witness.
 env={};name=b'APPLYCH.EXE';files={}
 if case=='exact-before-pcplus':
  files={'APPLYCH.EXE':helper,'BIN/APPLYCH.EXE':bad};env={'PCPLUS':'D:\\BIN'}
 elif case in('pcplus-file','pcplus-stem'):
  name=b'APPLYCH'if case.endswith('stem')else b'APPLYCH.EXE'
  files={'BIN/APPLYCH.com'if case.endswith('stem')else'BIN/APPLYCH.EXE':helper};env={'PCPLUS':'D:\\BIN'}
  if case.endswith('stem'):files['APPLYCH.exe']=bad
 elif case in('path-file','path-stem'):
  name=b'APPLYCH'if case.endswith('stem')else b'APPLYCH.EXE'
  files={'BIN/APPLYCH.exe'if case.endswith('stem')else'BIN/APPLYCH.EXE':helper};env={'PATH':'D:\\BIN;Z:\\;Z:\\SYSTEM;Z:\\BIN'}
 elif case=='com-priority':name=b'APPLYCH';files={'APPLYCH.com':helper,'APPLYCH.exe':bad}
 elif case=='batch-collision':
  name=b'CALL.BAT';files={'CALL.BAT':b'@echo off\r\necho START>D:\\BATSEEN.TXT\r\necho [%0] [%1] [%2] [%3] [%4] [%5]>D:\\BATARGS.TXT\r\nD:\r\ncd \\\r\nD:\\BIN\\APPLYCH.EXE %1 %2 %3 %4 %5\r\n','CALL.COM':bad,'BIN/APPLYCH.EXE':helper}
  env={'COMSPEC':'Z:\\COMMAND.COM'}
 else:
  relative='/'.join(['ABCDEFGH']*14);files={relative+'/APPLYCH.EXE':helper};env={'PCPLUS':'D:\\'+relative.replace('/','\\')}
 return name,files,env
