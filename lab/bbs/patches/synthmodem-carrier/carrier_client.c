#define _GNU_SOURCE
#include <errno.h>
#include <poll.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <termios.h>
#include <time.h>
#include <unistd.h>
#include "carrier_protocol.h"
#include "carrier_client.h"

static int carrier_fd = -1;
static long long now_ms(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t) < 0) return -1;
    return (long long)t.tv_sec * 1000 + t.tv_nsec / 1000000;
}
static int ready(short events, long long deadline) {
    for (;;) {
        long long now = now_ms();
        if (now < 0) return -1;
        long long left = deadline - now;
        if (left <= 0) { errno = ETIMEDOUT; return -1; }
        struct pollfd p = { carrier_fd, events, 0 };
        int r = poll(&p, 1, (int)left);
        if (r < 0 && errno == EINTR) continue;
        if (r <= 0) { if (!r) errno = ETIMEDOUT; return -1; }
        if (p.revents & (POLLERR | POLLNVAL)) { errno = EIO; return -1; }
        return 0; /* recv/send diagnoses a peer hangup explicitly. */
    }
}
static int transact(uint8_t type) {
    const uint8_t message[2] = { PC_CARRIER_VERSION, type };
    long long now = now_ms();
    if (now < 0) return -1;
    long long deadline = now + 1500;
    for (;;) {
        now = now_ms();
        if (now < 0) return -1;
        if (now >= deadline) { errno = ETIMEDOUT; return -1; }
        ssize_t n = send(carrier_fd, message, sizeof(message), MSG_NOSIGNAL);
        if (n == 2) break;
        if (n < 0 && errno == EINTR) continue;
        if (n < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
            if (ready(POLLOUT, deadline) == 0) continue;
            return -1;
        }
        if (n >= 0) errno = EIO;
        return -1;
    }
    for (;;) {
        now = now_ms();
        if (now < 0) return -1;
        if (now >= deadline) { errno = ETIMEDOUT; return -1; }
        uint8_t reply[3];
        ssize_t n = recv(carrier_fd, reply, sizeof(reply), 0);
        if (n < 0 && errno == EINTR) continue;
        if (n < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
            if (ready(POLLIN, deadline) == 0) continue;
            return -1;
        }
        if (n == 2 && reply[0] == PC_CARRIER_VERSION && reply[1] == (type | PC_CARRIER_ACK)) return 0;
        errno = n == 0 ? EPIPE : EPROTO;
        return -1;
    }
}
int pcplus_carrier_start(void) {
    if (carrier_fd >= 0) { errno = EALREADY; return -1; }
    const char *path = getenv("SYNTHMODEM_CARRIER_PATH");
    if (!path || !*path) return 0; /* Explicit legacy opt-out. */
    struct sockaddr_un address = { .sun_family = AF_UNIX };
    if (strlen(path) >= sizeof(address.sun_path)) { errno = ENAMETOOLONG; return -1; }
    strcpy(address.sun_path, path);
    long long now = now_ms();
    if (now < 0) return -1;
    long long deadline = now + 5000;
    for (;;) {
        carrier_fd = socket(AF_UNIX, SOCK_SEQPACKET | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
        if (carrier_fd < 0) return -1;
        if (connect(carrier_fd, (struct sockaddr *)&address, sizeof(address)) == 0) break;
        int saved = errno; close(carrier_fd); carrier_fd = -1;
        if (saved != ENOENT && saved != ECONNREFUSED && saved != EAGAIN && saved != EINTR) { errno = saved; return -1; }
        now = now_ms();
        if (now < 0) return -1;
        if (now >= deadline) { errno = ETIMEDOUT; return -1; }
        poll(NULL, 0, 10);
    }
    struct ucred peer;
    socklen_t size = sizeof(peer);
    if (getsockopt(carrier_fd, SOL_SOCKET, SO_PEERCRED, &peer, &size) < 0 ||
        size != sizeof(peer) || peer.uid != geteuid()) {
        close(carrier_fd); carrier_fd = -1; errno = EACCES; return -1;
    }
    if (transact(PC_CARRIER_HELLO) < 0) { int saved = errno; close(carrier_fd); carrier_fd = -1; errno = saved; return -1; }
    return 0;
}
int pcplus_carrier_down(int pty_fd) {
    if (carrier_fd < 0) return 0;
    if (transact(PC_CARRIER_DOWN) < 0) return -1;
    /* The helper has stopped accepting this session's DATA_TX. Retire bytes
       already admitted to the PTY before the modem enters command mode. */
    if (pty_fd >= 0 && tcflush(pty_fd, TCIFLUSH) < 0 && errno != EIO) return -1;
    return 0;
}
