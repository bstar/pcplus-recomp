#include "directory_resource_owner.h"
#include "session_baseline.h"
#include "../directory/directory_resource_cli.h"
#include <dos.h>
#include <string.h>
extern unsigned __far __cdecl directory_resources_program_queue(void);
extern unsigned __far __cdecl directory_resources_defaults(unsigned char *);
extern unsigned char __far redisplay_snapshot[63000];
extern unsigned terminal_program_pending,terminal_program_active,terminal_program_kind,terminal_program_status;
extern unsigned redisplay_active,command_menu_active,connection_state,terminal_parser_active,terminal_tx_count;
extern unsigned process_psp;
#pragma aux redisplay_snapshot "redisplay_snapshot";
#pragma aux terminal_program_pending "terminal_program_pending";
#pragma aux terminal_program_active "terminal_program_active";
#pragma aux terminal_program_kind "terminal_program_kind";
#pragma aux terminal_program_status "terminal_program_status";
#pragma aux connection_state "connection_state";
#pragma aux terminal_parser_active "terminal_parser_active";
#pragma aux terminal_tx_count "terminal_tx_count";
#pragma aux process_psp "process_psp";
#define PROPOSAL ((const directory_selection_proposal __far *)(redisplay_snapshot+2788))
#define BUNDLE ((directory_resource_bundle __far *)(redisplay_snapshot+3978))
typedef struct actual_session {
 live_configuration_plan configuration;
 transfer_import_settings transfer;
} actual_session;
typedef struct preview_session {
 actual_session actual;
 unsigned proposal_seal,baseline_seal;
} preview_session;
#define PREVIEW ((preview_session __far *)(redisplay_snapshot+5602))
directory_resource_owner_snapshot terminal_directory_resources;
static unsigned cookie=0xd840;
typedef char dro_word_abi[sizeof(unsigned)==2?1:-1];
typedef char dro_snapshot_abi[sizeof(directory_resource_owner_snapshot)==14?1:-1];
typedef char dro_actual_abi[sizeof(actual_session)==694?1:-1];
typedef char dro_preview_abi[sizeof(preview_session)==698?1:-1];
static void initialize(void)
{if(cookie==0xd840){memset(&terminal_directory_resources,0,sizeof(terminal_directory_resources));cookie=0xd841;}}
static unsigned seal(const unsigned char __far *bytes,unsigned count)
{unsigned value=0xa953;while(count--){value=(value<<1)|(value>>15);value^=*bytes++;}return value;}
/* Keep the1264-byte accepted image off the resource-reading call stack. */
static unsigned accepted(unsigned *value)
{prm_dos_image image;unsigned status=hook_baseline_copy(&image);if(!status)*value=seal((const unsigned char __far *)&image,sizeof(image));return status;}
static unsigned current(void)
{
 actual_session actual;unsigned i,status;
 status=directory_resource_capture(&actual.configuration,&actual.transfer);
 if(status)return DRO_CONTEXT;
 for(i=0;i<sizeof(actual);++i)
  if(((const unsigned char *)&actual)[i]!=((const unsigned char __far *)&PREVIEW->actual)[i])return DRO_CHANGED;
 return 0;
}
unsigned __far __cdecl terminal_directory_resources_bind(const prm_dos_image *baseline,
 const live_configuration_plan *active,const transfer_import_settings *transfer)
{
 unsigned i;
 initialize();
 if(terminal_directory_resources.state!=DRO_IDLE || terminal_program_pending || terminal_program_active ||
  !redisplay_active || !command_menu_active)return DRO_CONTEXT;
 for(i=0;i<sizeof(*active);++i)((unsigned char __far *)&PREVIEW->actual.configuration)[i]=((const unsigned char *)active)[i];
 for(i=0;i<sizeof(*transfer);++i)((unsigned char __far *)&PREVIEW->actual.transfer)[i]=((const unsigned char *)transfer)[i];
 PREVIEW->proposal_seal=seal((const unsigned char __far *)PROPOSAL,sizeof(*PROPOSAL));
 PREVIEW->baseline_seal=seal((const unsigned char __far *)baseline,sizeof(*baseline));
 return 0;
}
unsigned __far __cdecl terminal_directory_resources_queued(void)
{return cookie==0xd841 && terminal_directory_resources.state==DRO_QUEUED;}
unsigned __far __cdecl terminal_directory_resources_queue(const directory_selection_proposal __far *proposal)
{
 unsigned status,baseline;
 initialize();
 if(cookie!=0xd841 || terminal_directory_resources.state!=DRO_IDLE || terminal_program_pending || terminal_program_active ||
  !redisplay_active || !command_menu_active || connection_state || terminal_parser_active)return DRO_BUSY;
 if(FP_SEG(proposal)!=FP_SEG(PROPOSAL) || FP_OFF(proposal)!=FP_OFF(PROPOSAL))return DRO_ARGUMENT;
 status=directory_resources_initialize();if(status)return DRO_RESOURCES;
 status=current();if(status)return status;
 status=accepted(&baseline);if(status)return DRO_BASELINE;
 terminal_directory_resources.proposal_seal=seal((const unsigned char __far *)PROPOSAL,sizeof(*PROPOSAL));
 if(terminal_directory_resources.proposal_seal!=PREVIEW->proposal_seal || baseline!=PREVIEW->baseline_seal)return DRO_CHANGED;
 terminal_directory_resources.baseline_seal=baseline;
 terminal_directory_resources.mask=terminal_directory_resources.detail=terminal_directory_resources.status=0;
 status=directory_resources_program_queue();
 if(status){terminal_directory_resources.status=DRO_BUSY;terminal_directory_resources.detail=status;return DRO_BUSY;}
 terminal_directory_resources.state=DRO_QUEUED;return 0;
}
unsigned __far __cdecl terminal_directory_resources_run(void)
{
 directory_resource_request request;
 unsigned char record[114],defaults[948];
 unsigned status,baseline,i;
 directory_resource_owner_snapshot *r=&terminal_directory_resources;
 if(cookie!=0xd841 || r->state!=DRO_QUEUED || terminal_program_pending || terminal_program_active!=1 ||
  terminal_program_kind!=6 || terminal_program_status!=2 || redisplay_active || command_menu_active ||
  connection_state || terminal_parser_active || terminal_tx_count)return DRO_CONTEXT;
 r->state=DRO_RUNNING;++r->attempts;
 if(seal((const unsigned char __far *)PROPOSAL,sizeof(*PROPOSAL))!=r->proposal_seal){r->status=DRO_CHANGED;goto failed;}
 status=accepted(&baseline);
 if(status){r->status=DRO_BASELINE;r->detail=status;goto failed;}
 if(baseline!=r->baseline_seal){r->status=DRO_CHANGED;goto failed;}
 if(PREVIEW->proposal_seal!=r->proposal_seal || PREVIEW->baseline_seal!=r->baseline_seal){r->status=DRO_CHANGED;goto failed;}
 status=current();if(status){r->status=status;goto failed;}
 for(i=0;i<114;++i)record[i]=PROPOSAL->context.selection.record[i];
 status=directory_resource_cli_request(record,PROPOSAL->configuration.serial.terminal_id,process_psp,&request);
 if(status){r->status=DRO_REQUEST;r->detail=status;goto failed;}
 status=directory_resources_defaults(defaults);
 if(status){r->status=DRO_DEFAULTS;r->detail=status;goto failed;}
 status=directory_resources_stage(&request,defaults,BUNDLE);
 if(status){r->status=DRO_RESOURCES;r->detail=status;goto failed;}
 r->mask=BUNDLE->mask;r->state=DRO_READY;return 0;
failed:
 r->state=DRO_FAILED;return r->status;
}
void __far __cdecl terminal_directory_resources_release(void)
{
 if(cookie!=0xd841)return;
 if(terminal_directory_resources.state==DRO_QUEUED || terminal_directory_resources.state==DRO_READY ||
  terminal_directory_resources.state==DRO_FAILED)terminal_directory_resources.state=DRO_IDLE;
}
