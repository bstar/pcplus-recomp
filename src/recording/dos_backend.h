#ifndef PCPLUS_RECORDING_DOS_BACKEND_H
#define PCPLUS_RECORDING_DOS_BACKEND_H
#include "file.h"
/* Kernel and canonical-owner adapters. A production owner supplies a stable
 * zero-initialized recording_file and uses this table; it publishes no stdio
 * FILE and never exposes an inherited file handle to a script child. */
extern recording_file_ops recording_dos_ops;
#endif
