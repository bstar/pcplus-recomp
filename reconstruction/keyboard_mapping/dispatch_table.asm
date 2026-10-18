; Exact original DS44e0 indirect near-code targets, not live profile bindings.
BITS 16
%ifdef KEYBOARD_MAPPING_OMF
SEGMENT _DATA public class=DATA use16
global keyboard_dispatch_table
extern keyboard_original_0401
extern keyboard_original_0553
extern keyboard_mapping_noop
extern keyboard_original_12d2
extern keyboard_original_1302
extern keyboard_original_1310
extern keyboard_original_132e
extern keyboard_original_1340
extern keyboard_original_134c
extern keyboard_original_1350
extern keyboard_original_1368
extern keyboard_original_1374
extern keyboard_original_138a
extern keyboard_original_139c
extern keyboard_original_13ae
extern keyboard_original_13c0
extern keyboard_original_13d2
extern keyboard_original_13e4
extern keyboard_original_1404
extern keyboard_original_140e
extern keyboard_original_1418
extern keyboard_original_1422
extern keyboard_original_142c
extern keyboard_original_1436
extern keyboard_original_1440
extern keyboard_original_145a
extern keyboard_original_14a8
extern keyboard_original_14c2
extern keyboard_original_14dc
extern keyboard_original_14f6
extern keyboard_original_1512
extern keyboard_original_151a
extern keyboard_original_1524
extern keyboard_original_153a
extern keyboard_original_1542
extern keyboard_original_154c
extern keyboard_original_1564
extern keyboard_original_157c
extern keyboard_original_1594
extern keyboard_original_15b6
extern keyboard_original_15d6
extern keyboard_original_1a76
extern keyboard_original_24e2
extern keyboard_original_3250
extern keyboard_original_3316
extern keyboard_original_332e
extern keyboard_original_3a25
extern keyboard_original_40aa
extern keyboard_original_56fe
extern keyboard_original_ba0f
extern keyboard_original_ba1b
extern keyboard_original_ba27
extern keyboard_original_ba3f
extern keyboard_original_ba57
extern keyboard_original_ba63
extern keyboard_original_ba6f
extern keyboard_original_ba7b
extern keyboard_original_ba93
extern keyboard_original_ba9f
extern keyboard_original_bab7
extern keyboard_original_bac3
extern keyboard_original_baf3
extern keyboard_original_bb17
extern keyboard_original_bb23
extern keyboard_original_bb47
keyboard_dispatch_table:
 dw keyboard_mapping_noop ; scan00
 dw keyboard_mapping_noop ; scan01
 dw keyboard_mapping_noop ; scan02
 dw keyboard_original_40aa ; scan03
 dw keyboard_mapping_noop ; scan04
 dw keyboard_mapping_noop ; scan05
 dw keyboard_mapping_noop ; scan06
 dw keyboard_mapping_noop ; scan07
 dw keyboard_mapping_noop ; scan08
 dw keyboard_mapping_noop ; scan09
 dw keyboard_mapping_noop ; scan0a
 dw keyboard_mapping_noop ; scan0b
 dw keyboard_mapping_noop ; scan0c
 dw keyboard_mapping_noop ; scan0d
 dw keyboard_mapping_noop ; scan0e
 dw keyboard_original_138a ; scan0f
 dw keyboard_original_1350 ; scan10
 dw keyboard_original_ba0f ; scan11
 dw keyboard_original_3316 ; scan12
 dw keyboard_original_baf3 ; scan13
 dw keyboard_original_ba1b ; scan14
 dw keyboard_original_0553 ; scan15
 dw keyboard_original_1368 ; scan16
 dw keyboard_original_ba57 ; scan17
 dw keyboard_original_bac3 ; scan18
 dw keyboard_original_134c ; scan19
 dw keyboard_mapping_noop ; scan1a
 dw keyboard_mapping_noop ; scan1b
 dw keyboard_mapping_noop ; scan1c
 dw keyboard_mapping_noop ; scan1d
 dw keyboard_original_ba7b ; scan1e
 dw keyboard_original_ba63 ; scan1f
 dw keyboard_original_12d2 ; scan20
 dw keyboard_original_1302 ; scan21
 dw keyboard_original_1310 ; scan22
 dw keyboard_original_132e ; scan23
 dw keyboard_original_3a25 ; scan24
 dw keyboard_original_1340 ; scan25
 dw keyboard_original_1a76 ; scan26
 dw keyboard_mapping_noop ; scan27
 dw keyboard_mapping_noop ; scan28
 dw keyboard_mapping_noop ; scan29
 dw keyboard_mapping_noop ; scan2a
 dw keyboard_mapping_noop ; scan2b
 dw keyboard_original_56fe ; scan2c
 dw keyboard_original_3250 ; scan2d
 dw keyboard_original_24e2 ; scan2e
 dw keyboard_original_1374 ; scan2f
 dw keyboard_original_0401 ; scan30
 dw keyboard_original_ba6f ; scan31
 dw keyboard_original_ba9f ; scan32
 dw keyboard_mapping_noop ; scan33
 dw keyboard_mapping_noop ; scan34
 dw keyboard_mapping_noop ; scan35
 dw keyboard_mapping_noop ; scan36
 dw keyboard_mapping_noop ; scan37
 dw keyboard_mapping_noop ; scan38
 dw keyboard_mapping_noop ; scan39
 dw keyboard_mapping_noop ; scan3a
 dw keyboard_original_1564 ; scan3b
 dw keyboard_original_1564 ; scan3c
 dw keyboard_original_1564 ; scan3d
 dw keyboard_original_1564 ; scan3e
 dw keyboard_original_1564 ; scan3f
 dw keyboard_original_1564 ; scan40
 dw keyboard_original_1564 ; scan41
 dw keyboard_original_1564 ; scan42
 dw keyboard_original_1564 ; scan43
 dw keyboard_original_1564 ; scan44
 dw keyboard_mapping_noop ; scan45
 dw keyboard_mapping_noop ; scan46
 dw keyboard_original_1524 ; scan47
 dw keyboard_original_13c0 ; scan48
 dw keyboard_original_14a8 ; scan49
 dw keyboard_mapping_noop ; scan4a
 dw keyboard_original_139c ; scan4b
 dw keyboard_mapping_noop ; scan4c
 dw keyboard_original_13ae ; scan4d
 dw keyboard_mapping_noop ; scan4e
 dw keyboard_original_153a ; scan4f
 dw keyboard_original_13d2 ; scan50
 dw keyboard_original_14c2 ; scan51
 dw keyboard_original_15d6 ; scan52
 dw keyboard_original_15b6 ; scan53
 dw keyboard_original_154c ; scan54
 dw keyboard_original_154c ; scan55
 dw keyboard_original_154c ; scan56
 dw keyboard_original_154c ; scan57
 dw keyboard_original_154c ; scan58
 dw keyboard_original_154c ; scan59
 dw keyboard_original_154c ; scan5a
 dw keyboard_original_154c ; scan5b
 dw keyboard_original_154c ; scan5c
 dw keyboard_original_154c ; scan5d
 dw keyboard_original_157c ; scan5e
 dw keyboard_original_157c ; scan5f
 dw keyboard_original_157c ; scan60
 dw keyboard_original_157c ; scan61
 dw keyboard_original_157c ; scan62
 dw keyboard_original_157c ; scan63
 dw keyboard_original_157c ; scan64
 dw keyboard_original_157c ; scan65
 dw keyboard_original_157c ; scan66
 dw keyboard_original_157c ; scan67
 dw keyboard_original_bb23 ; scan68
 dw keyboard_original_bb17 ; scan69
 dw keyboard_original_332e ; scan6a
 dw keyboard_original_ba3f ; scan6b
 dw keyboard_original_1440 ; scan6c
 dw keyboard_original_bb47 ; scan6d
 dw keyboard_original_ba27 ; scan6e
 dw keyboard_original_145a ; scan6f
 dw keyboard_mapping_noop ; scan70
 dw keyboard_original_13e4 ; scan71
 dw keyboard_mapping_noop ; scan72
 dw keyboard_original_bab7 ; scan73
 dw keyboard_original_ba93 ; scan74
 dw keyboard_original_1512 ; scan75
 dw keyboard_original_14f6 ; scan76
 dw keyboard_original_151a ; scan77
 dw keyboard_original_1594 ; scan78
 dw keyboard_original_1594 ; scan79
 dw keyboard_original_1594 ; scan7a
 dw keyboard_original_1594 ; scan7b
 dw keyboard_original_1594 ; scan7c
 dw keyboard_original_1594 ; scan7d
 dw keyboard_original_1594 ; scan7e
 dw keyboard_original_1594 ; scan7f
 dw keyboard_original_1594 ; scan80
 dw keyboard_original_1594 ; scan81
 dw keyboard_mapping_noop ; scan82
 dw keyboard_original_1542 ; scan83
 dw keyboard_original_14dc ; scan84
 dw keyboard_original_1404 ; scan85
 dw keyboard_original_140e ; scan86
 dw keyboard_original_1418 ; scan87
 dw keyboard_original_1422 ; scan88
 dw keyboard_original_142c ; scan89
 dw keyboard_original_1436 ; scan8a
 dw keyboard_mapping_noop ; scan8b
 dw keyboard_mapping_noop ; scan8c
