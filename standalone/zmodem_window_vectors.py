"""Literal independent delayed-ACK schedules, shared by DOS/linked fixtures.
These schedules specify packet endings and peer replies; no product code runs.
"""
from check_zmodem import h,meta
from check_zmodem_wire import packet

def vectors(fmt=67,name='TEST.BIN',include_long=False):
 G,Q,E,W=105,106,104,107
 # Header openings are explicit; a tuple is (length,ending,reply).
 # None polls empty, 'ack' returns the exact boundary, integer requests ZRPOS.
 schedules=[
  ('delayed-full-window',18433,0,[
   0,(1024,W,'ack'),1024,
   *[(1024,e,'ack' if e==W else None) for e in (G,Q,G,Q,G,Q,G,W)],9216,
   *[(1024,e,'ack' if e==W else None) for e in (G,Q,G,Q,G,Q,G,W)],17408,
   (1024,G,None),(1,E,None)]),
  ('capacity-independent-of-ACK',10241,4096,[
   0,(1024,W,'ack'),1024,
   *[(1024,e,'ack' if e in (Q,W) else None) for e in (Q,Q,Q,W)],5120,
   *[(1024,e,'ack' if e in (Q,W) else None) for e in (Q,Q,Q,W)],9216,
   (1024,Q,'ack'),(1,E,None)]),
  ('open-frame-reposition',5000,0,[
   0,(1024,W,'ack'),1024,(1024,G,None),(1024,Q,1536),(0,E,None),1536,
   (1024,W,'ack'),2560,(1024,G,None),(1024,Q,None),(392,E,None)])]
 if include_long:
  # Literal 4 KiB storage segments, ACK every 1 KiB, then rewind a whole
  # 128 KiB verified file at EOF. Forward replay ACKs are not fresh failures.
  size=131073;one=[0,(1024,W,'ack')]
  for start in range(1024,size,4096):
   one.append(start);left=min(4096,size-start)
   if left==4096:one.extend((1024,e,'ack') for e in (Q,Q,Q,W))
   else:one.extend([(1024,Q,'ack')]*3+[(1,E,None)])
  schedules.append(('long-confirmed-prefix-replay',size,4096,one+[('eof-rewind',0)]+one))
 result=[]
 for label,size,capacity,actions in schedules:
  body=(bytes(range(256))*((size+255)//256))[:size];ready=h(1,(0x23000000 if fmt==67 else 0x03000000)|capacity)
  rx=list(ready+h(9));tx=h(0)+h(4,0x01000000,fmt)+packet(meta(name,size).ljust(128,b'\0'),fmt,W,0);script=[(h(0),ready),(h(4,0x01000000,fmt)+packet(meta(name,size).ljust(128,b'\0'),fmt,W,0),h(9))]
  offset=0
  for action in actions:
   if isinstance(action,tuple) and action[0]=='eof-rewind':
    wire=h(11,size,fmt);reply=h(9,action[1]);tx+=wire;rx.extend(reply);script.append((wire,reply));continue
   if isinstance(action,int):offset=action;wire=h(10,offset,fmt);reply=b''
   else:
    n,ending,response=action;wire=packet(body[offset:offset+n],fmt,ending,0);offset+=n
    reply=h(3,offset) if response=='ack' else h(9,response) if isinstance(response,int) else b''
    rx.extend(reply)
    # Zero-length CRCE only closes the rejected old frame; no input poll follows.
    if n and ending!=W and not isinstance(response,int):rx.append(65535)
   tx+=wire;script.append((wire,reply))
  tx+=h(11,size,fmt)+h(8)+b'OO';rx.extend(ready+h(8));script.extend([(h(11,size,fmt),ready),(h(8),h(8)),(b'OO',b'')])
  result.append(dict(label=label,body=body,rx=rx,tx=tx,script=script))
 return result
