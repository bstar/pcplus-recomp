#!/usr/bin/env python3
"""Enable the stock ENiGMA YMODEM helper in the owned loopback lab only.

Run with no active lab sessions. Stops/restarts only the PID validated by
enigma.py. Changes helper paths and selector order; retains upstream sY/ry
arguments, protocol implementation, menus and terminal decoder.
"""
import hashlib,json,subprocess
from pathlib import Path
import enigma
from enigma_transfer import HELPER,SHA

def main():
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=enigma.SOURCE,text=True).strip()==enigma.COMMIT
 assert HELPER.is_file()
 original=enigma.SOURCE/'docker/bin/sexyz-amd64'
 assert hashlib.sha256(original.read_bytes()).hexdigest()==SHA
 connections=subprocess.check_output(['ss','-Htn','state','established','sport','=',':23233'],text=True)
 assert not connections.strip(),'Active owned lab session; finish before configuring'
 config=enigma.SOURCE/'config/config.hjson';before=config.read_bytes();settings=json.loads(before)
 output=enigma.LAB/'ymodem';output.mkdir(exist_ok=True)
 backup=output/('config-before-'+hashlib.sha256(before).hexdigest()+'.json')
 if not backup.exists():backup.write_bytes(before)
 protocol=settings.setdefault('fileTransferProtocols',{}).setdefault('ymodemSexyz',{})
 protocol['sort']=-1
 external=protocol.setdefault('external',{})
 external.update(sendCmd=str(HELPER),recvCmd=str(HELPER))
 enigma.stop()
 config.write_text(json.dumps(settings,indent=2)+'\n')
 enigma.start()
 result=dict(passed=True,server_commit=enigma.COMMIT,
  before_sha256=hashlib.sha256(before).hexdigest(),
  after_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),
  stock_helper_sha256=SHA,adapted_helper_sha256=hashlib.sha256(HELPER.read_bytes()).hexdigest(),
  override=protocol,scope='Owned loopback ENiGMA helper executable paths and YMODEM selector ordering only; stock inherited sY/ry arguments and protocol code.')
 (output/'setup.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
