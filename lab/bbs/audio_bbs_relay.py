"""Passive byte-transparent loopback relay with explicit owned BBS endpoint."""
import select,socket,threading,time


class Relay:
 def __init__(self,target_port):
  assert isinstance(target_port,int) and 1024<=target_port<=65535
  self.target_port=target_port;self.server=socket.socket();self.server.bind(('127.0.0.1',0));self.server.listen(1);self.server.settimeout(120)
  self.port=self.server.getsockname()[1];self.stop=threading.Event();self.errors=[]
  self.to_bbs=bytearray();self.from_bbs=bytearray();self.trace=[];self.thread=threading.Thread(target=self.run,daemon=True)
 def run(self):
  start=time.monotonic_ns()
  try:
   client,_=self.server.accept()
   with client,socket.create_connection(('127.0.0.1',self.target_port),timeout=3) as bbs:
    while not self.stop.is_set():
     ready,_,_=select.select([client,bbs],[],[],.1)
     for source in ready:
      body=source.recv(4096)
      if not body:return
      target,stream,direction=(bbs,self.to_bbs,'to_bbs') if source is client else (client,self.from_bbs,'from_bbs')
      now=time.monotonic_ns();self.trace.append({'direction':direction,'offset':len(stream),'count':len(body),'seconds':(now-start)/1e9,'monotonic_ns':str(now)})
      stream.extend(body);target.sendall(body)
  except Exception as error:
   if not self.stop.is_set():self.errors.append(repr(error))
  finally:self.server.close()
