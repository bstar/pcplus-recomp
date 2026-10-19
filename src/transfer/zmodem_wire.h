#ifndef PCPLUS_ZMODEM_WIRE_H
#define PCPLUS_ZMODEM_WIRE_H
/* Maintained Forsberg ZMODEM framing, not a transfer/file owner. Near cdecl,
 * DS=SS. No allocation, globals, UART, filesystem or original binary inputs.
 * Caller retains state and a disjoint 1..1024-byte tentative payload buffer.
 * Buffer contents become acceptable ONLY on ZW_DATA; all other events forbid
 * committing them. On error caller recovers from its last committed offset.
 */
#ifdef __WATCOMC__
typedef unsigned long zw_u32;
#else
#include <stdint.h>
typedef uint32_t zw_u32;
#ifndef __cdecl
#define __cdecl
#endif
#endif
enum { ZW_MORE=0, ZW_HEADER, ZW_DATA, ZW_CRC, ZW_FORMAT, ZW_OVERFLOW,
 ZW_CANCEL, ZW_ARGUMENT };
enum { ZW_BIN16=65, ZW_HEX=66, ZW_BIN32=67 };
enum { ZW_CRCE=104, ZW_CRCG=105, ZW_CRCQ=106, ZW_CRCW=107 };
typedef struct zw_decoder {
 unsigned char *buffer;
 unsigned capacity,count,phase,index,escape,cans,control,overflow,nibble;
 unsigned format,ending;
 unsigned char header[5];
 zw_u32 crc,received;
} zw_decoder;
unsigned __cdecl zw_init(zw_decoder *,unsigned char *,unsigned capacity,
 unsigned escape_controls);
/* Search headers again, preserving cancellation count and negotiation. */
void __cdecl zw_headers(zw_decoder *);
/* Begin data using the last accepted header's CRC width. Following CRCE/CRCW,
 * feed searches headers; following CRCG/CRCQ it starts another data subpacket.
 * A DATA event retains count/ending until the next feed or explicit reset. */
unsigned __cdecl zw_data(zw_decoder *);
unsigned __cdecl zw_feed(zw_decoder *,unsigned byte_value);
/* Return encoded length, or zero without writing anything on invalid args or
 * insufficient space. Output spans must not overlap input spans. Max output:
 * 24 bytes/header, 2059 bytes/1024-byte data packet with all quoting enabled.
 * Hex headers end CR LF and optional XON (omitted for ZACK=3 and ZFIN=8).
 * Binary/data quoting always protects IAC with ZRUB1 for Telnet peers. */
unsigned __cdecl zw_header_encode(unsigned format,const unsigned char *header,
 unsigned escape_controls,unsigned char *out,unsigned capacity);
unsigned __cdecl zw_data_encode(unsigned format,const unsigned char *data,
 unsigned length,unsigned ending,unsigned escape_controls,
 unsigned char *out,unsigned capacity);
#endif
