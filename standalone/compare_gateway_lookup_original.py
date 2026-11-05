#!/usr/bin/env python3
"""Compare linked direct interpreter selection with genuine native spawn search.
DOS/heap/EXEC are modeled; this does not execute an analysis executable or
establish foreground/UI/UART ownership. Invalid COMSPEC and CRT batch coercion
are explicit maintained-policy differences, excluded from these paired vectors.
"""
import argparse,json
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_DX
from check_program_exec import Program
import check_hook_lookup as shared
from check_gateway_lookup import Gateway
ROOT=shared.ROOT
sha=shared.sha
class Native(Program):
 def interrupt(self,u,n,data):
  if u.reg_read(UC_X86_REG_AX)>>8==0x4b:
   path=self.cstring(u.reg_read(UC_X86_REG_DX));self.exec_error=self.errors.get(path,0 if path in self.files else 2)
  super().interrupt(u,n,data)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--terminal',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 binary=a.terminal.resolve();out=a.output.resolve();assert binary.is_relative_to(ROOT/'build') and out.is_relative_to(ROOT/'build') and not out.exists()
 shared.FOLDER=str(binary.parent.relative_to(ROOT/'build'));manifest=json.loads(binary.with_name('manifest.json').read_text());assert sha(binary)==manifest['binary_sha256'] and manifest['experimental_gateway_lookup']
 out.mkdir(parents=True);cases=[]
 vectors=[
 ('qualified',b'C:\\DOS\\COMMAND.COM',[],[b'C:\\DOS\\COMMAND.COM'],{}),
 ('bare-PATH',b'SHELL.COM',[b'PATH=P;Q'],[b'Q\\SHELL.COM'],{}),
 ('extension',b'SHELL',[],[b'SHELL.exe'],{}),
 ('qualified-extension',b'D:\\DOS\\SHELL',[],[b'D:\\DOS\\SHELL.exe'],{}),
 ('no-system-fallback',b'MISSING.COM',[],[b'COMMAND.COM'],{}),
 ('drive-relative',b'C:SHELL.COM',[b'PATH=Q'],[b'Q\\C:SHELL.COM'],{}),
 ('access-denied',b'SHELL.COM',[b'PATH=Q'],[b'Q\\SHELL.COM'],{b'SHELL.COM':5}),
 ('PATH-denial',b'SHELL.COM',[b'PATH=P;Q'],[b'Q\\SHELL.COM'],{b'P\\SHELL.COM':5}),
 ('empty-first',b'SHELL.COM',[b'PATH=;Q'],[b'Q\\SHELL.COM'],{}),
 ('repeated-delimiters',b'SHELL.COM',[b'PATH=P;;Q'],[b'Q\\SHELL.COM'],{}),
 ('drive-root',b'SHELL.COM',[b'PATH=C:'],[b'C:\\SHELL.COM'],{}),
 ('forward-slash',b'SHELL.COM',[b'PATH=C:/DOS/'],[b'C:/DOS/SHELL.COM'],{}),
 ('UNC-error',b'SHELL.COM',[b'PATH=\\\\HOST\\BIN;Q'],[b'Q\\SHELL.COM'],{b'\\\\HOST\\BIN\\SHELL.COM':5}),
 ('COM-precedence',b'SHELL',[],[b'SHELL.com',b'SHELL.exe'],{}),
 ('invalid-COM-stops',b'SHELL',[],[b'SHELL.com',b'SHELL.exe'],{b'SHELL.com':11})]
 for label,name,variables,files,errors in vectors:
  env=[b'COMSPEC='+name,*variables];source=Gateway(env,files,errors);status,r=source.run_gateway()
  native=Native(original=True);native.files=set(files);native.errors=errors;native.environment(env)
  name_at=native.call('program_getenv',[native.string(b'COMSPEC')]);assert name_at
  argv=native.argv([native.cstring(name_at)]);result=native.call('program_spawn_search',[0,name_at,argv,0],limit=2000000)
  left=[e[:3] for e in source.events if e[0]=='exec'];right=[e[:3] for e in native.events if e[0]=='exec']
  checks=dict(identical_execution_paths_and_tails=left==right,empty_tails=all(e[2]==b'' for e in left),same_success=(status==0)==(result!=65535),no_source_resource_probe=not any(e[0]=='probe' for e in source.events))
  case=dict(case=label,passed=all(checks.values()),checks=checks,source_result=list(r),original_result=result,executions=left);cases.append(case)
  print(label,{k:v for k,v in checks.items() if not v},flush=True);assert case['passed'],(case,right)
 def serial(v):
  if isinstance(v,bytes):return dict(hex=v.hex())
  raise TypeError(type(v).__name__)
 names=('standalone/compare_gateway_lookup_original.py','standalone/check_gateway_lookup.py','standalone/check_hook_lookup.py','standalone/check_program_exec.py','reconstruction/program_exec/provenance.json')
 originals=('analysis/pcplus-originals/PCPLUS-main-2.01.EXE','analysis/pcplus-overlays/manifest.json','build/program-exec/EXECUTOR.EXE','build/program-exec/program_exec.map')
 report=dict(passed=True,binary_sha256=sha(binary),cases=cases,sources={n:sha(ROOT/n) for n in names},original_inputs={n:sha(ROOT/n) for n in originals},scope=__doc__)
 (out/'result.json').write_text(json.dumps(report,indent=2,default=serial)+'\n')
if __name__=='__main__':main()
