#include "viewer_external.h"
#include <dos.h>
typedef unsigned long linear;
static linear address(const void __far *p)
{return ((linear)FP_SEG(p)<<4)+FP_OFF(p);}
static unsigned span(const void __far *p,unsigned n)
{return p&&n&&n-1<=0xffffU-FP_OFF(p)&&address(p)<=0xfffffUL-(n-1);}
static unsigned overlap(const void __far *a,unsigned an,const void __far *b,unsigned bn)
{return address(a)<address(b)+bn&&address(b)<address(a)+an;}
unsigned __far __cdecl viewer_external_build(const unsigned char __far *prm,
 const char __far *parameters,char __far *command,unsigned capacity,unsigned __far *length)
{
 unsigned n,i,m,total;
 if(!span(prm,1264)||!span(parameters,VIEWER_EXTERNAL_PARAMETER_BYTES)||
    !capacity||capacity>VIEWER_EXTERNAL_COMMAND_BYTES||!span(command,capacity)||!span(length,2)||
    overlap(command,capacity,prm,1264)||overlap(command,capacity,parameters,VIEWER_EXTERNAL_PARAMETER_BYTES)||
    overlap(length,2,prm,1264)||overlap(length,2,parameters,VIEWER_EXTERNAL_PARAMETER_BYTES)||
    overlap(command,capacity,length,2))return VEXT_ARGUMENT;
 for(n=0;n<VIEWER_EXTERNAL_CONFIG_BYTES&&prm[VIEWER_EXTERNAL_PRM_OFFSET+n];++n){}
 if(n==VIEWER_EXTERNAL_CONFIG_BYTES)return VEXT_CONFIG;
 if(!n)return VEXT_DISABLED;
 for(m=0;m<VIEWER_EXTERNAL_PARAMETER_BYTES&&parameters[m];++m){}
 if(m==VIEWER_EXTERNAL_PARAMETER_BYTES)return VEXT_PARAMETERS;
 total=n+1+m;if(total+1>capacity)return VEXT_CAPACITY;
 for(i=0;i<n;++i)command[i]=(char)prm[VIEWER_EXTERNAL_PRM_OFFSET+i];
 command[n]=' ';for(i=0;i<m;++i)command[n+1+i]=parameters[i];
 command[total]=0;*length=total;return VEXT_OK;
}
