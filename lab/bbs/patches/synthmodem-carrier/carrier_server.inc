/* SPDX-License-Identifier: GPL-2.0-or-later
 * Included after the helper's wire/queue routines. */
static void carrier_close(void) {
    if (C.peer >= 0) { close(C.peer); C.peer = -1; }
    if (C.listener >= 0) { close(C.listener); C.listener = -1; }
    if (C.owns_path) {
        struct stat st;
        if (lstat(C.path, &st) == 0 && S_ISSOCK(st.st_mode) &&
            st.st_dev == C.device && st.st_ino == C.inode) unlink(C.path);
        C.owns_path = false;
    }
}

static int carrier_wait(int fd, short events, long long deadline) {
    while (!g_quit) {
        long long left = deadline - monotonic_ms();
        if (left <= 0) { errno = ETIMEDOUT; return -1; }
        struct pollfd p = { fd, events, 0 };
        int result = poll(&p, 1, (int)left);
        if (result < 0 && errno == EINTR) continue;
        if (result <= 0) { if (!result) errno = ETIMEDOUT; return -1; }
        if (p.revents & (POLLERR | POLLNVAL)) { errno = EIO; return -1; }
        return 0;
    }
    errno = EINTR;
    return -1;
}

static int carrier_ack(uint8_t type) {
    uint8_t record[2] = { PC_CARRIER_VERSION, type | PC_CARRIER_ACK };
    long long deadline = monotonic_ms() + 1500;
    while (!g_quit && monotonic_ms() < deadline) {
        ssize_t n = send(C.peer, record, sizeof(record), MSG_NOSIGNAL);
        if (n == sizeof(record)) return 0;
        if (n < 0 && errno == EINTR) continue;
        if (n < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
            if (carrier_wait(C.peer, POLLOUT, deadline) == 0) continue;
            return -1;
        }
        if (n >= 0) errno = EIO;
        return -1;
    }
    errno = g_quit ? EINTR : ETIMEDOUT;
    return -1;
}

static int carrier_start(void) {
    const char *path = getenv("SYNTHMODEM_CARRIER_PATH");
    if (!path || !*path) return 0;
    if (strlen(path) >= sizeof(C.path)) { errno = ENAMETOOLONG; return -1; }
    strcpy(C.path, path);
    struct sockaddr_un address = { .sun_family = AF_UNIX };
    strcpy(address.sun_path, path);
    C.listener = socket(AF_UNIX, SOCK_SEQPACKET | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
    if (C.listener < 0) return -1;
    mode_t mask = umask(0077);
    int result = bind(C.listener, (struct sockaddr *)&address, sizeof(address));
    int saved = errno;
    umask(mask);
    errno = saved;
    if (result < 0) return -1; /* Never remove an existing path. */
    struct stat st;
    if (lstat(path, &st) < 0) return -1;
    C.device = st.st_dev; C.inode = st.st_ino; C.owns_path = true;
    if (listen(C.listener, 1) < 0) return -1;
    long long deadline = monotonic_ms() + 5000;
    for (;;) {
        C.peer = accept4(C.listener, NULL, NULL, SOCK_NONBLOCK | SOCK_CLOEXEC);
        if (C.peer >= 0) break;
        if (errno == EINTR) { if (g_quit) return -1; continue; }
        if (errno != EAGAIN && errno != EWOULDBLOCK) return -1;
        if (carrier_wait(C.listener, POLLIN, deadline) < 0) return -1;
    }
    struct ucred peer;
    socklen_t size = sizeof(peer);
    if (getsockopt(C.peer, SOL_SOCKET, SO_PEERCRED, &peer, &size) < 0 ||
        size != sizeof(peer) || peer.uid != geteuid()) { errno = EACCES; return -1; }
    deadline = monotonic_ms() + 1500;
    for (;;) {
        uint8_t record[3];
        ssize_t n = recv(C.peer, record, sizeof(record), 0);
        if (n == 2 && record[0] == PC_CARRIER_VERSION && record[1] == PC_CARRIER_HELLO) break;
        if (n < 0 && errno == EINTR) { if (g_quit) return -1; continue; }
        if (n < 0 && (errno == EAGAIN || errno == EWOULDBLOCK)) {
            if (carrier_wait(C.peer, POLLIN, deadline) == 0) continue;
            return -1;
        }
        errno = n == 0 ? EPIPE : EPROTO;
        return -1;
    }
    if (carrier_ack(PC_CARRIER_HELLO) < 0) return -1;
    close(C.listener); C.listener = -1;
    C.enabled = true;
    return 0;
}

/* Must run before dispatch, reads or writes on every loop/poll return. The
 * modem waits for ACK before changing mode, so no result text can race into
 * the online data parser. One VM/helper belongs to one physical call. */
static int carrier_progress(void) {
    if (!C.enabled || C.retiring) return 0;
    uint8_t record[3];
    ssize_t n = recv(C.peer, record, sizeof(record), 0);
    if (n < 0 && (errno == EAGAIN || errno == EWOULDBLOCK || errno == EINTR)) return 0;
    if (n != 2 || record[0] != PC_CARRIER_VERSION || record[1] != PC_CARRIER_DOWN) {
        errno = n == 0 ? EPIPE : EPROTO;
        LOGE("Carrier status channel failed: %s", strerror(errno));
        return -1;
    }
    C.retiring = true;
    C.retire_deadline = monotonic_ms() + 1000;
    S.data_mode = false;
    S.pty_tx_at = S.pty_tx_len = 0;
    S.ctrl_rx_len = 0;
    S.pending_len = 0;
    S.data_pending_deadline = 0;
    S.hangup_phase = 0;
    static const char status[] = "{\"event\":\"nocarrier\"}";
    if (wire_write(S.host_control_fd, WIRE_TYPE_MODEM_STATUS, status, sizeof(status) - 1) < 0) return -1;
    return carrier_ack(PC_CARRIER_DOWN);
}
