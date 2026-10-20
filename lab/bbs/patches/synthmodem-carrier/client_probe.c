#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <unistd.h>
#include "carrier_client.h"

/* Test driver only: the production entry points are linked unmodified. */
int main(int argc, char **argv) {
    if (argc != 3) return 64;
    int pty = atoi(argv[1]), enabled = atoi(argv[2]);
    setvbuf(stdout, NULL, _IONBF, 0);
    if (pcplus_carrier_start() < 0) {
        printf("START_ERROR %d\n", errno); return 20;
    }
    if (enabled) {
        int sockets = 0;
        for (int fd = 3; fd < 256; fd++) {
            int type; socklen_t size = sizeof(type);
            if (getsockopt(fd, SOL_SOCKET, SO_TYPE, &type, &size) == 0 &&
                type == SOCK_SEQPACKET) {
                if (!(fcntl(fd, F_GETFD) & FD_CLOEXEC)) return 21;
                sockets++;
            }
        }
        if (sockets != 1) return 22;
        if (pcplus_carrier_start() != -1 || errno != EALREADY) return 23;
    }
    puts("READY");
    char trigger;
    if (read(STDIN_FILENO, &trigger, 1) != 1) return 24;
    if (pcplus_carrier_down(pty) < 0) {
        printf("DOWN_ERROR %d\n", errno); return 25;
    }
    puts("DOWN");
    return 0;
}
