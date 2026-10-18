#ifndef PCPLUS_TERMINAL_IMPORT_H
#define PCPLUS_TERMINAL_IMPORT_H
#include "prm_dos.h"
/* Explicit, partial 2.01 import. No version signature is known. The requested
 * file must be externally identified as2.01; unknown fields are not applied.
 * All fields are16-bit DOS words; see terminal_import.inc for assembly layout. */
typedef struct terminal_import_settings {
 unsigned port_number,baud_low,baud_high,parity,data_bits,stop_bits;
 unsigned software_flow,hardware_flow,terminal_id;
 unsigned normal_attribute,bold_attribute,preset_attribute;
 unsigned reverse_attribute,underline_attribute,autowrap,scroll_enabled;
 unsigned io_base,irq;
 unsigned mapping_pause_character,mapping_character_delay_units;
 unsigned translation_mode,clipboard_separator;
} terminal_import_settings;
typedef unsigned terminal_import_status;
enum {
 TERMINAL_IMPORT_OK=0, TERMINAL_IMPORT_IO, TERMINAL_IMPORT_SERIAL,
 TERMINAL_IMPORT_FLOW, TERMINAL_IMPORT_PROFILE, TERMINAL_IMPORT_DISPLAY,
 TERMINAL_IMPORT_ARGUMENT,TERMINAL_IMPORT_TRANSLATION=12,TERMINAL_IMPORT_CLIPBOARD=13
};
/* Destination commits only on success. No DOS/UART/BIOS in decode(). */
terminal_import_status __cdecl terminal_import_decode(const prm_dos_image *image,
 terminal_import_settings *destination);
/* Read-only exact-size load; IO detail optional. Does not create/repair files. */
terminal_import_status __cdecl terminal_import_read(const char *path,
 terminal_import_settings *destination,prm_dos_result *io);
#endif
