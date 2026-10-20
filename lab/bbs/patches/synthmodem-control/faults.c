/* Compile the actual upstream/candidate translation unit; only read/write are
 * transport models. SPDX-License-Identifier: GPL-2.0-or-later */
#define main control_program_main
#define write modeled_write
#define read modeled_read
#include "modemd-ctrl.c"
#undef main
#undef write
#undef read

static unsigned char input[8192], output[131072];
static size_t input_len, output_len, write_limit;
static int inject_errno, zero_write, fail_after;
ssize_t modeled_read(int fd, void *buf, size_t len) {
    (void)fd;
    if (len > input_len) len = input_len;
    memcpy(buf, input, len); memmove(input, input + len, input_len - len);
    input_len -= len;
    return (ssize_t)len;
}
ssize_t modeled_write(int fd, const void *buf, size_t len) {
    (void)fd;
    if (fail_after == 0) { fail_after = -1; errno = EAGAIN; return -1; }
    if (fail_after > 0) fail_after--;
    if (inject_errno) { errno = inject_errno; inject_errno = 0; return -1; }
    if (zero_write) return 0;
    if (len > write_limit) len = write_limit;
    if (output_len + len > sizeof(output)) abort();
    memcpy(output + output_len, buf, len); output_len += len;
    return (ssize_t)len;
}
static void reset(void) {
    memset(&S, 0, sizeof(S)); S.pty_fd = 51; S.host_control_fd = 50;
    input_len = output_len = 0; write_limit = sizeof(output);
    inject_errno = zero_write = 0; fail_after = -1;
}
static void frame(unsigned char type, const void *data, size_t len) {
    wire_encode_header(input + input_len, type, (uint16_t)len);
    memcpy(input + input_len + WIRE_HEADER_SIZE, data, len);
    input_len += len + WIRE_HEADER_SIZE;
}
static int parser_defect(void) {
    reset(); frame(WIRE_TYPE_AT, "FIRST", 5); frame(WIRE_TYPE_AT, "SECOND", 6);
    unsigned char type, *payload; size_t len, total = input_len;
    if (wire_try_parse(input, &total, &type, &payload, &len) != 1) return 1;
    return type != WIRE_TYPE_AT || len != 5 || memcmp(payload, "FIRST", 5);
}
static int short_write_defect(void) {
    reset(); S.data_mode = true; write_limit = 2;
    frame(WIRE_TYPE_DATA_TX, "ABCDEFG", 7);
    if (handle_host_control_readable() < 0) return 1;
#ifdef FIXED
    while (pty_busy()) if (flush_pty() < 0) return 1;
#endif
    return output_len != 7 || memcmp(output, "ABCDEFG", 7);
}
int main(void) {
#ifndef FIXED
    int parser = parser_defect(), short_write = short_write_defect();
    reset(); write_limit = 1; fail_after = 1;
    int reverse = wire_write(S.host_control_fd, WIRE_TYPE_DATA_RX, "DATA", 4) < 0 && output_len == 1;
    printf("{\"stock_parser_corruption\":%s,\"stock_short_write_loss\":%s,\"stock_reverse_frame_truncated\":%s}\n",
           parser ? "true" : "false", short_write ? "true" : "false", reverse ? "true" : "false");
    return !(parser && short_write && reverse);
#else
    if (parser_defect() || short_write_defect()) return 1;
    unsigned checks = 2;
    for (int error = 0; error < 3; error++) {
        reset(); frame(WIRE_TYPE_AT, "INIT", 4);
        if (handle_host_control_readable() < 0) return 2;
        inject_errno = error == 0 ? EINTR : error == 1 ? EAGAIN : EWOULDBLOCK;
        if (flush_pty() < 0 || output_len || !pty_busy()) return 3;
        write_limit = 1;
        while (pty_busy()) if (flush_pty() < 0) return 4;
        if (output_len != 5 || memcmp(output, "INIT\r", 5)) return 5;
        checks++;
    }
    reset(); frame(WIRE_TYPE_AT, "ONE", 3); frame(WIRE_TYPE_AT, "TWO", 3);
    if (handle_host_control_readable() < 0) return 6;
    write_limit = 1;
    for (unsigned i = 0; i < 20; i++) {
        if (flush_pty() < 0 || dispatch_host_frames() < 0) return 7;
    }
    if (output_len != 8 || memcmp(output, "ONE\rTWO\r", 8)) return 8;
    checks++;
    for (int error = 0; error < 2; error++) {
        reset(); S.data_mode = true; frame(WIRE_TYPE_DATA_TX, "XYZ", 3);
        if (handle_host_control_readable() < 0) return 9;
        if (error) inject_errno = EIO; else zero_write = 1;
        if (flush_pty() >= 0 || !pty_busy() || output_len) return 10;
        checks++;
    }
    reset(); S.data_mode = true; frame(WIRE_TYPE_DATA_TX, "QUEUED", 6);
    if (handle_host_control_readable() < 0) return 11;
    memcpy(input, "\r\nNO CARRIER\r\n", 14); input_len = 14;
    /* Host output records the real status/AT response. No queued bytes may
     * survive into a newly entered command-mode session. */
    if (handle_pty_readable() < 0 || S.data_mode || pty_busy()) return 12;
    checks++;
    for (int error = 0; error < 3; error++) {
        reset();
        if (wire_write(S.host_control_fd, WIRE_TYPE_DATA_RX, "ABCDEFG", 7) < 0) return 13;
        write_limit = 1;
        if (flush_host() < 0 || output_len != 1) return 14;
        inject_errno = error == 0 ? EINTR : error == 1 ? EAGAIN : EWOULDBLOCK;
        if (flush_host() < 0 || output_len != 1 || !host_busy()) return 15;
        if (wire_write(S.host_control_fd, WIRE_TYPE_DATA_RX, "HI", 2) < 0) return 16;
        while (host_busy()) if (flush_host() < 0) return 17;
        static const unsigned char want[] = {8,0,0x15,'A','B','C','D','E','F','G',3,0,0x15,'H','I'};
        if (output_len != sizeof(want) || memcmp(output, want, sizeof(want))) return 18;
        checks++;
    }
    for (int error = 0; error < 2; error++) {
        reset();
        if (wire_write(S.host_control_fd, WIRE_TYPE_DATA_RX, "XYZ", 3) < 0) return 19;
        if (error) inject_errno = EPIPE; else zero_write = 1;
        if (flush_host() >= 0 || !S.host_tx_failed || !host_busy()) return 20;
        checks++;
    }
    reset();
    unsigned char maximum[WIRE_MAX_PAYLOAD] = {0};
    for (unsigned i = 0; i < 16; i++)
        if (wire_write(S.host_control_fd, WIRE_TYPE_DATA_RX, maximum, sizeof(maximum)) < 0) return 21;
    size_t full = S.host_tx_len;
    if (wire_write(S.host_control_fd, WIRE_TYPE_DATA_RX, "X", 1) >= 0 ||
        !S.host_tx_failed || S.host_tx_len != full || output_len) return 22;
    checks++;
    reset();
    for (unsigned i = 0; i < 16; i++)
        if (wire_write(S.host_control_fd, WIRE_TYPE_DATA_RX, maximum, sizeof(maximum)) < 0) return 23;
    unsigned char original[65536]; memcpy(original, S.host_tx, sizeof(original));
    write_limit = 4096;
    if (flush_host() < 0 || output_len != 4096) return 24;
    if (wire_write(S.host_control_fd, WIRE_TYPE_DATA_RX, "TAIL", 4) < 0 || S.host_tx_at) return 25;
    while (host_busy()) if (flush_host() < 0) return 26;
    static const unsigned char tail[] = {5,0,0x15,'T','A','I','L'};
    if (output_len != sizeof(original) + sizeof(tail) || memcmp(output, original, sizeof(original)) ||
        memcmp(output + sizeof(original), tail, sizeof(tail))) return 27;
    checks++;
    printf("{\"passed\":true,\"fault_cases\":%u}\n", checks);
    return 0;
#endif
}
