#!/usr/bin/env python3
"""Compare banked deadline selection with the accepted resident source build.

Actual linked instructions/bridges execute; BIOS/UART boundaries are modeled.
The baseline is a diagnostic input only, never an application build input.
"""
import argparse,hashlib,itertools,json,re,struct,tempfile
from pathlib import Path
import check_transport as transport
from check_modem_far_live import Modem
from terminal_memory import inspect_terminal_memory
from unicorn.x86_const import UC_X86_REG_DS,UC_X86_REG_SS
ROOT=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def symbols(folder):
    return {n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',(folder/'terminal.map').read_text(),re.M|re.I)}

def raw_at(image,symbol):
    return struct.unpack_from('<H',image,8)[0]*16+symbol[0]*16+symbol[1]

def load(folder):
    transport.BINARY=folder/'TERMINAL.EXE';transport.MAP=folder/'terminal.map'
    return Modem()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--product',type=Path,required=True);p.add_argument('--menu',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    baseline,product,menu,output=(v.resolve() for v in (a.baseline,a.product,a.menu,a.output))
    assert all(v.is_relative_to(ROOT/'build') for v in (baseline,product,menu,output)) and not output.exists();output.mkdir(parents=True)
    old_symbols=symbols(baseline);old_image=(baseline/'TERMINAL.EXE').read_bytes()
    begin=raw_at(old_image,old_symbols['terminal_transfer_set_budget']);end=raw_at(old_image,old_symbols['terminal_transfer_shutdown'])
    assert 64<end-begin<256 and old_symbols['terminal_transfer_set_budget'][0]==old_symbols['terminal_transfer_shutdown'][0]==0
    body=old_image[begin:end];old=load(baseline);models=[('resident',old,'terminal_transfer_set_budget',False)]
    products={};frozen={str(baseline/'TERMINAL.EXE'):sha(baseline/'TERMINAL.EXE'),str(baseline/'terminal.map'):sha(baseline/'terminal.map')}
    for name,folder in (('banked',product),('original-menu',menu)):
        image=(folder/'TERMINAL.EXE').read_bytes();syms=symbols(folder);at=raw_at(image,syms['terminal_transfer_set_budget_impl'])
        assert image[at:at+len(body)]==body,'Relocation changed deadline instruction bytes'
        memory=inspect_terminal_memory(folder/'TERMINAL.EXE',folder/'terminal.map')
        assert memory['modem_bridge_pairs_verified']==24 and memory['resident_CS_extent_bytes']<65536
        models.extend([(name+'-entry',load(folder),'terminal_transfer_set_budget',False),(name+'-implementation',load(folder),'terminal_transfer_set_budget_impl',True)])
        products[name]={'binary_sha256':sha(folder/'TERMINAL.EXE'),'map_sha256':sha(folder/'terminal.map'),'memory':memory,'body_sha256':hashlib.sha256(image[at:at+len(body)]).hexdigest()}
        frozen.update({str(folder/'TERMINAL.EXE'):sha(folder/'TERMINAL.EXE'),str(folder/'terminal.map'):sha(folder/'terminal.map')})
    rates=[(r,0) for r in (0,299,300,599,600,1199,1200,2399,2400,4799,4800,9599,9600,19200,38400,65535)]+[(0,1),(49664,1)]
    contexts=((0,0),(1,0),(5,0),(6,0),(6,1),(9,0));cases=[]
    for protocol,(state,direct),(low,high) in itertools.product(range(3),contexts,rates):
        results=[];budgets=[]
        for label,m,entry,far in models:
            for key,value in [('terminal_transfer_protocol',protocol),('connection_state',state),('terminal_directory_mode',direct),('terminal_baud_low',low),('terminal_baud_high',high),('transfer_progress_budget',0xbeef)]:m.put(key,value)
            results.append(m.invoke(entry,far=far));budgets.append(m.get('transfer_progress_budget'))
            assert m.uc.reg_read(UC_X86_REG_DS)==m.uc.reg_read(UC_X86_REG_SS)==m.ds
            assert not m.tx and not m.controls,'Pure selector touched UART/modem'
        assert all(r==results[0] for r in results) and all(b==budgets[0] for b in budgets),(protocol,state,direct,low,high,results,budgets)
        cases.append({'protocol':protocol,'connection_state':state,'direct':direct,'baud_low':low,'baud_high':high,'budget':budgets[0],'passed':True})
    # The map/relocation verifier must inspect the newly added bridge itself.
    image=(product/'TERMINAL.EXE').read_bytes();syms=symbols(product);listing=(product/'terminal.map').read_bytes();rejected=[]
    with tempfile.TemporaryDirectory(dir=output) as directory:
        exe=Path(directory)/'BAD.EXE';mp=Path(directory)/'BAD.MAP';mp.write_bytes(listing)
        for symbol,delta in [('terminal_transfer_set_budget',5),('terminal_transfer_set_budget_far',3)]:
            mutated=bytearray(image);mutated[raw_at(image,syms[symbol])+delta]=0x90;exe.write_bytes(mutated)
            try:inspect_terminal_memory(exe,mp)
            except AssertionError:rejected.append(symbol)
            else:raise AssertionError('Invalid new bridge accepted: '+symbol)
    assert all(sha(Path(p))==h for p,h in frozen.items())
    sources={n:sha(ROOT/n) for n in ('standalone/check_transfer_budget_bank.py','standalone/check_modem_far_live.py','standalone/check_connection.py','standalone/check_transport.py','standalone/dos_image.py','standalone/terminal_memory.py','src/terminal/connection.asm','src/terminal/transfer_actions.asm','src/terminal/modem_abi.inc','src/terminal/modem_bridge.asm','src/terminal/far_bridge.inc')}
    result=dict(passed=True,baseline={'path':str(baseline),'binary_sha256':sha(baseline/'TERMINAL.EXE'),'map_sha256':sha(baseline/'terminal.map')},products=products,
        body_bytes=len(body),body_sha256=hashlib.sha256(body).hexdigest(),configurations=len(cases),executions=len(cases)*len(models),cases=cases,
        registers_flags_and_DS_SS_equal=True,new_bridge_mutations_rejected=rejected,sources=sources,
        scope=__doc__+' Exact body bytes plus every register/FLAGS and stack-return comparison over five actual paths. No protocol/physical or complete menu acceptance claim.')
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS:',len(body),'identical body bytes;',len(cases),'configurations;',len(cases)*len(models),'executions; two invalid bridges rejected')
if __name__=='__main__':main()
