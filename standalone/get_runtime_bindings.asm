BITS 16
CPU 8086
SEGMENT _TEXT public class=CODE use16
extern _get_scenario
extern runtime_get_abort_gate
extern _get_unexpected_abort
global aspect_get,aspect_abort_recovered,runtime_alarm_abort_gate,_get_test_abort
; Actual checkpoint runs an authored command body; native GET operand/typed
; owner is covered separately. No synthetic source is an application binary.
aspect_get: jmp _get_scenario
_get_test_abort: jmp runtime_get_abort_gate
runtime_alarm_abort_gate:
aspect_abort_recovered: jmp _get_unexpected_abort
