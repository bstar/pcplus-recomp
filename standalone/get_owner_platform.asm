BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern aspect_abort_recovered
global runtime_alarm_abort_gate
runtime_alarm_abort_gate: jmp aspect_abort_recovered
