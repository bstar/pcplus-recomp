; Link after all phone-log C objects.
BITS 16
CPU 8086
SEGMENT PHONE_LOG_CODE public align=1 class=FARCODE use16
GROUP PHONE_LOG_GROUP PHONE_LOG_CODE
global terminal_phone_log_code_end
terminal_phone_log_code_end:
