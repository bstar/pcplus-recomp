#!/usr/bin/env python3
"""Boot the Nix-built i386 helper; isolated virtio modem stand-in, no DSP/audio."""
import argparse,gzip,hashlib,json,select,socket,struct,subprocess,threading,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REV='b1752e4d0039e0cff72735924e03aa99922723a8'
MEDIA={'bzImage':'2bac10d87a024026de6c00539ea70d19194169b6b99111d9178815b470d77dbe',
 'rootfs-slmodemd-pjsip.cpio.gz':'c52f230a8b38a8e3476b4a669948e02dd615a367ab0f649251e93209fd659ead'}
INIT=b'''#!/bin/busybox sh
export PATH=/bin:/sbin:/usr/bin:/usr/local/bin
mount -t proc proc /proc
mount -t sysfs sysfs /sys
mount -t devtmpfs devtmpfs /dev
for m in virtio virtio_ring virtio_pci_modern_dev virtio_pci_legacy_dev virtio_pci virtio_console; do
 insmod /lib/modules/virtio/$m.ko || exit 80
done
i=0
while [ ! -e /dev/vport0p2 ]; do
 sleep 0.1
 i=$((i+1))
 [ "$i" -lt 50 ] || exit 81
done
echo LAB-BOOT-I386
SYNTHMODEM_CONTROL_PATH=/dev/vport0p1 SYNTHMODEM_PTY_PATH=/dev/vport0p2 SYNTHMODEM_BUILD_ID=pcplus-nix-i386 /usr/local/bin/modemd-ctrl
result=$?
echo LAB-HELPER-EXIT=$result
poweroff -f
'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def records(data):
 at=0;entries=[]
 while at<len(data):
  assert data[at:at+6]==b'070701'
  fields=[int(data[at+6+i*8:at+14+i*8],16) for i in range(13)]
  name=data[at+110:at+109+fields[11]].decode();start=(at+110+fields[11]+3)&~3
  body=data[start:start+fields[6]];assert len(body)==fields[6];at=(start+fields[6]+3)&~3
  if name=='TRAILER!!!':break
  assert not name.startswith('/') and '..' not in Path(name).parts
  entries.append((name,fields,body))
 return entries
def archive(entries):
 out=bytearray()
 for name,fields,data in entries:
  fields=list(fields);fields[6]=len(data);fields[11]=len(name.encode())+1
  out.extend(b'070701'+b''.join(f'{n:08x}'.encode() for n in fields)+name.encode()+b'\0')
  out.extend(b'\0'*(-len(out)%4));out.extend(data);out.extend(b'\0'*(-len(out)%4))
 return bytes(out)
def frame(kind,data=b''):return struct.pack('<HB',len(data)+1,kind)+data

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();assert out.is_relative_to(ROOT/'build');out.mkdir(parents=True,exist_ok=False)
 names=['lab/bbs/synthmodem_vm_control.py','nix/flake.nix','nix/flake.lock','tools/modem-dev',
        'lab/bbs/patches/synthmodem-control/control.patch']
 frozen={n:sha(ROOT/n) for n in names}
 built=json.loads(subprocess.check_output(['nix','--extra-experimental-features','nix-command flakes',
  'build',str(ROOT/'nix')+'#synthmodem-control-i386','--no-link','--json'],text=True))
 helper=Path(built[0]['outputs']['out'])/'bin/modemd-ctrl'
 elf=helper.read_bytes();assert elf[:5]==b'\x7fELF\x01' and struct.unpack_from('<H',elf,18)[0]==3
 assert 'INTERP' not in subprocess.check_output(['readelf','-l',str(helper)],text=True)
 media={}
 for name,h in MEDIA.items():
  path=ROOT/'build/bbs-lab/synthmodem-vm-cache/vm/images'/name
  if not path.exists():
   b=urllib.request.urlopen(f'https://raw.githubusercontent.com/synexo/synthmodem/{REV}/vm/images/{name}',timeout=30).read()
   assert hashlib.sha256(b).hexdigest()==h;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b)
  assert sha(path)==h;media[name]=path
 original=records(gzip.decompress(media['rootfs-slmodemd-pjsip.cpio.gz'].read_bytes()));entries=[];replaced=0
 for name,fields,data in original:
  if name=='usr/local/bin/modemd-ctrl':data=elf;replaced+=1
  entries.append((name,fields,data))
 assert replaced==1 and 'lab-init' not in {x[0] for x in original}
 inode=max(x[1][0] for x in original)+1
 entries.append(('lab-init',[inode,0o100755,0,0,1,0,len(INIT),0,0,0,0,0,0],INIT))
 entries.append(('TRAILER!!!',[0]*13,b''))
 image=out/'candidate.cpio.gz';image.write_bytes(gzip.compress(archive(entries),mtime=0))
 rebuilt=records(gzip.decompress(image.read_bytes()))
 old={n:hashlib.sha256(d).hexdigest() for n,_,d in original};new={n:hashlib.sha256(d).hexdigest() for n,_,d in rebuilt}
 assert set(new)==set(old)|{'lab-init'}
 assert [n for n in old if old[n]!=new[n]]==['usr/local/bin/modemd-ctrl']
 listeners=[]
 for _ in range(2):
  s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF,4096);s.bind(('127.0.0.1',0));s.listen(1);s.settimeout(10);listeners.append(s)
 cmd=['qemu-system-i386','-machine','pc','-accel','tcg','-m','128','-smp','1','-display','none','-monitor','none',
  '-serial','file:'+str(out/'console.log'),'-no-reboot','-nic','none','-kernel',str(media['bzImage']),'-initrd',str(image),
  '-append','console=ttyS0 rdinit=/lab-init panic=-1','-device','virtio-serial-pci,id=serial0']
 for i,s in enumerate(listeners,1):
  cmd+=['-chardev',f'socket,id=p{i},host=127.0.0.1,port={s.getsockname()[1]}',
        '-device',f'virtserialport,bus=serial0.0,nr={i},chardev=p{i},name=lab.port{i}']
 checks={};packet_buf=bytearray();packets=[];data_rx=bytearray();host_wire=bytearray()
 def receive_until(conn,predicate,timeout=15):
  deadline=time.monotonic()+timeout
  while not predicate():
   left=deadline-time.monotonic();assert left>0,'Guest control deadline';assert select.select([conn],[],[],left)[0]
   b=conn.recv(65536);assert b,'Guest control EOF';packet_buf.extend(b);host_wire.extend(b)
   while len(packet_buf)>=3:
    length,kind=struct.unpack_from('<HB',packet_buf);assert 1<=length<=4094
    if len(packet_buf)<length+2:break
    body=bytes(packet_buf[3:length+2]);packets.append((kind,body));del packet_buf[:length+2]
    if kind==0x15:data_rx.extend(body)
 def exact(conn,count,timeout=15):
  b=bytearray();deadline=time.monotonic()+timeout
  while len(b)<count:
   left=deadline-time.monotonic();assert left>0,('Guest modem deadline',len(b),count)
   assert select.select([conn],[],[],left)[0];part=conn.recv(min(65536,count-len(b)));assert part;b.extend(part)
  return bytes(b)
 errors=[];workers=[];connections=[]
 with (out/'qemu.log').open('w') as log:
  vm=subprocess.Popen(cmd,stdout=log,stderr=log)
  try:
   ctrl=listeners[0].accept()[0];modem=listeners[1].accept()[0];connections=[ctrl,modem]
   for s in connections:s.setsockopt(socket.SOL_SOCKET,socket.SO_SNDBUF,4096)
   receive_until(ctrl,lambda:any(k==0x10 for k,_ in packets))
   checks['guest_HELLO_matches_build']=any(k==0x10 and b'pcplus-nix-i386' in b for k,b in packets)
   ctrl.sendall(frame(0x11,b'ATZ')+frame(0x11,b'ATD1'))
   checks['coalesced_guest_AT_exact']=exact(modem,9)==b'ATZ\rATD1\r'
   modem.sendall(b'\r\nOK\r\nCONNECT 14400\r\n')
   receive_until(ctrl,lambda:any(k==0x13 and b'"connect"' in b for k,b in packets))
   checks['guest_actual_mode_transition']=True
   payload=bytes(range(256))*65536+b'XYZ'
   def forward():
    try:
     for at in range(0,len(payload),4093):ctrl.sendall(frame(0x14,payload[at:at+4093]))
    except Exception as e:errors.append(repr(e))
   worker=threading.Thread(target=forward,daemon=True);workers.append(worker);worker.start();time.sleep(.2)
   checks['forward_source_backpressured']=worker.is_alive()
   modem.sendall(b'FORWARD-STALL-LIVE')
   receive_until(ctrl,lambda:b'FORWARD-STALL-LIVE' in data_rx,timeout=2)
   checks['reverse_service_during_forward_stall']=bytes(data_rx)==b'FORWARD-STALL-LIVE'
   data_rx.clear()
   received=exact(modem,len(payload));worker.join(3)
   checks['forward_payload_exact']=received==payload;checks['forward_worker_complete']=not worker.is_alive()
   (out/'forward.bin').write_bytes(received)
   reverse=bytes(range(256))*65536+b'XYZ'
   def backward():
    try:modem.sendall(reverse)
    except Exception as e:errors.append(repr(e))
   worker=threading.Thread(target=backward,daemon=True);workers.append(worker);worker.start();time.sleep(.2)
   checks['reverse_source_backpressured']=worker.is_alive()
   ctrl.sendall(frame(0x14,b'REVERSE-STALL-LIVE'))
   checks['forward_service_during_reverse_stall']=exact(modem,18,timeout=2)==b'REVERSE-STALL-LIVE'
   receive_until(ctrl,lambda:len(data_rx)>=len(reverse));worker.join(3)
   checks['reverse_payload_exact']=bytes(data_rx)==reverse;checks['reverse_worker_complete']=not worker.is_alive()
   (out/'reverse.bin').write_bytes(data_rx)
   ctrl.close();vm.wait(timeout=10)
   checks['guest_exited_after_transport_close']=vm.returncode==0 and 'LAB-HELPER-EXIT=1' in (out/'console.log').read_text()
  finally:
   for s in connections:
    try:s.close()
    except OSError:pass
   for s in listeners:s.close()
   if vm.poll() is None:vm.kill();vm.wait()
   for t in workers:t.join(2)
 checks['no_worker_errors']=not errors;checks['workers_stopped']=all(not t.is_alive() for t in workers)
 assert all(sha(ROOT/n)==h for n,h in frozen.items()),'Inputs changed'
 (out/'control-wire.bin').write_bytes(host_wire)
 result={'passed':all(checks.values()),'checks':checks,'errors':errors,'frozen_inputs':frozen,'Nix_build':built,
  'helper_sha256':sha(helper),'ELF_class':'ELF32 static Intel i386','media_sha256':MEDIA,'candidate_image_sha256':sha(image),
  'archive_entries_changed':['usr/local/bin/modemd-ctrl'],'archive_entries_added':['lab-init'],
  'forward_bytes':len(payload),'forward_sha256':sha(out/'forward.bin'),'reverse_bytes':len(reverse),'reverse_sha256':sha(out/'reverse.bin'),
  'qemu_command':cmd,'qemu_version':subprocess.check_output(['qemu-system-i386','--version'],text=True).splitlines()[0],
  'scope':'Actual Nix-built i386 helper in booted upstream Linux VM over virtio control and modem-stand-in character ports. No Node writer, actual modem DSP, SIP/RTP/audio, DOS/BBS or hardware.'}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
 return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())

