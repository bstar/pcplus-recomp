/* Explicit host-only clock boundary for date/time/date rollover checks. */
#define __cdecl
#include "../src/directory/phone_log_clock.h"
static unsigned scenario,dates,times;
void phone_clock_model(unsigned value){scenario=value;dates=times=0;}
unsigned phone_clock_dates(void){return dates;}
unsigned phone_clock_times(void){return times;}
void phone_log_clock_date(unsigned *year,unsigned *month,unsigned *day)
{
 unsigned first=dates++;
 if(scenario==1&&first==0){*year=1999;*month=12;*day=31;return;}
 if(scenario==2&&!(first&1)){*year=1999;*month=12;*day=31;return;}
 *year=scenario==3?2100:2000;*month=*day=1;
}
void phone_log_clock_time(unsigned *hour,unsigned *minute,unsigned *second)
{++times;*hour=*minute=0;*second=5;}
