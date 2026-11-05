#ifndef PCPLUS_GATEWAY_UART_H
#define PCPLUS_GATEWAY_UART_H
/* Retained Gateway IRQ owner. Begin/end: far cdecl, DS=SS=parent DGROUP,
 * IF1/DF0. Caller owns kind9/active1/pending0 and foreground/display/files.
 * Begin0 leaves RX/flow/DCD service live through a DOS child. 4state/ABI,
 * 5overflow,7TXbusy,8unsupported line/FIFO. End restores the original parent
 * ISR and returns observed fault; a failed repair keeps the lease active.
 * The raw EXEC return entry is IF0-only and uses no DOS or BIOS calls. */
unsigned __far __cdecl gateway_uart_begin(void);
unsigned __far __cdecl gateway_uart_end(void);
#pragma aux gateway_uart_begin "gateway_uart_begin";
#pragma aux gateway_uart_end "gateway_uart_end";
#endif
