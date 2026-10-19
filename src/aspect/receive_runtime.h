#ifndef PCPLUS_ASPECT_RECEIVE_RUNTIME_H
#define PCPLUS_ASPECT_RECEIVE_RUNTIME_H
void runtime_receive_reset(void);
void runtime_receive_begin(unsigned mode);
void runtime_receive_note_byte(unsigned value);
unsigned runtime_receive_character(unsigned echo,unsigned delayed);
#if defined(ASPECT_RUNTIME_DIAGNOSTIC)
void runtime_receive_fixture(unsigned seconds,unsigned step);
unsigned runtime_receive_seconds(void);
#endif
#endif
