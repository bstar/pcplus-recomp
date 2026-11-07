/* Diagnostic-only faults at loader's real resident DOS kernel boundaries. */
#define CODE __based(__segname("_CODE"))
static unsigned CODE mode;
static unsigned CODE opens;
static unsigned CODE reads;
static unsigned CODE closes;
unsigned __cdecl meta_load_real_open(const char *,int *);
unsigned __cdecl meta_load_real_read(int,void __far *,unsigned,unsigned *);
unsigned __cdecl meta_load_real_close(int);
void __far __cdecl meta_load_fault(unsigned value){mode=value;opens=reads=closes=0;}
unsigned __far __cdecl meta_load_calls(unsigned what){return what==0?opens:what==1?reads:closes;}
unsigned __cdecl meta_load_fs_open(const char *p,int *h){++opens;return meta_load_real_open(p,h);}
unsigned __cdecl meta_load_fs_read(int h,void __far *p,unsigned n,unsigned *done)
{++reads;if(mode==1 && reads==1){*done=0;return 5;}if(mode==2 && reads==1 && n>1)--n;return meta_load_real_read(h,p,n,done);}
unsigned __cdecl meta_load_fs_close(int h)
{unsigned e;++closes;if(mode==4)return 5;e=meta_load_real_close(h);return e?e:mode==3?5:0;}
