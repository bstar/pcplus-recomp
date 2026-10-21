/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "genwrap.h"
#include "dirwrap.h"
#include "zmodem.h"
#include "zmodem_wire.h"
#include "receive_finish.h"

BOOL loc_receive_finish(zmodem_t* zm)
{
    zw_decoder decoder;
    unsigned char unused;
    unsigned count,headers=0,first_o=0,limit;
    uint64_t start,now;
    int c;
    unsigned result;
    if (!zm || !zm->recv_byte) return FALSE;
    limit=zm->recv_timeout;
    if (!limit) limit=1;
    if (limit>60) limit=60;
    start=xp_timer64();
    if (start==UINT64_MAX || zw_init(&decoder,&unused,1,0)!=ZW_MORE) return FALSE;
    for (count=0;count<512;) {
        if (zm->local_abort || zm->cancelled ||
            (zm->is_cancelled && zm->is_cancelled(zm->cbdata))) {
            zm->cancelled=TRUE;
            return FALSE;
        }
        if (zm->is_connected && !zm->is_connected(zm->cbdata)) return FALSE;
        now=xp_timer64();
        if (now==UINT64_MAX || now<start || now-start>=(uint64_t)limit*1000) return FALSE;
        /* One-second polls keep disconnect/cancel serviced. Neither input nor
         * a valid stale header refreshes this total monotonic deadline. */
        c=zm->recv_byte(zm->cbdata,1);
        now=xp_timer64();
        if (now==UINT64_MAX || now<start || now-start>=(uint64_t)limit*1000) return FALSE;
        if (zm->local_abort || zm->cancelled ||
            (zm->is_cancelled && zm->is_cancelled(zm->cbdata))) {
            zm->cancelled=TRUE;
            return FALSE;
        }
        if (zm->is_connected && !zm->is_connected(zm->cbdata)) return FALSE;
        if (c<0) continue;
        if (c>255) return FALSE;
        ++count;
        if ((c&127)==17 || (c&127)==19) continue;
        if (first_o) return c=='O';
        if (!decoder.phase) {
            if (c=='O') { first_o=1; continue; }
            if (c!=42 && c!=24 && c!=13 && c!=10) return FALSE;
        }
        result=zw_feed(&decoder,(unsigned)c);
        if (result==ZW_CANCEL) { zm->cancelled=TRUE; return FALSE; }
        if (result==ZW_HEADER) {
            if ((decoder.header[0]!=ZFIN && decoder.header[0]!=ZABORT) ||
                decoder.header[1] || decoder.header[2] || decoder.header[3] || decoder.header[4] ||
                ++headers>=10) return FALSE;
            /* Queued valid closing retries can precede OO on a slow link.
             * The initial reply is already in flight: do not queue more
             * replies that could reach the sender after it returns to UI. */
        } else if (result!=ZW_MORE) return FALSE;
    }
    return FALSE;
}
