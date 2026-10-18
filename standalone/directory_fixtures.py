"""Synthetic23050-byte directories; no private entries or full PRM defaults."""
import struct
from modem_fixtures import fixture
from terminal_config_fixtures import BASES,IRQS
def prm(*,port=1,baud=6,soft=0,hard=1):
 data=bytearray(fixture(timeout=5))
 struct.pack_into('<2H',data,0,port-1,baud)
 for i,(base,irq) in enumerate(zip(BASES,IRQS)):
  struct.pack_into('<H',data,0x174+i*2,base);struct.pack_into('<H',data,0x184+i*2,irq)
 struct.pack_into('<2H',data,0x198,soft,hard)
 return bytes(data)
def directory(*,entry=1,target=b'CaseTest:23',port=0,baud=6,profile=6,direct=0):
 data=bytearray(23050)
 for i in range(200):
  offset=250+i*114;name=f'LAB NODE {i+1:03}'.encode();number=f'Node{i+1:03}:23'.encode()
  data[offset:offset+len(name)]=name;data[offset+25:offset+25+len(number)]=number
  struct.pack_into('<H',data,offset+46,6)
  data[offset+49]=8;data[offset+50]=1;data[offset+61:offset+69]=b'00/00/00'
  data[offset+72]=4;data[offset+73]=6
 at=250+(entry-1)*114
 data[at+25:at+46]=target.ljust(21,b'\0');struct.pack_into('<H',data,at+46,baud)
 data[at+73]=profile;data[at+74]=direct;data[at+104]=port
 data[:3]=b'9,\0'
 return bytes(data)