%else
dw 0x0e60,0x0e60,0x0e60,0x40aa,0x0e60,0x0e60,0x0e60,0x0e60,0x0e60,0x0e60
dw 0x0e60,0x0e60,0x0e60,0x0e60,0x0e60,0x138a,0x1350,0xba0f,0x3316,0xbaf3
dw 0xba1b,0x0553,0x1368,0xba57,0xbac3,0x134c,0x0e60,0x0e60,0x0e60,0x0e60
dw 0xba7b,0xba63,0x12d2,0x1302,0x1310,0x132e,0x3a25,0x1340,0x1a76,0x0e60
dw 0x0e60,0x0e60,0x0e60,0x0e60,0x56fe,0x3250,0x24e2,0x1374,0x0401,0xba6f
dw 0xba9f,0x0e60,0x0e60,0x0e60,0x0e60,0x0e60,0x0e60,0x0e60,0x0e60,0x1564
dw 0x1564,0x1564,0x1564,0x1564,0x1564,0x1564,0x1564,0x1564,0x1564,0x0e60
dw 0x0e60,0x1524,0x13c0,0x14a8,0x0e60,0x139c,0x0e60,0x13ae,0x0e60,0x153a
dw 0x13d2,0x14c2,0x15d6,0x15b6,0x154c,0x154c,0x154c,0x154c,0x154c,0x154c
dw 0x154c,0x154c,0x154c,0x154c,0x157c,0x157c,0x157c,0x157c,0x157c,0x157c
dw 0x157c,0x157c,0x157c,0x157c,0xbb23,0xbb17,0x332e,0xba3f,0x1440,0xbb47
dw 0xba27,0x145a,0x0e60,0x13e4,0x0e60,0xbab7,0xba93,0x1512,0x14f6,0x151a
dw 0x1594,0x1594,0x1594,0x1594,0x1594,0x1594,0x1594,0x1594,0x1594,0x1594
dw 0x0e60,0x1542,0x14dc,0x1404,0x140e,0x1418,0x1422,0x142c,0x1436,0x0e60
dw 0x0e60
%endif
