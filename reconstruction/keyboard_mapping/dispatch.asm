; Recovered PCPlus 2.01 terminal keyboard mapping instructions; see docs/KEYBOARD_MAPPING.md.
BITS 16
CPU 8086
%ifdef KEYBOARD_MAPPING_OMF
SEGMENT _TEXT public class=CODE use16
global keyboard_mapping_dispatch,keyboard_mapping_shift_tab
extern keyboard_mapping_emit
extern keyboard_mapping_echo
extern keyboard_service_ab0b
extern keyboard_service_0bc0
extern keyboard_service_1e30
extern keyboard_service_1ea0
extern keyboard_service_1efc
extern keyboard_service_1e0c
extern keyboard_service_64fe
extern keyboard_service_40c1
extern keyboard_service_0ca2
extern keyboard_service_4b14
extern keyboard_service_427f
extern keyboard_service_82b6
extern keyboard_service_6bbe
extern keyboard_service_353d
extern keyboard_service_433d
extern keyboard_service_4870
extern keyboard_service_0cd2
extern keyboard_service_0e06
extern keyboard_service_1bbe
extern keyboard_service_6e5a
extern keyboard_service_baab
extern keyboard_service_6dca
extern keyboard_service_47b6
extern keyboard_service_ba03
extern keyboard_service_b9f7
extern keyboard_service_0cb4
extern keyboard_service_b9d3
extern keyboard_service_20a4
extern keyboard_service_3a25
extern keyboard_service_0610
extern keyboard_service_badb
extern keyboard_service_bab7
extern keyboard_service_ba93
extern keyboard_service_1aaa
extern keyboard_service_46ba
extern keyboard_service_2eaa
extern keyboard_service_2f78
extern keyboard_service_2fb8
extern terminal_keymap
extern keyboard_dispatch_table
extern keyboard_mapping_key
extern keyboard_mapping_scrollback_mode
extern keyboard_mapping_hook_enabled
extern keyboard_mapping_hook_character
extern keyboard_state_1d1a
extern keyboard_state_33cc
extern keyboard_state_36f0
extern keyboard_state_36fc
extern keyboard_state_36d8
extern keyboard_state_36e4
extern keyboard_state_900c
extern keyboard_state_34b0
extern keyboard_state_34bc
extern keyboard_state_35b8
extern keyboard_state_35c4
extern keyboard_state_36c0
extern keyboard_state_36cc
extern keyboard_state_4b02
extern keyboard_state_4afe
extern keyboard_state_4210
extern keyboard_state_1d18
extern keyboard_state_3414
extern keyboard_state_3420
extern keyboard_state_3408
extern keyboard_state_33fc
extern keyboard_state_3708
extern keyboard_state_3714
extern keyboard_state_3756
extern keyboard_state_33e4
extern keyboard_state_360c
extern keyboard_state_33d8
extern keyboard_state_3600
extern keyboard_state_3976
extern keyboard_state_33f0
extern keyboard_state_373c
extern keyboard_state_35f4
extern keyboard_state_35e8
extern keyboard_state_35dc
extern keyboard_state_35d0
extern keyboard_state_3720
extern keyboard_state_33c0
extern keyboard_state_342c
extern keyboard_state_3630
extern keyboard_state_363c
extern keyboard_state_33b4
extern keyboard_state_3390
extern keyboard_state_3384
extern keyboard_state_339c
extern keyboard_state_33a8
extern keyboard_state_34c8
extern keyboard_state_34d4
extern keyboard_state_34e0
extern keyboard_state_34ec
extern keyboard_state_34f8
extern keyboard_state_3504
extern keyboard_state_3510
extern keyboard_state_351c
extern keyboard_state_3528
extern keyboard_state_3534
extern keyboard_state_3618
extern keyboard_state_3624
extern keyboard_state_1d4e
extern keyboard_state_cee6
extern keyboard_state_2070
extern keyboard_state_3252
extern keyboard_state_cffb
extern keyboard_state_333e
extern keyboard_state_3150
extern keyboard_state_3174
extern keyboard_state_31e0
extern keyboard_state_3758
extern keyboard_state_3262
extern keyboard_state_4675
extern keyboard_state_ce6a
extern keyboard_state_467b
global keyboard_original_138a
global keyboard_original_139c
global keyboard_original_13ae
global keyboard_original_13c0
global keyboard_original_13d2
global keyboard_original_13e4
global keyboard_original_1404
global keyboard_original_140e
global keyboard_original_1418
global keyboard_original_1422
global keyboard_original_142c
global keyboard_original_1436
global keyboard_original_1440
global keyboard_original_145a
global keyboard_original_14a8
global keyboard_original_14c2
global keyboard_original_14dc
global keyboard_original_14f6
global keyboard_original_1512
global keyboard_original_151a
global keyboard_original_1524
global keyboard_original_153a
global keyboard_original_1542
global keyboard_original_154c
global keyboard_original_1564
global keyboard_original_157c
global keyboard_original_1594
global keyboard_original_15b6
global keyboard_original_15d6
%define short
%else
ORG 0x138a
%define keyboard_mapping_emit 0xa62
%define keyboard_mapping_echo 0xe4e
%define keyboard_service_ab0b 0xab0b
%define keyboard_service_0bc0 0xbc0
%define keyboard_service_1e30 0x1e30
%define keyboard_service_1ea0 0x1ea0
%define keyboard_service_1efc 0x1efc
%define keyboard_service_1e0c 0x1e0c
%define keyboard_service_64fe 0x64fe
%define keyboard_service_40c1 0x40c1
%define keyboard_service_0ca2 0xca2
%define keyboard_service_4b14 0x4b14
%define keyboard_service_427f 0x427f
%define keyboard_service_82b6 0x82b6
%define keyboard_service_6bbe 0x6bbe
%define keyboard_service_353d 0x353d
%define keyboard_service_433d 0x433d
%define keyboard_service_4870 0x4870
%define keyboard_service_0cd2 0xcd2
%define keyboard_service_0e06 0xe06
%define keyboard_service_1bbe 0x1bbe
%define keyboard_service_6e5a 0x6e5a
%define keyboard_service_baab 0xbaab
%define keyboard_service_6dca 0x6dca
%define keyboard_service_47b6 0x47b6
%define keyboard_service_ba03 0xba03
%define keyboard_service_b9f7 0xb9f7
%define keyboard_service_0cb4 0xcb4
%define keyboard_service_b9d3 0xb9d3
%define keyboard_service_20a4 0x20a4
%define keyboard_service_3a25 0x3a25
%define keyboard_service_0610 0x610
%define keyboard_service_badb 0xbadb
%define keyboard_service_bab7 0xbab7
%define keyboard_service_ba93 0xba93
%define keyboard_service_1aaa 0x1aaa
%define keyboard_service_46ba 0x46ba
%define keyboard_service_2eaa 0x2eaa
%define keyboard_service_2f78 0x2f78
%define keyboard_service_2fb8 0x2fb8
%define terminal_keymap 0x3378
%define keyboard_dispatch_table 0x44e0
%define keyboard_mapping_key 0xcffa
%define keyboard_mapping_scrollback_mode 0x1d74
%define keyboard_mapping_hook_enabled 0x1d6e
%define keyboard_mapping_hook_character 0x1d70
%define keyboard_state_1d1a 0x1d1a
%define keyboard_state_33cc 0x33cc
%define keyboard_state_36f0 0x36f0
%define keyboard_state_36fc 0x36fc
%define keyboard_state_36d8 0x36d8
%define keyboard_state_36e4 0x36e4
%define keyboard_state_900c 0x900c
%define keyboard_state_34b0 0x34b0
%define keyboard_state_34bc 0x34bc
%define keyboard_state_35b8 0x35b8
%define keyboard_state_35c4 0x35c4
%define keyboard_state_36c0 0x36c0
%define keyboard_state_36cc 0x36cc
%define keyboard_state_4b02 0x4b02
%define keyboard_state_4afe 0x4afe
%define keyboard_state_4210 0x4210
%define keyboard_state_1d18 0x1d18
%define keyboard_state_3414 0x3414
%define keyboard_state_3420 0x3420
%define keyboard_state_3408 0x3408
%define keyboard_state_33fc 0x33fc
%define keyboard_state_3708 0x3708
%define keyboard_state_3714 0x3714
%define keyboard_state_3756 0x3756
%define keyboard_state_33e4 0x33e4
%define keyboard_state_360c 0x360c
%define keyboard_state_33d8 0x33d8
%define keyboard_state_3600 0x3600
%define keyboard_state_3976 0x3976
%define keyboard_state_33f0 0x33f0
%define keyboard_state_373c 0x373c
%define keyboard_state_35f4 0x35f4
%define keyboard_state_35e8 0x35e8
%define keyboard_state_35dc 0x35dc
%define keyboard_state_35d0 0x35d0
%define keyboard_state_3720 0x3720
%define keyboard_state_33c0 0x33c0
%define keyboard_state_342c 0x342c
%define keyboard_state_3630 0x3630
%define keyboard_state_363c 0x363c
%define keyboard_state_33b4 0x33b4
%define keyboard_state_3390 0x3390
%define keyboard_state_3384 0x3384
%define keyboard_state_339c 0x339c
%define keyboard_state_33a8 0x33a8
%define keyboard_state_34c8 0x34c8
%define keyboard_state_34d4 0x34d4
%define keyboard_state_34e0 0x34e0
%define keyboard_state_34ec 0x34ec
%define keyboard_state_34f8 0x34f8
%define keyboard_state_3504 0x3504
%define keyboard_state_3510 0x3510
%define keyboard_state_351c 0x351c
%define keyboard_state_3528 0x3528
%define keyboard_state_3534 0x3534
%define keyboard_state_3618 0x3618
%define keyboard_state_3624 0x3624
%define keyboard_state_1d4e 0x1d4e
%define keyboard_state_cee6 0xcee6
%define keyboard_state_2070 0x2070
%define keyboard_state_3252 0x3252
%define keyboard_state_cffb 0xcffb
%define keyboard_state_333e 0x333e
%define keyboard_state_3150 0x3150
%define keyboard_state_3174 0x3174
%define keyboard_state_31e0 0x31e0
%define keyboard_state_3758 0x3758
%define keyboard_state_3262 0x3262
%define keyboard_state_4675 0x4675
%define keyboard_state_ce6a 0xce6a
%define keyboard_state_467b 0x467b
%endif
%include "encodings.inc"
keyboard_mapping_shift_tab:
keyboard_original_138a:
L_138a: lea bx,[keyboard_state_33cc]
L_138e: call keyboard_mapping_emit
L_1391: cmp word [keyboard_state_1d1a],0x0
L_1396: jz short L_139b
L_1398: call keyboard_service_0bc0
L_139b: ret
keyboard_original_139c:
L_139c: lea bx,[keyboard_state_36f0]
L_13a0: call keyboard_mapping_emit
L_13a3: cmp word [keyboard_state_1d1a],0x0
L_13a8: jz short L_13ad
L_13aa: call keyboard_service_1e30
L_13ad: ret
keyboard_original_13ae:
L_13ae: lea bx,[keyboard_state_36fc]
L_13b2: call keyboard_mapping_emit
L_13b5: cmp word [keyboard_state_1d1a],0x0
L_13ba: jz short L_13bf
L_13bc: call keyboard_service_1ea0
L_13bf: ret
keyboard_original_13c0:
L_13c0: lea bx,[keyboard_state_36d8]
L_13c4: call keyboard_mapping_emit
L_13c7: cmp word [keyboard_state_1d1a],0x0
L_13cc: jz short L_13d1
L_13ce: call keyboard_service_1efc
L_13d1: ret
keyboard_original_13d2:
L_13d2: lea bx,[keyboard_state_36e4]
L_13d6: call keyboard_mapping_emit
L_13d9: cmp word [keyboard_state_1d1a],0x0
L_13de: jz short L_13e3
L_13e0: call keyboard_service_1e0c
L_13e3: ret
keyboard_original_13e4:
L_13e4: cmp word [keyboard_state_900c],0x0
L_13e9: jz short L_1402
L_13eb: call keyboard_service_64fe
L_13ee: mov [keyboard_mapping_key],ax
L_13f1: mov ax,0x1
L_13f4: push ax
L_13f5: call keyboard_service_ab0b
L_13f8: push word [keyboard_mapping_key]
L_13fc: call keyboard_service_ab0b
L_13ff: call keyboard_service_40c1
L_1402: ret
L_1403: nop
keyboard_original_1404:
L_1404: lea bx,[keyboard_state_34b0]
L_1408: call keyboard_mapping_emit
L_140b: jmp near keyboard_service_0ca2
keyboard_original_140e:
L_140e: lea bx,[keyboard_state_34bc]
L_1412: call keyboard_mapping_emit
L_1415: jmp near keyboard_service_0ca2
keyboard_original_1418:
L_1418: lea bx,[keyboard_state_35b8]
L_141c: call keyboard_mapping_emit
L_141f: jmp near keyboard_service_0ca2
keyboard_original_1422:
L_1422: lea bx,[keyboard_state_35c4]
L_1426: call keyboard_mapping_emit
L_1429: jmp near keyboard_service_0ca2
keyboard_original_142c:
L_142c: lea bx,[keyboard_state_36c0]
L_1430: call keyboard_mapping_emit
L_1433: jmp near keyboard_service_0ca2
keyboard_original_1436:
L_1436: lea bx,[keyboard_state_36cc]
L_143a: call keyboard_mapping_emit
L_143d: jmp near keyboard_service_0ca2
keyboard_original_1440:
L_1440: cmp word [keyboard_state_4b02],0x0
L_1445: jnz short L_1452
L_1447: mov word [keyboard_state_4afe],0x0
L_144d: call keyboard_service_4b14
L_1450: ret
L_1451: nop
L_1452: lea bx,[keyboard_state_4210]
L_1456: call keyboard_service_427f
L_1459: ret
keyboard_original_145a:
L_145a: push bp
L_145b: mov_load bp,sp
L_145d: sub sp,0x4
L_1460: push si
L_1461: mov ax,keyboard_state_3262
L_1464: push ax
L_1465: push word [keyboard_state_1d18]
L_1469: mov ax,keyboard_state_4675
L_146c: push ax
L_146d: mov ax,keyboard_state_ce6a
L_1470: push ax
L_1471: call keyboard_service_82b6
L_1474: add sp,0x8
L_1477: call keyboard_service_6bbe
L_147a: mov_load si,ax
L_147c: mov [bp-0x2],dx
L_147f: sub_load ax,ax
L_1481: push ax
L_1482: push ax
L_1483: push ax
L_1484: mov ax,keyboard_state_ce6a
L_1487: push ax
L_1488: mov ax,keyboard_state_467b
L_148b: push ax
L_148c: call keyboard_service_353d
L_148f: add sp,0x2
L_1492: push ax
L_1493: call keyboard_service_433d
L_1496: add sp,0xa
L_1499: push word [bp-0x2]
L_149c: push si
L_149d: call keyboard_service_4870
L_14a0: call keyboard_service_0cd2
L_14a3: pop si
L_14a4: mov_load sp,bp
L_14a6: pop bp
L_14a7: ret
keyboard_original_14a8:
L_14a8: cmp word [keyboard_mapping_scrollback_mode],0x0
L_14ad: jz short L_14ba
L_14af: sub_load ax,ax
L_14b1: push ax
L_14b2: call keyboard_service_0e06
L_14b5: add sp,0x2
L_14b8: ret
L_14b9: nop
L_14ba: lea bx,[keyboard_state_3414]
L_14be: call keyboard_mapping_emit
L_14c1: ret
keyboard_original_14c2:
L_14c2: cmp word [keyboard_mapping_scrollback_mode],0x0
L_14c7: jz short L_14d4
L_14c9: mov ax,0x1
L_14cc: push ax
L_14cd: call keyboard_service_0e06
L_14d0: add sp,0x2
L_14d3: ret
L_14d4: lea bx,[keyboard_state_3420]
L_14d8: call keyboard_mapping_emit
L_14db: ret
keyboard_original_14dc:
L_14dc: cmp word [keyboard_mapping_scrollback_mode],0x0
L_14e1: jz short L_14ec
L_14e3: lea bx,[keyboard_state_3414]
L_14e7: call keyboard_mapping_emit
L_14ea: ret
L_14eb: nop
L_14ec: sub_load ax,ax
L_14ee: push ax
L_14ef: call keyboard_service_0e06
L_14f2: add sp,0x2
L_14f5: ret
keyboard_original_14f6:
L_14f6: cmp word [keyboard_mapping_scrollback_mode],0x0
L_14fb: jz short L_1506
L_14fd: lea bx,[keyboard_state_3420]
L_1501: call keyboard_mapping_emit
L_1504: ret
L_1505: nop
L_1506: mov ax,0x1
L_1509: push ax
L_150a: call keyboard_service_0e06
L_150d: add sp,0x2
L_1510: ret
L_1511: nop
keyboard_original_1512:
L_1512: lea bx,[keyboard_state_3408]
L_1516: call keyboard_mapping_emit
L_1519: ret
keyboard_original_151a:
L_151a: lea bx,[keyboard_state_33fc]
L_151e: call keyboard_mapping_emit
L_1521: jmp near keyboard_service_0ca2
keyboard_original_1524:
L_1524: lea bx,[keyboard_state_3708]
L_1528: call keyboard_mapping_emit
L_152b: cmp word [keyboard_state_1d1a],0x0
L_1530: jz short L_1538
L_1532: sub_load ax,ax
L_1534: cwd
L_1535: call keyboard_service_1bbe
L_1538: ret
L_1539: nop
keyboard_original_153a:
L_153a: lea bx,[keyboard_state_3714]
L_153e: call keyboard_mapping_emit
L_1541: ret
keyboard_original_1542:
L_1542: call keyboard_service_6e5a
L_1545: call keyboard_service_baab
L_1548: call keyboard_service_6dca
L_154b: ret
keyboard_original_154c:
L_154c: mov bx,[keyboard_mapping_key]
L_1550: mov_load ax,bx
L_1552: shl bx,1
L_1554: add_load bx,ax
L_1556: shl bx,1
L_1558: shl bx,1
L_155a: add bx,keyboard_state_3150
L_155e: call keyboard_mapping_emit
L_1561: jmp near keyboard_service_0ca2
keyboard_original_1564:
L_1564: mov bx,[keyboard_mapping_key]
L_1568: mov_load ax,bx
L_156a: shl bx,1
L_156c: add_load bx,ax
L_156e: shl bx,1
L_1570: shl bx,1
L_1572: add bx,keyboard_state_3174
L_1576: call keyboard_mapping_emit
L_1579: jmp near keyboard_service_0ca2
keyboard_original_157c:
L_157c: mov bx,[keyboard_mapping_key]
L_1580: mov_load ax,bx
L_1582: shl bx,1
L_1584: add_load bx,ax
L_1586: shl bx,1
L_1588: shl bx,1
L_158a: add bx,keyboard_state_31e0
L_158e: call keyboard_mapping_emit
L_1591: jmp near keyboard_service_0ca2
keyboard_original_1594:
L_1594: mov ax,0x3
L_1597: push ax
L_1598: mov ax,[keyboard_mapping_key]
L_159b: sub ax,strict word 0x78
L_159e: mov cx,0x36
L_15a1: mul cx
L_15a3: mov_load bx,ax
L_15a5: push word [bx+keyboard_state_3756]
L_15a9: add bx,keyboard_state_3758
L_15ad: push bx
L_15ae: call keyboard_service_47b6
L_15b1: add sp,0x6
L_15b4: ret
L_15b5: nop
keyboard_original_15b6:
L_15b6: cmp word [keyboard_mapping_key],0x53
L_15bb: jnz short L_15c4
L_15bd: lea bx,[keyboard_state_33e4]
L_15c1: jmp short L_15c8
L_15c3: nop
L_15c4: lea bx,[keyboard_state_360c]
L_15c8: call keyboard_mapping_emit
L_15cb: cmp word [keyboard_state_1d1a],0x0
L_15d0: jz short L_15d5
L_15d2: call keyboard_service_ba03
L_15d5: ret
keyboard_original_15d6:
L_15d6: cmp word [keyboard_mapping_key],0x52
L_15db: jnz short L_15e4
L_15dd: lea bx,[keyboard_state_33d8]
L_15e1: jmp short L_15e8
L_15e3: nop
L_15e4: lea bx,[keyboard_state_3600]
L_15e8: call keyboard_mapping_emit
L_15eb: cmp word [keyboard_state_1d1a],0x0
L_15f0: jz short L_15f5
L_15f2: call keyboard_service_b9f7
L_15f5: cmp word [keyboard_state_3976],0x0
L_15fa: jz short L_1600
L_15fc: call keyboard_service_0ca2
L_15ff: ret
L_1600: call keyboard_service_0cb4
L_1603: ret
keyboard_mapping_dispatch:
L_1604: push bp
L_1605: mov_load bp,sp
L_1607: sub sp,0x6
L_160a: mov ax,[keyboard_mapping_key]
L_160d: mov [bp-0x2],ax
L_1610: test al,0xff
L_1612: jnz short L_1630
L_1614: mov al,[bp-0x1]
L_1617: sub_load ah,ah
L_1619: mov [keyboard_mapping_key],ax
L_161c: cmp ax,0x8c
L_161f: jna short L_1624
L_1621: jmp near L_170a
L_1624: mov_load bx,ax
L_1626: shl bx,1
L_1628: call word near [bx+keyboard_dispatch_table]
L_162c: jmp near L_170a
L_162f: nop
L_1630: mov al,[keyboard_mapping_hook_character]
L_1633: cbw
L_1634: cmp ax,[keyboard_mapping_key]
L_1638: jnz short L_16a2
L_163a: cmp word [keyboard_mapping_hook_enabled],0x0
L_163f: jz short L_16a2
L_1641: call keyboard_service_b9d3
L_1644: mov [bp-0x4],ax
L_1647: inc ax
L_1648: jz short L_1650
L_164a: cmp word [bp-0x4],0xfffffffffffffffe
L_164e: jnz short L_165e
L_1650: mov ax,0x1
L_1653: push ax
L_1654: call keyboard_service_20a4
L_1657: add sp,0x2
L_165a: mov_load sp,bp
L_165c: pop bp
L_165d: ret
L_165e: cmp word [bp-0x4],0xfffffffffffffffd
L_1662: jnz short L_166c
L_1664: call keyboard_service_3a25
L_1667: mov_load sp,bp
L_1669: pop bp
L_166a: ret
L_166b: nop
L_166c: cmp word [keyboard_mapping_key],0x4900
L_1672: jnz short L_1684
L_1674: cmp word [keyboard_mapping_scrollback_mode],0x0
L_1679: jnz short L_160a
L_167b: mov word [keyboard_mapping_key],0x8400
L_1681: jmp short L_160a
L_1683: nop
L_1684: cmp word [keyboard_mapping_key],0x5100
L_168a: jz short L_168f
L_168c: jmp near L_160a
L_168f: cmp word [keyboard_mapping_scrollback_mode],0x0
L_1694: jz short L_1699
L_1696: jmp near L_160a
L_1699: mov word [keyboard_mapping_key],0x7600
L_169f: jmp near L_160a
L_16a2: mov ax,[keyboard_mapping_key]
L_16a5: cmp ax,0x4be0
L_16a8: jnz short L_16ad
L_16aa: jmp near L_173a
L_16ad: jna short L_16b2
L_16af: jmp near L_19be
L_16b2: cmp ax,0xe7f
L_16b5: jnz short L_16ba
L_16b7: jmp near L_17be
L_16ba: jna short L_16bf
L_16bc: jmp near L_1970
L_16bf: cmp ax,strict word 0xd
L_16c2: jnz short L_16c7
L_16c4: jmp near L_177c
L_16c7: jna short L_16cc
L_16c9: jmp near L_1930
L_16cc: cmp ax,strict word 0x9
L_16cf: jnz short L_16d4
L_16d1: jmp near L_17ac
L_16d4: jna short L_16d9
L_16d6: jmp near L_1944
L_16d9: or_load al,al
L_16db: jz short L_170a
L_16dd: sub al,0x7
L_16df: jnz short L_16e4
L_16e1: jmp near L_1790
L_16e4: jmp near L_1944
L_16e7: nop
L_16e8: lea bx,[keyboard_state_33f0]
L_16ec: call keyboard_mapping_emit
L_16ef: cmp word [keyboard_state_1d1a],0x0
L_16f4: jz short L_1700
L_16f6: mov ax,0x8
L_16f9: push ax
L_16fa: call keyboard_service_0610
L_16fd: add sp,0x2
L_1700: cmp word [keyboard_state_373c],0x0
L_1705: jz short L_170a
L_1707: call keyboard_service_badb
L_170a: cmp word [bp-0x2],0x80
L_170f: jc short L_1714
L_1711: jmp near L_1a64
L_1714: cmp word [keyboard_state_373c],0x0
L_1719: jnz short L_171e
L_171b: jmp near L_1a71
L_171e: call keyboard_service_badb
L_1721: mov_load sp,bp
L_1723: pop bp
L_1724: ret
L_1725: nop
L_1726: lea bx,[keyboard_state_35f4]
L_172a: call keyboard_mapping_emit
L_172d: cmp word [keyboard_state_1d1a],0x0
L_1732: jz short L_170a
L_1734: call keyboard_service_1ea0
L_1737: jmp short L_170a
L_1739: nop
L_173a: lea bx,[keyboard_state_35e8]
L_173e: call keyboard_mapping_emit
L_1741: cmp word [keyboard_state_1d1a],0x0
L_1746: jz short L_170a
L_1748: call keyboard_service_1e30
L_174b: jmp short L_170a
L_174d: nop
L_174e: lea bx,[keyboard_state_35dc]
L_1752: call keyboard_mapping_emit
L_1755: cmp word [keyboard_state_1d1a],0x0
L_175a: jz short L_170a
L_175c: call keyboard_service_1e0c
L_175f: jmp short L_170a
L_1761: nop
L_1762: lea bx,[keyboard_state_35d0]
L_1766: call keyboard_mapping_emit
L_1769: cmp word [keyboard_state_1d1a],0x0
L_176e: jz short L_170a
L_1770: call keyboard_service_1efc
L_1773: jmp short L_170a
L_1775: nop
L_1776: call L_15b6
L_1779: jmp short L_170a
L_177b: nop
L_177c: lea bx,[keyboard_state_3720]
L_1780: call keyboard_mapping_emit
L_1783: lea bx,[keyboard_state_3720]
L_1787: call keyboard_mapping_echo
L_178a: call keyboard_service_0ca2
L_178d: jmp near L_170a
L_1790: cmp word [keyboard_state_1d1a],0x0
L_1795: jz short L_17a3
L_1797: mov al,[keyboard_mapping_key]
L_179a: sub_load ah,ah
L_179c: push ax
L_179d: call keyboard_service_0610
L_17a0: add sp,0x2
L_17a3: push word [keyboard_mapping_key]
L_17a7: call keyboard_service_ab0b
L_17aa: jmp short L_178a
L_17ac: lea bx,[keyboard_state_33c0]
L_17b0: call keyboard_mapping_emit
L_17b3: lea bx,[keyboard_state_33c0]
L_17b7: call keyboard_mapping_echo
L_17ba: jmp near L_170a
L_17bd: nop
L_17be: lea bx,[keyboard_state_342c]
L_17c2: jmp short L_17f7
L_17c4: lea bx,[terminal_keymap]
L_17c8: call keyboard_mapping_emit
L_17cb: lea bx,[terminal_keymap]
L_17cf: jmp short L_1787
L_17d1: nop
L_17d2: cmp byte [keyboard_state_3630],0x0
L_17d7: jz short L_17e0
L_17d9: lea bx,[keyboard_state_3630]
L_17dd: jmp short L_17f7
L_17df: nop
L_17e0: sub_load ax,ax
L_17e2: push ax
L_17e3: call keyboard_service_0e06
L_17e6: add sp,0x2
L_17e9: jmp near L_170a
L_17ec: cmp byte [keyboard_state_363c],0x0
L_17f1: jz short L_17fe
L_17f3: lea bx,[keyboard_state_363c]
L_17f7: call keyboard_mapping_emit
L_17fa: jmp near L_170a
L_17fd: nop
L_17fe: mov ax,0x1
L_1801: jmp short L_17e2
L_1803: nop
L_1804: lea bx,[keyboard_state_33b4]
L_1808: call keyboard_mapping_emit
L_180b: lea bx,[keyboard_state_33b4]
L_180f: jmp near L_1787
L_1812: lea bx,[keyboard_state_3390]
L_1816: call keyboard_mapping_emit
L_1819: lea bx,[keyboard_state_3390]
L_181d: jmp near L_1787
L_1820: lea bx,[keyboard_state_3384]
L_1824: call keyboard_mapping_emit
L_1827: lea bx,[keyboard_state_3384]
L_182b: jmp near L_1787
L_182e: lea bx,[keyboard_state_339c]
L_1832: call keyboard_mapping_emit
L_1835: lea bx,[keyboard_state_339c]
L_1839: jmp near L_1787
L_183c: lea bx,[keyboard_state_33a8]
L_1840: call keyboard_mapping_emit
L_1843: lea bx,[keyboard_state_33a8]
L_1847: jmp near L_1787
L_184a: lea bx,[keyboard_state_34c8]
L_184e: call keyboard_mapping_emit
L_1851: lea bx,[keyboard_state_34c8]
L_1855: jmp near L_1787
L_1858: lea bx,[keyboard_state_34d4]
L_185c: call keyboard_mapping_emit
L_185f: lea bx,[keyboard_state_34d4]
L_1863: jmp near L_1787
L_1866: lea bx,[keyboard_state_34e0]
L_186a: call keyboard_mapping_emit
L_186d: lea bx,[keyboard_state_34e0]
L_1871: jmp near L_1787
L_1874: lea bx,[keyboard_state_34ec]
L_1878: call keyboard_mapping_emit
L_187b: lea bx,[keyboard_state_34ec]
L_187f: jmp near L_1787
L_1882: lea bx,[keyboard_state_34f8]
L_1886: call keyboard_mapping_emit
L_1889: lea bx,[keyboard_state_34f8]
L_188d: jmp near L_1787
L_1890: lea bx,[keyboard_state_3504]
L_1894: call keyboard_mapping_emit
L_1897: lea bx,[keyboard_state_3504]
L_189b: jmp near L_1787
L_189e: lea bx,[keyboard_state_3510]
L_18a2: call keyboard_mapping_emit
L_18a5: lea bx,[keyboard_state_3510]
L_18a9: jmp near L_1787
L_18ac: lea bx,[keyboard_state_351c]
L_18b0: call keyboard_mapping_emit
L_18b3: lea bx,[keyboard_state_351c]
L_18b7: jmp near L_1787
L_18ba: lea bx,[keyboard_state_3528]
L_18be: call keyboard_mapping_emit
L_18c1: lea bx,[keyboard_state_3528]
L_18c5: jmp near L_1787
L_18c8: lea bx,[keyboard_state_3534]
L_18cc: call keyboard_mapping_emit
L_18cf: lea bx,[keyboard_state_3534]
L_18d3: jmp near L_1787
L_18d6: lea bx,[keyboard_state_3618]
L_18da: jmp near L_17f7
L_18dd: nop
L_18de: lea bx,[keyboard_state_3624]
L_18e2: jmp near L_17f7
L_18e5: nop
L_18e6: call keyboard_service_bab7
L_18e9: jmp near L_170a
L_18ec: call keyboard_service_ba93
L_18ef: jmp near L_170a
L_18f2: call L_15d6
L_18f5: jmp near L_170a
L_18f8: call keyboard_service_1aaa
L_18fb: jmp near L_170a
L_18fe: call keyboard_service_46ba
L_1901: jmp near L_170a
L_1904: sub_load ax,ax
L_1906: push ax
L_1907: push word [keyboard_state_1d4e]
L_190b: mov ax,[keyboard_state_cee6]
L_190e: cmp word [keyboard_state_2070],0x1
L_1913: sbb_load cx,cx
L_1915: and cl,0xfe
L_1918: add cx,0x4
L_191b: cwd
L_191c: idiv cx
L_191e: inc dx
L_191f: push dx
L_1920: call keyboard_service_2eaa
L_1923: add sp,0x6
L_1926: mov ax,[keyboard_state_3252]
L_1929: mov [keyboard_state_cee6],ax
L_192c: jmp near L_170a
L_192f: nop
L_1930: sub ax,strict word 0x1c
L_1933: jz short L_18f8
L_1935: dec ax
L_1936: jz short L_18fe
L_1938: dec ax
L_1939: dec ax
L_193a: jz short L_1904
L_193c: sub ax,0xde9
L_193f: jnz short L_1944
L_1941: jmp near L_16e8
L_1944: test byte [keyboard_state_cffb],0xff
L_1949: jz short L_194e
L_194b: jmp near L_170a
L_194e: cmp word [keyboard_state_1d1a],0x0
L_1953: jz short L_1966
L_1955: cmp word [keyboard_mapping_key],0x1b
L_195a: jz short L_1966
L_195c: push word [keyboard_mapping_key]
L_1960: call keyboard_service_0610
L_1963: add sp,0x2
L_1966: push word [keyboard_mapping_key]
L_196a: call keyboard_service_ab0b
L_196d: jmp near L_170a
L_1970: cmp ax,0x48e0
L_1973: jnz short L_1978
L_1975: jmp near L_1762
L_1978: ja short L_199c
L_197a: sub ax,0x372a
L_197d: jnz short L_1982
L_197f: jmp near L_17c4
L_1982: sub ax,0x100d
L_1985: jnz short L_198a
L_1987: jmp near L_18ac
L_198a: sub ax,0xa9
L_198d: jnz short L_1992
L_198f: jmp near L_18d6
L_1992: sub ax,strict word 0x58
L_1995: jnz short L_199a
L_1997: jmp near L_18ba
L_199a: jmp short L_1944
L_199c: sub ax,0x4939
L_199f: jnz short L_19a4
L_19a1: jmp near L_18c8
L_19a4: sub ax,0xa7
L_19a7: jnz short L_19ac
L_19a9: jmp near L_17d2
L_19ac: sub ax,strict word 0x4d
L_19af: jnz short L_19b4
L_19b1: jmp near L_1820
L_19b4: sub ax,0x107
L_19b7: jnz short L_19bc
L_19b9: jmp near L_1882
L_19bc: jmp short L_1944
L_19be: cmp ax,0x5133
L_19c1: jnz short L_19c6
L_19c3: jmp near L_1874
L_19c6: ja short L_1a12
L_19c8: cmp ax,0x4e2b
L_19cb: jnz short L_19d0
L_19cd: jmp near L_1812
L_19d0: ja short L_19ee
L_19d2: sub ax,0x4c35
L_19d5: jnz short L_19da
L_19d7: jmp near L_1890
L_19da: sub ax,0x101
L_19dd: jnz short L_19e2
L_19df: jmp near L_189e
L_19e2: sub ax,0xaa
L_19e5: jnz short L_19ea
L_19e7: jmp near L_1726
L_19ea: jmp near L_1944
L_19ed: nop
L_19ee: sub ax,0x4f31
L_19f1: jnz short L_19f6
L_19f3: jmp near L_1858
L_19f6: sub ax,0xaf
L_19f9: jnz short L_19fe
L_19fb: jmp near L_18de
L_19fe: sub ax,strict word 0x52
L_1a01: jnz short L_1a06
L_1a03: jmp near L_1866
L_1a06: sub ax,0xae
L_1a09: jnz short L_1a0e
L_1a0b: jmp near L_174e
L_1a0e: jmp near L_1944
L_1a11: nop
L_1a12: cmp ax,0x53e0
L_1a15: jnz short L_1a1a
L_1a17: jmp near L_1776
L_1a1a: ja short L_1a40
L_1a1c: sub ax,0x51e0
L_1a1f: jnz short L_1a24
L_1a21: jmp near L_17ec
L_1a24: sub ax,strict word 0x50
L_1a27: jnz short L_1a2c
L_1a29: jmp near L_184a
L_1a2c: sub ax,0xb0
L_1a2f: jnz short L_1a34
L_1a31: jmp near L_18f2
L_1a34: sub ax,strict word 0x4e
L_1a37: jnz short L_1a3c
L_1a39: jmp near L_182e
L_1a3c: jmp near L_1944
L_1a3f: nop
L_1a40: sub ax,0x73e0
L_1a43: jnz short L_1a48
L_1a45: jmp near L_18e6
L_1a48: sub ax,0x100
L_1a4b: jnz short L_1a50
L_1a4d: jmp near L_18ec
L_1a50: sub ax,0x6b2d
L_1a53: jnz short L_1a58
L_1a55: jmp near L_1804
L_1a58: sub ax,strict word 0x22
L_1a5b: jnz short L_1a60
L_1a5d: jmp near L_183c
L_1a60: jmp near L_1944
L_1a63: nop
L_1a64: push word [keyboard_state_333e]
L_1a68: call keyboard_service_2f78
L_1a6b: add sp,0x2
L_1a6e: call keyboard_service_2fb8
L_1a71: mov_load sp,bp
L_1a73: pop bp
L_1a74: ret
