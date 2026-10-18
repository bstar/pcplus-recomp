"""Synthetic partial PRM fixtures; deliberately not full startup defaults."""
import struct
RATES=(300,1200,2400,4800,9600,19200,38400,57600,115200)
BASES=(0x3f8,0x2f8,0x3e8,0x2e8);IRQS=(4,3,4,3)
def image(*,port=2,baud=5,parity=0,bits=8,stop=1,soft=0,hard=1,profile=6,wrap=1,scroll=1,normal=0x1e,translation=0):
 data=bytearray(b'\xa5'*1264)
 struct.pack_into('<5H',data,0,port-1,baud,parity,stop,bits)
 struct.pack_into('<H',data,0x174+(port-1)*2,BASES[port-1])
 struct.pack_into('<H',data,0x184+(port-1)*2,IRQS[port-1])
 for offset,value in [(0x1e0,translation),(0x194,profile),(0x198,soft),(0x19a,hard),(0x19c,wrap),(0x19e,scroll),(0x1ae,normal),(0x1b0,0x2f),(0x1b2,0x3f),(0x1b4,0x70),(0x1b6,1),(0x3ec,0xffff)]:struct.pack_into('<H',data,offset,value)
 return bytes(data)
def change(data,offset,value):
 result=bytearray(data);struct.pack_into('<H',result,offset,value);return bytes(result)
