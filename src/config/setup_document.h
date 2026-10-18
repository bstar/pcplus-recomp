#ifndef PCPLUS_SETUP_DOCUMENT_H
#define PCPLUS_SETUP_DOCUMENT_H
#include "setup_model.h"
#include "prm_replace.h"
/* Offline owner for an existing, externally identified 2.01 image. No UART
 * reconfiguration. Save rechecks the original file before checked replacement;
 * it is not a concurrent-writer lock or a crash-atomic FAT transaction. */
typedef struct setup_document {
 prm_dos_image baseline,staged;
 char target[13];
 unsigned loaded,locked;
} setup_document;
typedef struct setup_document_result {
 unsigned status,bad_field;
 prm_dos_result io;
 prm_replace_result replacement;
} setup_document_result;
enum { SETUP_DOCUMENT_OK=0, SETUP_DOCUMENT_ARGUMENT, SETUP_DOCUMENT_LOAD,
 SETUP_DOCUMENT_INVALID, SETUP_DOCUMENT_CHANGED, SETUP_DOCUMENT_REPLACE,
 SETUP_DOCUMENT_LOCKED };
/* Leaf names only: ASCII letters/digits/_/- and an optional extension, 8.3.
 * Device names and reserved PRMEDIT.$$$ / PRMEDIT.BAK are rejected before I/O.
 * Failed open leaves document untouched. Invalid mapped fields can be opened
 * for explicit repair. No create, default fallback or implicit rewrite. */
unsigned __cdecl setup_document_open(const char *path,setup_document *document,
 setup_document_result *result);
unsigned __cdecl setup_document_save(setup_document *document,
 setup_document_result *result);
#endif
