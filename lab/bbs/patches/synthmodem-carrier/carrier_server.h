#ifndef PCPLUS_CARRIER_SERVER_H
#define PCPLUS_CARRIER_SERVER_H
#include "carrier_protocol.h"
/* Private to the helper translation unit. No status bytes use the PTY. */
static struct {
    int listener, peer;
    bool enabled, retiring, owns_path;
    long long retire_deadline;
    char path[sizeof(((struct sockaddr_un *)0)->sun_path)];
    dev_t device;
    ino_t inode;
} C = { .listener = -1, .peer = -1 };
static int carrier_start(void);
static int carrier_progress(void);
static void carrier_close(void);
#endif
