#include "capture_reservation.h"
capture_reservation_state capture_reservation={0,0,0};
typedef char cf_reservation_size[sizeof(capture_reservation)==8?1:-1];
unsigned __far __cdecl capture_file_reserve(capture_file_probe probe,void *context)
{
 unsigned conflict;
 if(capture_reservation.busy)return CF_BUSY;
 if(!probe)return CF_ARGUMENT;
 if(capture_reservation.probe && (capture_reservation.probe!=probe || capture_reservation.context!=context))return CF_BUSY;
 capture_reservation.busy=1;
 conflict=capture_file_probe_owners(probe,context);
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
 if(!capture_reservation.probe)return 0;
 capture_reservation.busy=1;
 conflict=capture_reservation.probe(identity,capture_reservation.context);
 capture_reservation.busy=0;return conflict!=0;
}
