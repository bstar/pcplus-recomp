#!/usr/bin/env python3
"""Freeze authored CP437 string command fixtures with independent expectations."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SHA='5664fdfae375774da5303cc8b53c00ef773a6650132de73c7206e46ddc05039a'
REPORT='analysis/aspect-string-commands/compiler-03/report.json'
REPORT_SHA='f996bcff0a439444c45473b0170210a7f5cad9a0a59648cf25c8bf846c03cd70'
# Explicit source-level predictions, never inferred from successful compilation
# or maintained runtime output. Native range/overflow errors abort before copy.
EXPECTED={
 'LEN':{'string0':'HELLO','integer0':5},
 'PEEK':{'string0':'ABC','integer0':66},
 'POKE':{'string0':'AZC'},
 'LOWER':{'string0':'abcz09!'}, 'UPPER':{'string0':'ABCZ09!'},
 'LOWHI':{'string0':'aézÇ'}, 'UPHI':{'string0':'AéZÇ'},
 'CAT':{'string0':'ABCD'}, 'CATLEN':{'string0':'ABCD'},
 'CPYLEN':{'string0':'WX'},
 'SET':{'string0':'A'*80}, 'SETLEN':{'string0':'AAADE'},
 'UPDATE':{'string0':'AxyDE'}, 'SUBCOPY':{'string0':'BCD'},
 'CMPEQ':{'integer0':1}, 'CMPNE':{'integer0':1}, 'CMPLEN':{'integer0':1},
 'LENEMP':{'string0':'','integer0':0}, 'LENMAX':{'string0':'A'*80,'integer0':80},
 'CATOFL':{'string0':'A'*79,'error':'operand','native_error':3},
 'CATFULL':{'string0':'A'*80,'error':'operand','native_error':3},
 'CATEMPTY':{'string0':'AB'}, 'CATZERO':{'string0':'AB'},
 'BADLEN':{'string0':'','error':'operand','native_error':1},
 'BADINDEX':{'string0':'ABC','error':'operand','native_error':1},
 'BADCHAR':{'string0':'ABC','error':'operand','native_error':1},
 'SUBEND':{'string0':'Z'}, 'BADSUM':{'string0':'ABCDE','error':'operand','native_error':3},
 'LOCAL':{'string0':'abc'}, 'PARAM':{'string0':'ABC'}, 'PGET':{'integer0':67},
 'LOCALCAT':{'string0':'ABCD'}, 'GLBGLB':{'string0':'ABCD','string1':'CD'},
 'PEEKHI':{'string0':'é','integer0':130}, 'POKEHI':{'string0':'AéC'},
 'SETZERO':{'string0':''},
 'IFEQSTAT':{'integer0':7}, 'IFNESTAT':{'integer0':7},
 'IFLTSTAT':{'integer0':7}, 'IFGTSTAT':{'integer0':7},
 'IFCSSTAT':{'integer0':7}, 'IFHISTAT':{'integer0':7},
 'IFEMPST':{'integer0':7}, 'IFPREFIX':{'integer0':7},
 'IFLOCAL':{'integer0':7}, 'IFPARAM':{'integer0':7},
 'IFNEFAIL':{'integer0':9}, 'IFEQFAIL':{'integer0':9},
 'CMPRLT':{'integer0':65535}, 'CMPRGT':{'integer0':1},
 'CMPREQ':{'integer0':0}, 'CMPZERO':{'integer0':7},
}

def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 path=ROOT/REPORT;raw=path.read_bytes();assert sha(raw)==REPORT_SHA
 report=json.loads(raw);assert report['compiler_sha256']==SHA
 assert report['harness_sha256']==sha((ROOT/'standalone/aspect_string_command_probe.py').read_bytes())
 accepted=[c for c in report['cases'] if c['success']];rejected=[c for c in report['cases'] if not c['success']]
 assert len(report['cases'])==65 and len(accepted)==52 and len(rejected)==13
 assert set(c['name'] for c in accepted)==set(EXPECTED)
 existing=set()
 for group in ['execution','arithmetic','parameter']:
  existing.update(v['name'] for v in json.loads((ROOT/f'standalone/fixtures/aspect_{group}_vectors.json').read_text())['vectors'])
 assert not set(EXPECTED)&existing,'Fixture name collision with existing runtime corpora'
 vectors=[]
 for c in accepted:
  source=c['source'].encode('cp437');wire=bytes.fromhex(c['hex'])
  assert sha(source)==c['source_sha256'] and sha(wire)==c['asx_sha256']
  assert source==(path.parent/(c['name']+'.ASP')).read_bytes() and wire==(path.parent/(c['name']+'.ASX')).read_bytes()
  assert len(c['name'])<=8
  v={k:c[k] for k in ['name','intent','source','source_sha256','hex','asx_sha256']}
  v.update(source_encoding='cp437',expected=EXPECTED[c['name']],dos_excluded=False);vectors.append(v)
 failed=[]
 for c in rejected:
  assert sha(c['source'].encode('cp437'))==c['source_sha256']
  v={k:c[k] for k in ['name','source','source_sha256','errors','log_sha256']};v['source_encoding']='cp437';failed.append(v)
 result=dict(compiler_sha256=SHA,private_report=REPORT,private_report_sha256=REPORT_SHA,
  probe_sha256=report['harness_sha256'],freezer_sha256=sha(Path(__file__).read_bytes()),source_encoding='cp437',
  vectors=vectors,rejected=failed,
  expectation_model='Hand-derived string/character/index arithmetic and ASCII-only case mapping; CP437 high bytes remain unchanged. strcmp is unsigned-byte lexicographic with signed -1/0/1 result. Native builtin FAILURE returns this result; SUCCESS returns result==0. Native operand/overflow errors1/3 become maintained operand error7 before mutation/writeback. No maintained runtime outputs informed these expectations.',
  findings=['Accepted STRLEN string integerdest; STRPEEK string index integerdest; STRPOKE string index character.',
   'Accepted STRCAT/STRCPY dest source [count]; STRSET dest character [count]; STRUPDT/SUBSTR dest source index count.',
   'String indexes are zero-based. Optional length emits01 plus integer operand; omitted length emits00.',
   'Direct IF quoted-string relational expressions rejected in the authored probes; STRCMP followed IF SUCCESS/FAILURE or numeric comparison with FAILURE accepted.',
   'SUCCESS uses numeric builtin27; FAILURE uses21. No other builtin service is needed by this corpus.',
   'Subcopy requires opcodeB6 in addition to AA/AB/AC/AE/AF/B0/B1/B2/B3/B4.',
   'String assignment copy terminates at the requested destination length; bounded fill preserves remaining preexisting string bytes and forces byte80 to NUL.'],
  scope='Original compiler output for authored scripts only, independent expected outcomes and rejected grammar attempts. No original executable/application/resource bytes and no claim of complete language or command coverage.')
 target=ROOT/'standalone/fixtures/aspect_string_command_vectors.json';target.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(dict(vectors=len(vectors),rejected=len(failed),completions=sum('error' not in v['expected'] for v in vectors),operand_stops=sum(v['expected'].get('error')=='operand' for v in vectors),fixture_sha256=sha(target.read_bytes()),freezer_sha256=result['freezer_sha256']),indent=2))
if __name__=='__main__':main()
