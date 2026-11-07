#ifndef LOC_LINE_PORT_PERSIST_H
#define LOC_LINE_PORT_PERSIST_H
#include "../directory/directory_replace.h"
/* Replace only the native ten-byte prefix of an existing exact1264-byte PRM.
 * Caller holds the canonical file claim. Absolute DOS83 target only; derived
 * same-parent PCPSTG.$$$ / PCPBAK.$$$ must not exist. Compare expected prefix,
 * stream every other byte unchanged, check all IO/close before rename, retain
 * recovery files on uncertain close/rollback. Not crash-atomic or externally
 * locked. Attributes/timestamps are not preserved. Result uses the established
 * directory_replace_result ABI and statuses; check installed/recovery flags.
 * Near-cdecl DS=SS. Output disjoint from all bounded inputs, unchanged on
 * argument rejection. Expected/replacement may overlap as read-only inputs. */
unsigned __cdecl line_port_persist(const char *target,const unsigned char *expected,
 const unsigned char *replacement,directory_replace_result *result);
#endif
