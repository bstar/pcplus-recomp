#!/usr/bin/env python3
"""Resolve the existing stock ENiGMA ZedZap helper in the owned loopback lab.
Preserve inherited -8 sz/rz arguments, menus and source code.
An explicit optional selector-first fixture bypasses the known arrow-input issue.
"""
import argparse,hashlib,json,subprocess
from pathlib import Path
import enigma
from enigma_transfer import HELPER,SHA
def main():
 p=argparse.ArgumentParser();p.add_argument('--select-first',action='store_true',help='Explicit fixture to avoid the separately observed fragmented-arrow selector issue.');a=p.parse_args()
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=enigma.SOURCE,text=True).strip()==enigma.COMMIT
 original=enigma.SOURCE/'docker/bin/sexyz-amd64';assert hashlib.sha256(original.read_bytes()).hexdigest()==SHA
 assert HELPER.is_file() and not subprocess.check_output(['ss','-Htn','state','established','sport','=',':23233'],text=True).strip()
 config=enigma.SOURCE/'config/config.hjson';before=config.read_bytes();settings=json.loads(before)
 out=enigma.LAB/('zmodem-selected' if a.select_first else 'zmodem');out.mkdir(exist_ok=True);backup=out/('config-before-'+hashlib.sha256(before).hexdigest()+'.json');assert not backup.exists();backup.write_bytes(before)
 protocol=settings.setdefault('fileTransferProtocols',{}).setdefault('zmodem8kSexyz',{})
 external=protocol.setdefault('external',{});external.update(sendCmd=str(HELPER),recvCmd=str(HELPER))
 if a.select_first:protocol['sort']=-2
 enigma.stop()
 try:
  config.write_text(json.dumps(settings,indent=2)+'\n');enigma.start()
 except BaseException:
  config.write_bytes(before);enigma.start();raise
 result=dict(passed=True,server_commit=enigma.COMMIT,before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(config.read_bytes()).hexdigest(),
  stock_helper_sha256=SHA,adapted_helper_sha256=hashlib.sha256(HELPER.read_bytes()).hexdigest(),override=protocol,backup=str(backup.relative_to(enigma.ROOT)),
  selector_fixture=a.select_first,
  scope='Owned ENiGMA zmodem8kSexyz executable paths; optional explicitly recorded selector-first fixture. Inherited -telnet -8 sz/rz, server/protocol implementation and menu code unchanged. No arrow-navigation compatibility claim.')
 (out/'setup.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
