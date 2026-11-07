#ifndef LOC_LINE_PORT_FRONT_H
#define LOC_LINE_PORT_FRONT_H
#define LINE_PORT_ACTION 125U
unsigned __far __cdecl line_port_front_event(unsigned,unsigned,unsigned short __far *);
unsigned __far __cdecl line_port_front_cursor(void);
void __far __cdecl line_port_front_poll(void);
unsigned __far __cdecl line_port_front_run(void);
#endif
