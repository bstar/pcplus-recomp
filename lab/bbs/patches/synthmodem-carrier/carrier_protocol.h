#ifndef PCPLUS_CARRIER_PROTOCOL_H
#define PCPLUS_CARRIER_PROTOCOL_H
/* Private, versioned SOCK_SEQPACKET control records, never PTY payload. */
#define PC_CARRIER_VERSION 1
#define PC_CARRIER_HELLO 0x10
#define PC_CARRIER_DOWN 0x11
#define PC_CARRIER_ACK 0x80
#endif
