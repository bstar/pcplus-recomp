#!/usr/bin/env python3
"""Run the download auditor under its canonical fixture-bound module name.

Fixture binding refreshes imported module globals. Running that module as
__main__ creates a second namespace which cannot receive those refreshes.
The auditor itself, captures and acceptance checks are unchanged.
"""
from audit_audio_download import main

if __name__ == '__main__':
    main()
