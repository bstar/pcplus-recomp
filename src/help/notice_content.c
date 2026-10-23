/* Authored maintained help. No copied vendor help resource or prose. */
#include "notice_content.h"
const help_page notice_help_pages[2]={
 {"EXTERNAL PROGRAM / ERROR NOTICE",{
  "The command could not run. Check its DOS filename and PATH setting.",
  "A missing program can also mean that its drive is not available.",
  "Invalid executable format: verify that the file is a DOS program.",
  "Insufficient memory: reduce other resident programs before retrying.",
  "",
  "Enter or Escape returns from this help view to the error notice.",
  "A second Enter or Escape dismisses the notice itself.",
  "The notice timer pauses while this help view is open.",
  "",
  "Use Left/Right for the serial-session topic.",0}},
 {"SERIAL SESSION / LOCAL INPUT",{
  "Serial receive and flow control continue while help is displayed.",
  "Incoming display bytes remain queued until the notice gives up its view.",
  "This bounded queue cannot store an unlimited incoming stream.",
  "",
  "Help keys are local. They are not transmitted to the remote system.",
  "The selected standard or enhanced BIOS keyboard mode remains in use.",
  "Mouse direction events select topics; Enter/Escape returns to the notice.",
  "The serial modem connection remains under the current session's control.",
  "",
  "Escape closes help. The next queued key still belongs to the notice.",0}}
};
