#include "capture_reservation.h"
#ifdef CAPTURE_FIXED_RESERVATION
#include <string.h>
#define RESERVATION_BYTES 74
#else
#define RESERVATION_BYTES 8
#endif
capture_reservation_state capture_reservation={0,0,0};
typedef char cf_reservation_size[sizeof(capture_reservation)==RESERVATION_BYTES?1:-1];
unsigned __far __cdecl capture_file_reserve(capture_file_probe probe,void *context)
{
 unsigned conflict;
 if(capture_reservation.busy)return CF_BUSY;
 if(!probe)return CF_ARGUMENT;
 if(capture_reservation.probe && (capture_reservation.probe!=probe || capture_reservation.context!=context))return CF_BUSY;
 capture_reservation.busy=1;
 conflict=capture_file_probe_owners(probe,context);
#ifdef CAPTURE_FIXED_RESERVATION
 if(!conflict&&capture_reservation.fixed_owner)
  conflict=probe(capture_reservation.fixed_identity,context);
#endif
 capture_reservation.busy=0;
 if(conflict)return CF_BUSY;
 capture_reservation.probe=probe;capture_reservation.context=context;return CF_OK;
}
unsigned __far __cdecl capture_file_release(capture_file_probe probe,void *context)
{
 if(capture_reservation.busy)return CF_BUSY;
 if(!probe)return CF_ARGUMENT;
 if(capture_reservation.probe!=probe || capture_reservation.context!=context)return CF_STATE;
 capture_reservation.probe=0;capture_reservation.context=0;return CF_OK;
}
unsigned __far __cdecl capture_file_reserved(const char *identity)
{
 unsigned conflict;
 if(capture_reservation.busy)return 1;
#ifdef CAPTURE_FIXED_RESERVATION
 if(capture_reservation.fixed_owner&&!strcmp(identity,capture_reservation.fixed_identity))return 1;
#endif
 if(!capture_reservation.probe)return 0;
 capture_reservation.busy=1;
 conflict=capture_reservation.probe(identity,capture_reservation.context);
 capture_reservation.busy=0;return conflict!=0;
}
#ifdef CAPTURE_FIXED_RESERVATION
static unsigned __far __cdecl fixed_probe(const char *identity,void *candidate)
{return !strcmp(identity,(const char *)candidate);}
unsigned __far __cdecl capture_file_claim(const char *identity,void *owner)
{
 char candidate[64];unsigned n,c,conflict;
 if(capture_reservation.busy)return CF_BUSY;
 if(!owner||!capture_file_validate_path(identity,0))return CF_ARGUMENT;
 for(n=0;;++n){
  c=(unsigned char)identity[n];if(c>='a'&&c<='z')c-=32;if(c=='/')c='\\';
  candidate[n]=(char)c;if(!c)break;
 }
 if(n<4||candidate[0]<'A'||candidate[0]>'Z'||candidate[1]!=':'||candidate[2]!='\\')return CF_ARGUMENT;
 if(capture_reservation.fixed_owner&&capture_reservation.fixed_owner!=owner)return CF_BUSY;
 capture_reservation.busy=1;
 conflict=capture_file_probe_owners(fixed_probe,candidate);
 if(!conflict&&capture_reservation.probe)conflict=capture_reservation.probe(candidate,capture_reservation.context);
 capture_reservation.busy=0;
 if(conflict)return CF_BUSY;
 memcpy(capture_reservation.fixed_identity,candidate,n+1);capture_reservation.fixed_owner=owner;
 return CF_OK;
}
unsigned __far __cdecl capture_file_unclaim(void *owner)
{
 if(capture_reservation.busy)return CF_BUSY;
 if(!owner)return CF_ARGUMENT;
 if(capture_reservation.fixed_owner!=owner)return CF_STATE;
 capture_reservation.fixed_owner=0;memset(capture_reservation.fixed_identity,0,64);
 return CF_OK;
}
#endif
