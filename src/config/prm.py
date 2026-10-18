"""Partial, lossless codec for the proved PCPlus 2.01 1264-byte memory image.

There is no proved format signature/version field. Matching the length does not
identify a file. No file IO or defaults copied from a user's installation occur
here. Unknown bytes remain opaque and are preserved exactly.
"""
from dataclasses import dataclass
import struct

IMAGE_SIZE=0x4f0
ORIGINAL_DS_BASE=0x1b84
BAUD_RATES=(300,1200,2400,4800,9600,19200,38400,57600,115200)
PARITIES=('N','O','E','M','S')
# Offsets proved by memory-image IO plus recovered consumer instructions.
WORD_FIELDS={
 'port_index':0,'baud_index':2,'parity_index':4,'stop_bits':6,'data_bits':8,
 'terminal_id':0x1d18-ORIGINAL_DS_BASE,
 'software_flow':0x1d1c-ORIGINAL_DS_BASE,
 'hardware_flow':0x1d1e-ORIGINAL_DS_BASE,
 'autowrap':0x1d20-ORIGINAL_DS_BASE,
 'scroll_enabled':0x1d22-ORIGINAL_DS_BASE,
 'normal_attribute':0x1d32-ORIGINAL_DS_BASE,
 'bold_attribute':0x1d34-ORIGINAL_DS_BASE,
 'preset_attribute':0x1d36-ORIGINAL_DS_BASE,
 'reverse_attribute':0x1d38-ORIGINAL_DS_BASE,
 'underline_attribute':0x1d3a-ORIGINAL_DS_BASE,
 'current_attribute':0x1f70-ORIGINAL_DS_BASE,
 'translation_mode':0x1d64-ORIGINAL_DS_BASE,
}

@dataclass(frozen=True)
class SerialSettings:
 port_index:int
 baud_index:int
 parity_index:int
 stop_bits:int
 data_bits:int

 def validate(self):
  """Enforce the settings actually selectable by the recovered line/port UI."""
  for name,low,high in [('port_index',0,7),('baud_index',0,8),('parity_index',0,4),('stop_bits',1,2),('data_bits',7,8)]:
   value=getattr(self,name)
   if type(value) is not int or not low<=value<=high:raise ValueError(f'{name} outside supported UI range {low}..{high}')

 @property
 def baud(self):
  self.validate();return BAUD_RATES[self.baud_index]

 @property
 def parity(self):
  self.validate();return PARITIES[self.parity_index]

@dataclass(frozen=True)
class LegacyPrm201:
 _image:bytes

 def __post_init__(self):
  object.__setattr__(self,'_image',bytes(self._image))
  if len(self._image)!=IMAGE_SIZE:raise ValueError(f'Expected exactly {IMAGE_SIZE} bytes; version/type identification is external')

 def to_bytes(self):return self._image

 def word(self,name):return struct.unpack_from('<H',self._image,WORD_FIELDS[name])[0]

 def with_word(self,name,value):
  """Edit a proved word location; application validation is separate."""
  if type(value) is not int or not 0<=value<=65535:raise ValueError('Expected unsigned 16-bit integer')
  output=bytearray(self._image);struct.pack_into('<H',output,WORD_FIELDS[name],value)
  return LegacyPrm201(output)

 @property
 def serial(self):return SerialSettings(*(self.word(name) for name in ('port_index','baud_index','parity_index','stop_bits','data_bits')))

 def with_serial(self,settings):
  settings.validate();output=bytearray(self._image)
  struct.pack_into('<5H',output,0,settings.port_index,settings.baud_index,settings.parity_index,settings.stop_bits,settings.data_bits)
  return LegacyPrm201(output)

 def port_io_base(self,index):
  if type(index) is not int or not 0<=index<8:raise ValueError('Expected port index 0..7')
  return struct.unpack_from('<H',self._image,0x1cf8-ORIGINAL_DS_BASE+index*2)[0]

 def port_irq(self,index):
  if type(index) is not int or not 0<=index<8:raise ValueError('Expected port index 0..7')
  return struct.unpack_from('<H',self._image,0x1d08-ORIGINAL_DS_BASE+index*2)[0]

 def modem_bytes(self,name,index=None):
  offset,size=_modem_region(name,index);region=self._image[offset:offset+size]
  if b'\0' not in region:raise ValueError('Unterminated modem field; opaque image preserved')
  return region.split(b'\0',1)[0]


 def with_modem_bytes(self,name,value,index=None):
  offset,size=_modem_region(name,index);value=bytes(value)
  if b'\0' in value or len(value)>=size:raise ValueError(f'Expected at most{size-1} non-NUL bytes')
  # Preserve all unknown bytes, including old bytes after the new terminator.
  output=bytearray(self._image);output[offset:offset+len(value)+1]=value+b'\0'
  return LegacyPrm201(output)


 def byte(self,name):return self._image[BYTE_FIELDS[name]]
 def with_byte(self,name,value):
  if type(value) is not int or not 0<=value<=255:raise ValueError('Expected unsigned8-bit integer')
  output=bytearray(self._image);output[BYTE_FIELDS[name]]=value;return LegacyPrm201(output)

