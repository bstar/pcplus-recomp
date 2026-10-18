#!/usr/bin/env python3
"""Actual DOS directory browser, strict file IO and selected-entry connection."""
import hashlib,json,struct
from pathlib import Path
from directory_fixtures import directory,prm
from test_connection_dos import run,ROOT,BINARY
def main():
 cases=[]
 def check(name,mode,*,payload=None,settings=None,args=None,keys='p4500 a-x',**kwargs):
  cases.append(run('directory-'+name,mode,keys,directory=directory() if payload is None else payload,prm=prm() if settings is None else settings,arguments=args or '@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1',**kwargs))
 check('literal','success')
 check('entry200-serial-profile','success',payload=directory(entry=200,port=2,baud=5,profile=4),args='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:200',com=2,profile=4)
 check('CLI-port-override','success',payload=directory(port=2,baud=5),args='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 COM3 38400 NONE',com=3)
 check('legacy-codes','success',payload=directory(target=b'a555'),args='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /C:LEGACY',target=b'9,555')
 direct=bytearray(prm());struct.pack_into('<H',direct,10,0)
 check('direct-no-modem','direct',payload=directory(direct=1,target=b''),settings=bytes(direct))
 check('browser-selection','success',payload=directory(entry=3),args='@D:\\TEST.PRM /E:D:\\TEST.DIR',keys='p500 down p100 down p100 enter p4500 a-x')
 check('browser-cancel','cancel',args='@D:\\TEST.PRM /E:D:\\TEST.DIR',keys='p500 escape')
 check('short-file','reject',payload=directory()[:-1],expected=7)
 check('suffix-file','reject',payload=directory()+b'X',expected=7)
 for name,offset,value in [('profile',73,7),('port',104,5),('HALF',51,1),('script',52,ord('X')),('password',75,ord('X')),('keyboard',86,ord('X')),('META',95,ord('X'))]:
  data=bytearray(directory());data[250+offset]=value
  check('unsupported-'+name,'reject',payload=bytes(data),expected=7)
 check('conflicting-targets','reject',args='@D:\\TEST.PRM /E:D:\\TEST.DIR /N:1 /D:Other:23',expected=7)
 out=ROOT/'build/directory-terminal';out.mkdir(parents=True,exist_ok=True)
 result={'passed':all(c['passed'] for c in cases),'binary_sha256':hashlib.sha256(BINARY.read_bytes()).hexdigest(),'cases':cases,'scope':'Actual DOS strict directory/PRM file IO, browser keys, entry settings and modem/direct controller through real emulated UART; synthetic files unchanged, independent IRQ/UART/PIC sampler.'}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
