#!/usr/bin/env python3
"""Preserve backend QEMU arguments and add one loopback diagnostic chardev."""
import os,sys
port=int(os.environ['PCPLUS_TRACE_PORT']);assert 1024<=port<=65535
os.execvp('qemu-system-i386',['qemu-system-i386',*sys.argv[1:],
 '-chardev',f'socket,id=trace,host=127.0.0.1,port={port},server=off,nodelay=on',
 '-device','virtserialport,bus=virtio-serial0.0,nr=3,chardev=trace,name=pcplus.trace'])
