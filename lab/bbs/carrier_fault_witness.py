"""Build the existing passive final-exit observer without its optional MSR read."""
import re
import subprocess
from product_inputs import ROOT


def build(binary,out):
    symbols={n:(int(s,16),int(o,16)) for s,o,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',
        (binary.parent/'terminal.map').read_text(),re.M|re.I)}
    fields={'DATA_SEGMENT':('_terminal_phone_log_event_status',0),'EVENT_STATUS_OFFSET':('_terminal_phone_log_event_status',1),
        'ISR_SEGMENT':('uart_receive_interrupt',0),'ISR_OFFSET':('uart_receive_interrupt',1),
        'EPOCH_OFFSET':('_terminal_phone_log_event_epoch',1),'LIFECYCLE_OFFSET':('_phone_log_lifecycle_store',1),
        'QUEUE_SEGMENT':('_phone_log_queue_store',0),'QUEUE_OFFSET':('_phone_log_queue_store',1),
        'CONNECTION_STATE_OFFSET':('connection_state',1),'CONNECTION_STATUS_OFFSET':('connection_status',1),
        'STARTUP_STATUS_OFFSET':('_terminal_phone_log_startup_status',1),'DISK_ATTEMPTS_OFFSET':('_terminal_phone_log_disk_attempts',1),
        'DISK_STATUS_OFFSET':('_terminal_phone_log_disk_status',1),'CONTROL_ACK_OFFSET':('_terminal_phone_log_retry_acks',1)}
    extra=dict(TRANSFER_ACTIVE='terminal_transfer_active',TRANSFER_FAULT='terminal_transfer_fault',TRANSFER_CLEANUP='terminal_transfer_cleanup_status',
        TRANSFER_DIRECTION='terminal_transfer_direction',TRANSFER_RX_DROPPED='uart_rx_dropped',TRANSFER_PENDING='terminal_transfer_pending',
        TRANSFER_DOWNLOAD='_transfer_download_result',TRANSFER_UPLOAD='_upload_source_result',TRANSFER_MSR_PORT='uart_port_msr')
    defines={k:symbols[n][i] for k,(n,i) in fields.items()};defines.update({k:symbols[n][1] for k,n in extra.items()})
    defines.update(TRANSFER_WATCH=1,IRQ_VECTOR=13)
    text=(ROOT/'standalone/phone_log_events_watch.asm').read_text()
    msr=''' mov dx,[es:TRANSFER_MSR_PORT]
 in al,dx
 test al,80h
 jnz .state
 inc word [transfer_watch+2]
'''
    assert text.count(msr)==1
    text=text.replace(msr,' ; Diagnostic reads only memory; no MSR delta-bit consumption.\n')
    text=text.replace(' in al,dx',' mov al,0x80 ; Inactive child probe also performs no hardware read.')
    assert ' in al,dx' not in text
    (out/'WITNESS.ASM').write_text(text)
    subprocess.run(['nasm','-fbin',*[f'-D{k}={v}' for k,v in defines.items()],str(out/'WITNESS.ASM'),'-o',str(out/'WITNESS.COM')],check=True)
    (out/'KEYWAIT.ASM').write_text('bits 16\ncpu 8086\norg 100h\nagain:\nxor ah,ah\nint 16h\ncmp ax,2d00h\njne again\nmov ax,4c00h\nint 21h\n')
    subprocess.run(['nasm','-fbin',str(out/'KEYWAIT.ASM'),'-o',str(out/'KEYWAIT.COM')],check=True)
