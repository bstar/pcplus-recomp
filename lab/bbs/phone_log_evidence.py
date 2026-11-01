"""Passive call-log evidence for actual owned BBS workflows."""
import json,re,struct,subprocess,sys
from pathlib import Path
from product_inputs import ROOT,sha
sys.path.insert(0,str(ROOT/'standalone'))
from test_phone_log_events_terminal import inspect_disk_record


def build_observer(binary,output,irq=5,extra=None):
    binary=Path(binary);parent=binary.parent;manifest=json.loads((parent/'manifest.json').read_text())
    assert manifest['experimental_phone_log_controls']
    symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',(parent/'terminal.map').read_text(),re.M|re.I)}
    fields={'DATA_SEGMENT':('_terminal_phone_log_event_status',0),'EVENT_STATUS_OFFSET':('_terminal_phone_log_event_status',1),
        'ISR_SEGMENT':('uart_receive_interrupt',0),'ISR_OFFSET':('uart_receive_interrupt',1),
        'EPOCH_OFFSET':('_terminal_phone_log_event_epoch',1),'LIFECYCLE_OFFSET':('_phone_log_lifecycle_store',1),
        'QUEUE_SEGMENT':('_phone_log_queue_store',0),'QUEUE_OFFSET':('_phone_log_queue_store',1),
        'CONNECTION_STATE_OFFSET':('connection_state',1),'CONNECTION_STATUS_OFFSET':('connection_status',1),
        'STARTUP_STATUS_OFFSET':('_terminal_phone_log_startup_status',1),'DISK_ATTEMPTS_OFFSET':('_terminal_phone_log_disk_attempts',1),
        'DISK_STATUS_OFFSET':('_terminal_phone_log_disk_status',1),'CONTROL_ACK_OFFSET':('_terminal_phone_log_retry_acks',1)}
    defines={key:symbols[name][index] for key,(name,index) in fields.items()};defines['IRQ_VECTOR']=irq+8
    if extra:defines.update(extra)
    subprocess.run(['nasm','-fbin',*[f'-D{k}={v}' for k,v in defines.items()],str(ROOT/'standalone/phone_log_events_watch.asm'),'-o',str(output)],check=True)
    return output


def audit(output):
    output=Path(output);result=json.loads((output/'result.json').read_text())
    assert result['configuration']['phone_log_enabled']
    captured=(output/'PLSTATE.BIN').read_bytes();assert len(captured)==9798
    header=struct.unpack_from('<10H',captured);assert 0<header[2]<=8
    samples=[captured[20+i*722:20+(i+1)*722] for i in range(header[2])];final=samples[-1]
    entry=result['configuration']['directory_entry']
    if entry:
        directory=(output/'TEST.DIR').read_bytes();at=250+(entry-1)*114
        name=directory[at:at+25].split(b'\0',1)[0];number=directory[at+25:at+46].split(b'\0',1)[0]
    else:
        name=b'MODEM';number=result['configuration']['command'].split('/D:',1)[1].split()[0].encode()
    data=(output/'PCPLUS.FON').read_bytes()
    checks,records=inspect_disk_record(final,1,1,name,number,data,max_elapsed=180)
    attempts,status,acks=struct.unpack_from('<3H',final,716)
    checks.update(observer_final=header[0]==0x4c45 and header[3]==1 and header[9]==0,
        actual_parent_segments=header[4]>0 and header[5]!=header[6],
        exact_append_attempts=(attempts,status,acks)==(2,0,0),
        START_saved_online=any(struct.unpack_from('<H',r,18)[0]==1 and struct.unpack_from('<I',r,76)[0]>=1 for r in samples),
        only_owned_log_created=[p.relative_to(output).as_posix() for p in output.rglob('*.FON')]==['PCPLUS.FON'])
    report=dict(passed=all(checks.values()),checks=checks,records=records,observer_header=list(header),
        log_sha256=sha(output/'PCPLUS.FON'),observer_sha256=sha(output/'OBSERVE.COM'),snapshot_sha256=sha(output/'PLSTATE.BIN'),
        scope='Actual owned stock BBS, parent event/file owners and passive 8086 COM3/IRQ5 snapshots. One normal call pair; not physical DCD/SIP or complete logging composition.')
    (output/'phone-log-evidence.json').write_text(json.dumps(report,indent=2)+'\n')
    assert report['passed'],checks
    return report
