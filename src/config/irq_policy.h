#ifndef PCPLUS_IRQ_POLICY_H
#define PCPLUS_IRQ_POLICY_H
/* Maintained exclusive master-PIC UART policy, not an original PRM default. */
#define PCPLUS_MASTER_IRQ_VALID(n) ((n)==3U || (n)==4U || (n)==5U || (n)==7U)
#endif
