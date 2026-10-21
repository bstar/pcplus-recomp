"""Index exact frontend offsets for the existing synchronous control oracle.

The original linear timestamp search is quadratic in long pre-protocol display
prefixes. Require contiguous, nonoverlapping manifests and preserve its result
for every byte; only the lookup changes, not ACK/NAK/time/finish policy.
"""
from bisect import bisect_right
import test_transfer_dos as reference

def audit_controls(protocol,sender_stream,opposite,trace,sender,post_time,ack_timeout=11):
 tables={}
 for direction in ('dos','bbs'):
  rows=sorted((r for r in trace if r['direction']==direction),key=lambda r:r['offset'])
  cursor=0;starts=[]
  for row in rows:
   assert row['offset']==cursor and row['size']>0,'Manifest must cover contiguous exact bytes'
   starts.append(cursor);cursor+=row['size']
  tables[direction]=(starts,rows,cursor)
 def indexed(same_trace,direction,offset):
  assert same_trace is trace
  starts,rows,size=tables[direction];assert 0<=offset<size
  i=bisect_right(starts,offset)-1;row=rows[i]
  assert row['offset']<=offset<row['offset']+row['size']
  return row['seconds']
 original=reference.timestamp
 try:
  reference.timestamp=indexed
  return reference.audit_controls(protocol,sender_stream,opposite,trace,sender,post_time,ack_timeout)
 finally:reference.timestamp=original
