#!/usr/bin/env python3
"""Compose the pinned Node candidate and Nix-built i386 helper in an isolated VM."""
import argparse,gzip,json,struct,subprocess,time
from pathlib import Path
from synthmodem_vm_control import ROOT,REV,MEDIA,INIT,sha,records,archive

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();candidate=a.candidate.resolve();out=a.output.resolve()
 assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 ledger=ROOT/'docs/validation/synthmodem-pressure.json'
 pins=json.loads(ledger.read_text())['candidate_sha256']
 assert all(sha(candidate/n)==h for n,h in pins.items()),'Candidate differs from pressure receipt'
 names=['lab/bbs/synthmodem_vm_composed.py','lab/bbs/synthmodem_vm_composed.js',
  'lab/bbs/synthmodem_vm_control.py','nix/flake.nix','nix/flake.lock','tools/modem-dev',
  'lab/bbs/patches/synthmodem-control/control.patch',str(ledger.relative_to(ROOT))]
 frozen={n:sha(ROOT/n) for n in names}
 built=json.loads(subprocess.check_output(['nix','--extra-experimental-features','nix-command flakes',
  'build',str(ROOT/'nix')+'#synthmodem-control-i386','--no-link','--json'],text=True))
 helper=Path(built[0]['outputs']['out'])/'bin/modemd-ctrl';elf=helper.read_bytes()
 assert elf[:5]==b'\x7fELF\x01' and struct.unpack_from('<H',elf,18)[0]==3
 assert 'INTERP' not in subprocess.check_output(['readelf','-l',str(helper)],text=True)
 media={n:ROOT/'build/bbs-lab/synthmodem-vm-cache/vm/images'/n for n in MEDIA}
 assert all(sha(media[n])==h for n,h in MEDIA.items()),'Pinned media missing or changed'
 original=records(gzip.decompress(media['rootfs-slmodemd-pjsip.cpio.gz'].read_bytes()))
 assert sum(n=='usr/local/bin/modemd-ctrl' for n,_,_ in original)==1
 assert 'lab-init' not in {n for n,_,_ in original}
 entries=[(n,f,elf if n=='usr/local/bin/modemd-ctrl' else d) for n,f,d in original]
 entries.append(('lab-init',[max(f[0] for _,f,_ in original)+1,0o100755,0,0,1,0,len(INIT),0,0,0,0,0,0],INIT))
 entries.append(('TRAILER!!!',[0]*13,b''))
 image=out/'candidate.cpio.gz';image.write_bytes(gzip.compress(archive(entries),mtime=0))
 rebuilt=records(gzip.decompress(image.read_bytes()))
 before={n:d for n,_,d in original};after={n:d for n,_,d in rebuilt}
 assert set(after)==set(before)|{'lab-init'}
 assert [n for n in before if before[n]!=after[n]]==['usr/local/bin/modemd-ctrl']
 vm=None;node=None
 with (out/'node.log').open('w') as nl,(out/'qemu.log').open('w') as ql:
  try:
   node=subprocess.Popen(['node',str(ROOT/'lab/bbs/synthmodem_vm_composed.js'),str(candidate),str(out)],stdout=nl,stderr=nl)
   end=time.monotonic()+10
   while not (out/'ports.json').exists():
    assert node.poll() is None, 'Node stopped before listening'
    assert time.monotonic()<end,'Node listen deadline';time.sleep(.05)
   ports=json.loads((out/'ports.json').read_text())
   cmd=['qemu-system-i386','-machine','pc','-accel','tcg','-m','128','-smp','1','-display','none','-monitor','none',
    '-serial','file:'+str(out/'console.log'),'-no-reboot','-nic','none','-kernel',str(media['bzImage']),'-initrd',str(image),
    '-append','console=ttyS0 rdinit=/lab-init panic=-1','-device','virtio-serial-pci,id=serial0']
   for i,key in enumerate(('controlPort','modemPort'),1):
    cmd+=['-chardev',f'socket,id=p{i},host=127.0.0.1,port={ports[key]}',
     '-device',f'virtserialport,bus=serial0.0,nr={i},chardev=p{i},name=lab.port{i}']
   vm=subprocess.Popen(cmd,stdout=ql,stderr=ql)
   # Bound the run as a whole, preserving a specific live process handle.
   end=time.monotonic()+115
   while node.poll() is None:
    assert time.monotonic()<end,'Composed test deadline';time.sleep(.1)
   assert node.returncode==0, f'Node failed: see {out}/node-error.txt and node.log'
   vm.wait(timeout=10)
  finally:
   for child in (node,vm):
    if child is not None and child.poll() is None:child.kill();child.wait()
 result=json.loads((out/'node-result.json').read_text())
 result['checks']['guest_exit_after_actual_session_teardown']=vm.returncode==0 and 'LAB-HELPER-EXIT=1' in (out/'console.log').read_text()
 result['checks']['frozen_inputs_unchanged']=all(sha(ROOT/n)==h for n,h in frozen.items()) and all(sha(candidate/n)==h for n,h in pins.items())
 # Independent Python audit: decode every guest frame, then compare serial and
 # BBS streams against a separately generated all-byte pattern.
 data=(out/'control-wire.bin').read_bytes();frames=[];at=0
 while at<len(data):
  assert at+3<=len(data);length,kind=struct.unpack_from('<HB',data,at)
  assert 1<=length<=4094 and at+length+2<=len(data)
  frames.append((kind,data[at+3:at+length+2]));at+=length+2
 pattern=bytes(range(256))*65536+bytes(range(3))
 modem=(out/'modem-wire.bin').read_bytes();bbs=(out/'bbs-wire.bin').read_bytes()
 result['checks']['independent_forward_audit']=modem[:9]==b'ATZ\rATD1\r' and modem[result['modem_payload_offset']:]==pattern
 guest_rx=b''.join(b for k,b in frames if k==0x15)
 target=f"127.0.0.1:{ports['bbsPort']}\r".encode()
 result['checks']['independent_guest_reverse_audit']=guest_rx==target+pattern
 # Only BINARY WILL/DO replies can precede the reverse payload on this fixture.
 decoded=bytearray();at=0;negotiation=[]
 while at<len(bbs):
  if bbs[at]!=255:decoded.append(bbs[at]);at+=1
  elif at+1<len(bbs) and bbs[at+1]==255:decoded.append(255);at+=2
  else:
   assert at+3<=len(bbs) and bbs[at+1] in (251,252,253,254)
   negotiation.append(list(bbs[at:at+3]));at+=3
 result['checks']['independent_bbs_reverse_audit']=bytes(decoded)==pattern and sorted(negotiation)==sorted([[255,251,0],[255,253,0]])
 result.update({'passed':all(result['checks'].values()),'frozen_inputs':frozen,'candidate_sha256':pins,
  'upstream_revision':REV,'Nix_build':built,'helper_sha256':sha(helper),'media_sha256':MEDIA,
  'candidate_image_sha256':sha(image),'archive_entries_changed':['usr/local/bin/modemd-ctrl'],
  'archive_entries_added':['lab-init'],'qemu_command':cmd,
  'qemu_version':subprocess.check_output(['qemu-system-i386','--version'],text=True).splitlines()[0],
  'guest_frames':len(frames),'wire_sha256':{n:sha(out/n) for n in ('control-wire.bin','modem-wire.bin','bbs-wire.bin')}})
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'passed':result['passed'],'checks':result['checks'],'result':str(out/'result.json')},indent=2))
 return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
