/* SPDX-License-Identifier: GPL-2.0-or-later */
#ifndef LOC_SEXYZ_RECEIVE_FINISH_H
#define LOC_SEXYZ_RECEIVE_FINISH_H
/* Call only after recv_init has accepted the sender's ZFIN and sent its reply.
 * Retain exclusive protocol ownership until OO or a bounded honest failure.
 * Uses the existing configured receive timeout, clamped to1..60 seconds. */
BOOL loc_receive_finish(zmodem_t* zm);
#endif
