#!/usr/bin/env python3
"""Freeze authored arithmetic fixtures and independently hand-derived expectations.

Optional analysis step: original compiler output is read only here, never by the
normal source-only build. No expression parser/evaluator derives expected values
from ASX; the explicit table below is reviewed against each authored source.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SHA='5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
REPORT='analysis/aspect-arithmetic/compiler-02/report.json'
REPORT_SHA='a2cce3421cfe0d30c3573ebf81e17373c04e51149b121f30abfc1ed30361f248'

# Explicit source-level final outcomes. Values may be signed here; freezing
# converts them to unsigned bank bit patterns. No target execution informs them.
# Each tuple is (bank, declaration index, mathematical outcome or stop name).
OUTCOMES={
 'IADD':('integer',3,22), 'ICADD':('integer',3,22),
 'ISUB':('integer',3,12), 'ICSUB':('integer',3,12),
 'IMUL':('integer',3,85), 'ICMUL':('integer',3,85),
 'IDIV':('integer',3,3), 'ICDIV':('integer',3,3),
 'IMOD':('integer',3,2), 'ICMOD':('integer',3,2),
 'INEGVAR':('integer',3,-17), 'IDOUBLE':('integer',3,16),
 'INEGPAR':('integer',3,-22), 'IPREC':('integer',3,42),
 'IPAREN':('integer',3,110), 'IPSUB':('integer',3,7),
 'IPDIV':('integer',3,0), 'IPMIX':('integer',3,90),
 'ILEFT':('integer',3,42), 'IKCONST':('integer',3,22),
 'IKDIV':('integer',3,3), 'IKMOD':('integer',3,2),
 'IDZ':('integer',3,'divide_zero'), 'IMZ':('integer',3,'divide_zero'),
 'ICDZ':('integer',3,'divide_zero'), 'ICMZ':('integer',3,'divide_zero'),
 'LADD':('long',3,65542), 'LCADD':('long',3,65542),
 'LSUB':('long',3,65532), 'LCSUB':('long',3,65532),
 'LMUL':('long',3,327685), 'LCMUL':('long',3,327685),
 'LDIV':('long',3,13107), 'LCDIV':('long',3,13107),
 'LMOD':('long',3,2), 'LCMOD':('long',3,2),
 'LNEGVAR':('long',3,-65537), 'LDOUBLE':('long',3,65536),
 'LNEGPAR':('long',3,-65542), 'LPREC':('long',3,65562),
 'LPAREN':('long',3,327710), 'LPSUB':('long',3,65527),
 'LPDIV':('long',3,2621), 'LPMIX':('long',3,327690),
 'LLEFT':('long',3,65562), 'LKCONST':('long',3,22),
 'LKDIV':('long',3,3), 'LKMOD':('long',3,2),
 'LDZ':('long',3,'divide_zero'), 'LMZ':('long',3,'divide_zero'),
 'LCDZ':('long',3,'divide_zero'), 'LCMZ':('long',3,'divide_zero'),
 'IMAX':('integer',0,32768), 'IMIN':('integer',0,-32769),
 'INEGDIV':('integer',0,-3), 'INEGMOD':('integer',0,-2),
 'IDIVOV':('integer',0,32768), 'INEGMIN':('integer',0,32768),
 'I65535':('integer',0,65535), 'I32768':('integer',0,32768),
 'LNEG':('long',0,-65537), 'LMAX':('long',0,2147483648),
 'LMIN':('long',0,-2147483649), 'LDIVOV':('long',0,2147483648),
 'LNEGDIV':('long',0,-13107), 'LNEGMOD':('long',0,-2),
 'LTOOWIDE':('long',0,4294967296), 'LHEXSIGN':('long',0,0xffffffff),
 'LSUFF':('long',0,22), 'LMIX':('long',0,65542),
 'LCONST':('long',0,22), 'LCMIX':('long',0,22),
 'IWRAP':('integer',0,65536), 'LFLOAT':('long',0,'float'),
 'IADDEDGE':('integer',2,32768), 'ISUBEDGE':('integer',2,-32769),
 'IDIVEDGE':('integer',2,'native_int0'), 'IMODEDGE':('integer',2,'native_int0'),
 'LADDEDGE':('long',2,2147483648), 'LSUBEDGE':('long',2,-2147483649),
 'LDIVEDGE':('long',2,2147483648), 'LMODEDGE':('long',2,0),
 'MIXVAR':('long',1,65542), 'MIXREV':('long',1,65542),
 'CHAIN':('integer',2,6), 'PREFIX':('integer',0,2),
}

# Explicit initialized/modified input banks, checked in addition to outcome.
EDGE_INPUTS={
 'IADDEDGE':(32767,1), 'ISUBEDGE':(-32768,1),
 'IDIVEDGE':(-32768,-1), 'IMODEDGE':(-32768,-1),
 'LADDEDGE':(2147483647,1), 'LSUBEDGE':(-2147483648,1),
 'LDIVEDGE':(-2147483648,-1), 'LMODEDGE':(-2147483648,-1),
}


def sha(data):return hashlib.sha256(data).hexdigest()


def bits(bank,value):
 return value & (0xffff if bank=='integer' else 0xffffffff)


def expectation(name):
 bank,index,value=OUTCOMES[name]
 result={}
 if index==3:
  a,b,c=(17,5,5) if bank=='integer' else (65537,5,5)
  if name in ('IDOUBLE','LDOUBLE'):a-=1
  result.update({bank+'0':bits(bank,a),bank+'1':b,bank+'2':c})
 elif name in EDGE_INPUTS:
  a,b=EDGE_INPUTS[name]
  result.update({bank+'0':bits(bank,a),bank+'1':bits(bank,b)})
 elif name in ('MIXVAR','MIXREV'):
  result.update(integer0=5,long0=65537)
 elif name=='CHAIN':
  result.update(integer0=6,integer1=5)
 error=value if isinstance(value,str) else None
 if error:
  result['error']=error
 else:
  result[bank+str(index)]=bits(bank,value)
 unsigned=None if error else bits(bank,value)
 signed=None if error else unsigned-(1<<(16 if bank=='integer' else 32)) if unsigned&(1<<(15 if bank=='integer' else 31)) else unsigned
 return result,dict(bank=bank,index=index,value=unsigned,signed_value=signed,
  mathematical_value=None if error else value)


def main():
 path=ROOT/REPORT;data=path.read_bytes();assert sha(data)==REPORT_SHA
 report=json.loads(data);assert report['compiler_sha256']==SHA
 probe=ROOT/'standalone/aspect_arithmetic_probe.py'
 assert report['harness_sha256']==sha(probe.read_bytes())
 assert len(report['cases'])==88
 accepted=[c for c in report['cases'] if c['success']]
 assert len(accepted)==86 and set(c['name'] for c in accepted)==set(OUTCOMES)
 assert {c['name'] for c in report['cases'] if not c['success']}=={'IUNIT','LUNIT'}
 vectors=[]
 for case in accepted:
  name=case['name'];source=case['source'].encode('ascii');wire=bytes.fromhex(case['hex'])
  assert sha(source)==case['source_sha256'] and sha(wire)==case['asx_sha256']
  assert (path.parent/(name+'.ASP')).read_bytes()==source
  assert (path.parent/(name+'.ASX')).read_bytes()==wire
  expected,outcome=expectation(name)
  fault=expected.get('error')=='native_int0'
  vector={k:case[k] for k in ['name','intent','source','source_sha256','hex','asx_sha256']}
  vector.update(expected=expected,outcome=outcome,dos_excluded=False,dos_requires_int0_owner=fault)
  if fault:
   vector['native_fault_note']='Word variable MIN/-1 reaches native IDIV INT0. DOS execution requires the maintained scoped INT0 owner; expected ASPECT_RUN_ARITHMETIC_FAULT=12. No unowned DOS execution.'
  vectors.append(vector)
 frozen=dict(compiler_sha256=SHA,private_report=REPORT,private_report_sha256=REPORT_SHA,
  probe_sha256=report['harness_sha256'],freezer_sha256=sha(Path(__file__).read_bytes()),
  expectation_model='Hand-authored source arithmetic and input snapshots; signed division truncates toward zero, remainder follows dividend; storage records modulo2^16/2^32 bit patterns. Results are independent expectations, not inferred from compilation success or maintained runtime output.',
  original_permissiveness='4294967296 literal wraps to zero in the frozen original compiler output; this preserves the observed fixture and does not prescribe future compiler policy.',
  error_codes=dict(divide_zero=11,native_int0=12),
  vectors=vectors,
  scope='Authored source and original-compiler-produced ASX only, with independent expected bank values/stops. No original compiler/application/resources included. Normal builds consume frozen vectors without original inputs.')
 target=ROOT/'standalone/fixtures/aspect_arithmetic_vectors.json'
 target.write_text(json.dumps(frozen,indent=2)+'\n')
 print(json.dumps(dict(path=str(target.relative_to(ROOT)),vectors=len(vectors),
  expected_completions=sum('error' not in v['expected'] for v in vectors),
  expected_stops={e:sum(v['expected'].get('error')==e for v in vectors) for e in ['divide_zero','native_int0','float']},
  fixture_sha256=sha(target.read_bytes()),freezer_sha256=frozen['freezer_sha256']),indent=2))


if __name__=='__main__':main()
