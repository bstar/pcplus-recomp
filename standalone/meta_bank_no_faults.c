/* Direct-kernel diagnostic compatibility with the shared workflow driver.
 * No intercepted file calls, injected errors or call-count claim in this mode. */
unsigned key_calls;
void key_fault_reset(unsigned fault){(void)fault;key_calls=0;}