# Capacities include the NUL terminator; proved overlay19 string-edit bounds.
# Responses are ALREADY expanded bytes in the image, unlike command strings.
MODEM_COMMAND_FIELDS={
 'initialization':(0x1b9c-ORIGINAL_DS_BASE,47),
 'dial_prefix':(0x1bcb-ORIGINAL_DS_BASE,25),
 'dial_suffix':(0x1be4-ORIGINAL_DS_BASE,25),
 'hangup':(0x1bfd-ORIGINAL_DS_BASE,25),
 'answer_on':(0x1c16-ORIGINAL_DS_BASE,25),
 'answer_off':(0x1c2f-ORIGINAL_DS_BASE,25),
}
MODEM_RESPONSE_COUNT=11
MODEM_RESPONSE_SIZE=16
WORD_FIELDS.update({
 'dial_timeout_seconds':0x1b8e-ORIGINAL_DS_BASE,
 'redial_pause_seconds':0x1b90-ORIGINAL_DS_BASE,
 'modem_autobaud':0x1b92-ORIGINAL_DS_BASE,
 'abort_drop_dtr':0x1b94-ORIGINAL_DS_BASE,
 'initialize_while_connected':0x1b98-ORIGINAL_DS_BASE,
 'dial_cycle_limit':0x1b9a-ORIGINAL_DS_BASE,
 'command_character_delay_units':0x1d68-ORIGINAL_DS_BASE,
 'break_delay_units':0x1d28-ORIGINAL_DS_BASE,
})
BYTE_FIELDS={'dial_abort_character':0x1b96-ORIGINAL_DS_BASE,
             'command_pause_character':0x1d66-ORIGINAL_DS_BASE}


def expand_modem_command(value):
 """Reimplement resident4934's valid bounded caret expansion, no transmission.

 ^@ becomes ff (the original sender's NUL sentinel); ^^^ becomes literal ^;
 other ^x becomes x&1f, including ^^ ->1e. A trailing caret is rejected rather
 than following the original out-of-bounds read. Input is a byte string without
 its C terminator. NUL and >128-byte input are rejected at this maintained API.
 """
 value=bytes(value)
 if b'\0' in value or len(value)>128:raise ValueError('Expected at most128 non-NUL bytes')
 result=bytearray();i=0
 while i<len(value):
  ch=value[i];i+=1
  if ch==94:
   if i==len(value):raise ValueError('Trailing caret has no bounded original expansion')
   following=value[i];i+=1
   if following==64:ch=255
   elif following==94 and i<len(value) and value[i]==94:ch=94;i+=1
   else:ch=following&31
  result.append(ch)
 return bytes(result)


def modem_command_events(value,pause_character,character_delay_units):
 """Pure plan of resident48cc; explicit units, no clock/UART side effects.

 Pause calls BIOS delay6b98(9), which waits10 tick changes. Ordinary bytes
 call transmit, then calibrated delay6b72. Sentinelff transmitsNUL without
 character pacing. Local echo (DS1d1a), when enabled, applies to ordinary bytes
 only and is deliberately outside this transport-independent event plan.
 """
 if type(pause_character) is not int or not 0<=pause_character<=255:raise ValueError('Expected uint8 pause character')
 if type(character_delay_units) is not int or not 0<=character_delay_units<=65535:raise ValueError('Expected uint16 delay units')
 events=[]
 for ch in expand_modem_command(value):
  if ch==0:break # Original48cc iterates an expanded NUL-terminated buffer.
  if ch==pause_character:events.append(('pause_bios_tick_changes',10))
  elif ch==255:events.append(('transmit',0))
  else:events.extend([('transmit',ch),('character_delay_units',character_delay_units)])
 return tuple(events)


def _modem_region(name,index=None):
 if name=='response':
  if type(index) is not int or not 0<=index<MODEM_RESPONSE_COUNT:raise ValueError('Expected response index0..10')
  return 0x1c48-ORIGINAL_DS_BASE+index*MODEM_RESPONSE_SIZE,MODEM_RESPONSE_SIZE
 if index is not None:raise ValueError('Only response fields have an index')
 return MODEM_COMMAND_FIELDS[name]
