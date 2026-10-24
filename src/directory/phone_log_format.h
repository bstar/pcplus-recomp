#ifndef PCPLUS_PHONE_LOG_FORMAT_H
#define PCPLUS_PHONE_LOG_FORMAT_H
#define PHONE_LOG_TEXT_CAPACITY 132U
#define PHONE_LOG_ENABLE_OFFSET 0x1e6U
enum { PLT_OK=0,PLT_ARGUMENT,PLT_CLOCK };
typedef struct phone_log_stamp {
 unsigned year,month,day,hour,minute,second;
} phone_log_stamp;
/* Native text layout; maintained bounded formatting and year modulo100.
 * Explicit CRLF. No FILE, printf, floating point, locale or password input.
 * Names/numbers <=63 CP437 bytes; controls/DEL rejected. Name uses22 columns
 * and truncation; number is right-aligned to at least20 columns. */
extern const char phone_log_heading[];
extern const unsigned phone_log_heading_count;
unsigned __cdecl phone_log_stamp_seconds(const phone_log_stamp *,unsigned long *);
/* Read date/time/date, retry at most three times across a date transition.
 * Reject malformed calendar fields; publish the full stamp atomically. */
unsigned __cdecl phone_log_read_stamp(phone_log_stamp *);
/* Output is NUL-terminated; count excludes NUL. Atomic rejection, capacity<=132,
 * nonwrapping near buffers, output/count disjoint from inputs and each other.
 * Input strings may overlap each other; start/end timestamps may be identical. */
unsigned __cdecl phone_log_format_start(const char *,const char *,const phone_log_stamp *,
 char *,unsigned,unsigned *);
unsigned __cdecl phone_log_format_end(const phone_log_stamp *,const phone_log_stamp *,
 char *,unsigned,unsigned *);
/* Exact1264-byte proved memory image: DS1d6a - DS1b84 = file01e6.
 * Any nonzero WORD enables. Never reads/writes other settings or changes input.
 * Returned flag is committed only after span/disjoint validation. */
unsigned __cdecl phone_log_decode_enabled(const unsigned char *,unsigned,unsigned *);
#endif
