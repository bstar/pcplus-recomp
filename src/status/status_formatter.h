#ifndef PCPLUS_STATUS_FORMATTER_H
#define PCPLUS_STATUS_FORMATTER_H
#ifdef STATUS_FORMAT_HOST
#include <stdint.h>
typedef uintptr_t StatusWord;
#define STATUS_FAR
#else
typedef unsigned StatusWord;
#define STATUS_FAR __far
#endif
/* DS=SS; all pointers are validated owned near spans. capacity1..136.
 * Returns bytecount, -1 capacity/overflow/nullstring, -2 malformed or
 * unsupportedformat, -3 insufficientwords. Valid-cap failures clear dst[0].
 * Does not validate arbitrary near pointers or reproduce the full CRT.
 */
int STATUS_FAR status_format(char *,unsigned,const char *,const StatusWord *,unsigned);
#endif
