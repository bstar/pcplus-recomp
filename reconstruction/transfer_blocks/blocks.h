#ifndef PCPLUS_TRANSFER_BLOCKS_H
#define PCPLUS_TRANSFER_BLOCKS_H
/* Maintained pure nearC DS=SS interfaces; no DOS/UART/clock calls.
 * CRC returns0success/1extent/2length; count0..32768, sourceNULL onlyifcount0.
 * Encode returns0success/1extent/2payloadsize-or-mode/3capacity.128/1024byte
 * full payload, block0..255, crc0checksum/1CRC. Output132/133/1028/1029bytes.
 * Caller owns extents; output committed after staging, overlap is supported.
 * No padding, handshake, retransmission, disk IO or full protocol claim.
 */
unsigned __cdecl transfer_crc16(const unsigned char *source,unsigned count,unsigned *result);
unsigned __cdecl transfer_block_encode(const unsigned char *source,unsigned count,
 unsigned block,unsigned crc,unsigned char *destination,unsigned capacity);
#endif
