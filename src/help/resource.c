#include "resource.h"
#include "document.h"
extern unsigned __cdecl help_file_open(const char *,unsigned *);
extern unsigned __cdecl help_file_close(unsigned);
extern unsigned __cdecl help_file_size(unsigned,unsigned long *);
extern unsigned __cdecl help_file_read(unsigned,unsigned long,unsigned char *,unsigned,unsigned *);
enum {R_ADMIT=1,R_PAGE,R_LOAD,R_READY,R_EDIT,R_FIND,R_ERROR};
static struct {
 unsigned owned,handle,phase,topic,top,next_top,active,stage,rows,footer,query_size,hit_topic;
 unsigned long hit_position;
 help_document document;help_cursor cursor;help_find find;
 help_page page[2];char titles[2][33],lines[2][17][75],footers[2][75],query[32];
} held;
static const help_page loading={"READING HELP RESOURCE",{"The serial session remains active. Escape returns to the notice.",0}};
static const char footer[]="Left/Right: topic  Up/Down PgUp/PgDn: scroll  /: find  F3: next  Esc";
static void copy(char *to,const char *from,unsigned maximum)
{unsigned i;for(i=0;i<maximum&&from[i];++i)to[i]=from[i];to[i]=0;}
static unsigned HELP_DOC_CODE HELP_DOC_CALL read_at(void *cookie,unsigned long offset,unsigned char *out,unsigned bytes,unsigned *got)
{(void)cookie;return help_file_read(held.handle,offset,out,bytes,got);}
static unsigned show_footer(const char *text)
{
 held.footer^=1;copy(held.footers[held.footer],text,74);
 return help_view_update(&held.page[held.active],held.footers[held.footer]);
}
static unsigned error_page(void)
{
 unsigned b=held.active^1,i;
 copy(held.titles[b],"HELP RESOURCE ERROR",32);held.page[b].title=held.titles[b];
 for(i=0;i<17;++i){held.lines[b][i][0]=0;held.page[b].lines[i]=held.lines[b][i];}
 copy(held.lines[b][0],"The help file is damaged, changed or could not be read.",74);
 copy(held.lines[b][2],"Escape returns to the notice. Check LOCHELP.HLP from DOS.",74);
 held.active=b;held.phase=R_ERROR;
 return help_view_update(&held.page[b],"Esc or Enter: return to the notice");
}
static void request_page(unsigned topic,unsigned top)
{held.topic=topic;held.top=top;held.phase=R_PAGE;}
static unsigned begin_find(unsigned repeat)
{
 unsigned status;
 if(!held.query_size){held.phase=R_READY;return show_footer(footer);}
 status=help_find_begin(&held.find,&held.document,held.query,repeat?held.hit_topic:held.topic,repeat?held.hit_position:0);
 if(status!=HELP_DOC_PENDING)return error_page();
 held.phase=R_FIND;return show_footer("Searching... Escape cancels; the serial session remains active.");
}
unsigned __far __cdecl help_resource_active(void){return held.owned;}
unsigned __far __cdecl help_resource_close(void)
{
 unsigned status;
 if(!held.owned)return HELP_VIEW_OK;
 help_find_cancel(&held.find);status=help_file_close(held.handle);
 if(status)return HELP_VIEW_STATE;
 held.owned=held.phase=held.query_size=0;held.document.phase=0;return HELP_VIEW_OK;
}
unsigned __far __cdecl help_resource_open(const char *path)
{
 unsigned status,i;unsigned long bytes;
 if(held.owned||help_view_active())return HELP_VIEW_STATE;
 status=help_file_open(path,&held.handle);
 if(status)return status==2||status==3?HELP_RESOURCE_MISSING:HELP_VIEW_STATE;
 held.owned=1;held.phase=R_ADMIT;held.topic=held.top=held.active=held.stage=held.footer=held.query_size=0;
 held.hit_topic=0;held.hit_position=0;held.query[0]=0;
 for(i=0;i<2;++i)held.page[i]=loading;
 status=help_view_open(&loading,1,0);
 if(status){if(help_resource_close())return HELP_VIEW_STATE;return status;}
 status=help_file_size(held.handle,&bytes);
 if(!status)status=help_document_begin(&held.document,read_at,0,bytes);
 if(status!=HELP_DOC_PENDING)return error_page();
 return HELP_VIEW_OK;
}
unsigned __far __cdecl help_resource_step(void)
{
 unsigned status,i,b,length;unsigned long next;
 if(!held.owned)return HELP_VIEW_STATE;
 if(held.phase==R_ADMIT){
  status=help_document_step(&held.document);
  if(status==HELP_DOC_OK)request_page(0,0);
  else if(status!=HELP_DOC_PENDING)return error_page();
 }else if(held.phase==R_PAGE){
  status=help_cursor_begin(&held.cursor,&held.document,held.topic);if(status)return error_page();
  if(held.top>=held.cursor.record.lines)held.top=held.cursor.record.lines?held.cursor.record.lines-1:0;
  b=held.active^1;held.stage=b;held.rows=0;held.next_top=held.top;
  copy(held.titles[b],held.cursor.record.title,32);held.page[b].title=held.titles[b];
  for(i=0;i<17;++i){held.lines[b][i][0]=0;held.page[b].lines[i]=held.lines[b][i];}
  held.phase=R_LOAD;
 }else if(held.phase==R_LOAD){
  status=help_cursor_step(&held.cursor);b=held.stage;
  if(status==HELP_DOC_LINE&&held.cursor.number>held.top){
   copy(held.lines[b][held.rows++],held.cursor.line,74);
   for(length=0;held.cursor.line[length];++length){}
   held.next_top=held.cursor.number;
   if(length>74){
    if(held.rows<17)copy(held.lines[b][held.rows++],held.cursor.line+74,74);
    else held.next_top=held.cursor.number-1;
   }
  }else if(status!=HELP_DOC_LINE&&status!=HELP_DOC_PENDING&&status!=HELP_DOC_END)return error_page();
  if(held.rows==17||status==HELP_DOC_END){held.active=b;held.phase=R_READY;return help_view_update(&held.page[b],footer);}
 }else if(held.phase==R_FIND){
  status=help_find_step(&held.find);
  if(status==HELP_DOC_FOUND){
   held.hit_topic=held.find.match_topic;held.hit_position=(unsigned long)held.find.match_line+1;
   next=held.find.match_line?held.find.match_line-1:0;request_page(held.hit_topic,(unsigned)next);
  }else if(status==HELP_DOC_END){held.phase=R_READY;return show_footer("No matching text. / changes the search; Escape returns.");}
  else if(status!=HELP_DOC_PENDING)return error_page();
 }
 return HELP_VIEW_OK;
}
unsigned __far __cdecl help_resource_key(unsigned key)
{
 unsigned c=key&255,topic=held.topic,top=held.top,last;
 char prompt[40];
 if(!held.owned)return HELP_VIEW_STATE;
 if(held.phase==R_EDIT){
  if(c==27){held.phase=R_READY;return show_footer(footer);}
  if(c==13)return begin_find(0);
  if(c==8){if(held.query_size)held.query[--held.query_size]=0;}
  else if(c>=32&&c<127&&held.query_size<31){held.query[held.query_size++]=(char)c;held.query[held.query_size]=0;}
  copy(prompt,"Find: ",6);copy(prompt+6,held.query,31);return show_footer(prompt);
 }
 if(held.phase==R_FIND){if(c==27){help_find_cancel(&held.find);held.phase=R_READY;return show_footer(footer);}return HELP_VIEW_OK;}
 if(c==27||c==13||key==0x2c00)return HELP_RESOURCE_CLOSE;
 if(held.phase!=R_READY)return HELP_VIEW_OK;
 if(c=='/'){held.phase=R_EDIT;held.query_size=0;held.query[0]=0;return show_footer("Find: ");}
 if(key==0x3d00)return begin_find(1);
 last=held.cursor.record.lines?held.cursor.record.lines-1:0;
 if(key==0x4b00){topic=topic?topic-1:held.document.header.topics-1;top=0;}
 else if(key==0x4d00||c=='t'||c=='T'){if(++topic==held.document.header.topics)topic=0;top=0;}
 else if(key==0x4800){if(top)--top;}
 else if(key==0x5000){if(top<last)++top;}
 else if(key==0x4900)top=top>17?top-17:0;
 else if(key==0x5100){top=held.next_top>top?held.next_top:top<last?top+1:top;if(top>last)top=last;}
 else if(key==0x4700)top=0;
 else if(key==0x4f00)top=last;
 if(topic!=held.topic||top!=held.top){held.hit_topic=topic;held.hit_position=(unsigned long)top+1;request_page(topic,top);}
 return HELP_VIEW_OK;
}
