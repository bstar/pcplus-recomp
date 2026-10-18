"""Synthetic modem+serial subset; not full original PRM defaults."""
import struct
from terminal_config_fixtures import image

def fixture(*,timeout=3,autobaud=0,drop=1,initialize=1):
 data=bytearray(image(port=1,baud=6,soft=0,hard=1,normal=7))
 struct.pack_into('<7H',data,10,timeout,0,autobaud,drop,27,initialize,1)
 for offset,size,text in [(0x18,47,b'ATZ^M'),(0x47,25,b'ATD'),(0x60,25,b'^M'),(0x79,25,b'+++~ATH^M'),(0x92,25,b''),(0xab,25,b'')]:
  data[offset:offset+size]=text+b'\0'*(size-len(text))
 responses=[b'CONNECT',b'CON1200',b'CON2400',b'CON4800',b'CON9600',b'CON19200',b'CON38400',b'NO CARRIER',b'BUSY',b'VOICE',b'TIMEOUT']
 for i,text in enumerate(responses):data[0xc4+i*16:0xc4+(i+1)*16]=text.ljust(16,b'\0')
 data[0x12]=27;data[0x1e2]=ord('~');struct.pack_into('<H',data,0x1e4,30)
 return bytes(data)
