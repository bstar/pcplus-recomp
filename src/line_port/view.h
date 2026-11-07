#ifndef LOC_LINE_PORT_VIEW_H
#define LOC_LINE_PORT_VIEW_H
/* Native selector indices, deliberately separate from maintained UART values. */
typedef struct line_port_values {
 unsigned port,baud,parity,stop,bits;
} line_port_values;
/* Draw only the native popup footprint and its bottom title in an 80x25 view.
 * Returns 1 on invalid inputs, without writing the frame. No file/UART effects.
 * Caller owns saved-screen restoration and cursor (native row18,column67). */
unsigned __far __cdecl line_port_view(const line_port_values *values,
                                     unsigned __far *frame,unsigned cells);
#endif
