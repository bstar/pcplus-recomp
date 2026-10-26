; Each role keeps a full4000-byte snapshot. Only proven mutually exclusive
; screen owners may share physical cells; their entry guards are bidirectional.
%ifndef PCPLUS_UI_STORAGE_POLICY
%define PCPLUS_UI_STORAGE_POLICY
%ifdef TERMINAL_NATIVE_RESET_OVERLAY
%define TERMINAL_UI_SCREEN_OVERLAY
%elifdef TERMINAL_DIRECTORY_VIEW
%define TERMINAL_UI_SCREEN_OVERLAY
%endif
%endif
