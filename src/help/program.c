/* Source PCHELP consumer. The legacy process ABI and observed original UI
 * controls are retained; bounded resource/memory services are maintained. */
#include <dos.h>
#include <stdio.h>
#include <string.h>
#include "parent.h"
#include "document.h"
static help_parent_context parent;
static help_document document;
static help_cursor cursor;
static FILE *file;
static unsigned rows,page,topic,top,normal,bold,reverse;
static unsigned hit_topic,hit_line,hit_column,hit_length,hit_valid;
static unsigned topic_row=0xffff;
static unsigned edge_thumb;
static unsigned idle_cursor,idle_shape;
static unsigned __far *video;
static char query[56];
static unsigned HELP_DOC_CODE HELP_DOC_CALL read_at(void *cookie,unsigned long at,unsigned char *out,unsigned n,unsigned *got)
{
 (void)cookie;*got=0;
 if(fseek(file,(long)at,SEEK_SET))return 1;
 *got=(unsigned)fread(out,1,n,file);return ferror(file)?1:0;
}
static unsigned record(unsigned which,help_record *out)
{
 unsigned got;unsigned char raw[38];
 if(read_at(0,3UL+(unsigned long)which*38,raw,38,&got)||got!=38)return 1;
 return help_record_decode(raw,38,&document.header,document.bytes,out);
}
static unsigned next_line(void)
{
 unsigned status;do{status=help_cursor_step(&cursor);}while(status==HELP_DOC_PENDING);
 return status;
}
static unsigned geometry(void)
{
 return *(unsigned char __far *)MK_FP(0x40,0x49)==3 &&
  *(unsigned __far *)MK_FP(0x40,0x4a)==80 &&
  *(unsigned char __far *)MK_FP(0x40,0x62)==0 &&
  *(unsigned char __far *)MK_FP(0x40,0x84)+1==rows &&
  *(unsigned __far *)MK_FP(0x40,0x63)==0x3d4;
}
static void cell(unsigned row,unsigned col,unsigned ch,unsigned attr)
{if(row<rows&&col<80)video[row*80+col]=(attr<<8)|(ch&255);}
static void text(unsigned row,unsigned col,const char *s,unsigned attr)
{while(col<80&&*s)cell(row,col++,(unsigned char)*s++,attr);}
static void fill(unsigned row,unsigned left,unsigned right,unsigned ch,unsigned attr)
{unsigned i;for(i=left;i<=right&&i<80;++i)cell(row,i,ch,attr);}
static void footer(const char *s)
{fill(rows-1,0,79,' ',reverse);text(rows-1,(80-(unsigned)strlen(s))/2,s,reverse);}
static void set_cursor(unsigned position,unsigned shape)
{
 union REGS r;r.h.ah=1;r.x.cx=shape;int86(0x10,&r,&r);
 r.h.ah=2;r.x.bx=0;r.x.dx=position;int86(0x10,&r,&r);
}
static unsigned key(void)
{
 union REGS r;r.h.ah=0;int86(0x16,&r,&r);
 return r.h.al?r.h.al:r.x.ax;
}
static unsigned fold(unsigned c){return c>='a'&&c<='z'?c-32:c;}
static unsigned draw(void)
{
 help_record rec;unsigned r,i,status,thumb;char heading[48];
 if(!geometry()||record(topic,&rec))return 1;
 for(r=0;r<rows;++r){fill(r,0,79,' ',normal);cell(r,0,' ',reverse);cell(r,79,176,reverse);}
 fill(0,0,79,' ',reverse);text(0,1,rec.title,reverse);
 sprintf(heading,"%s On-line Help ",parent.title);text(0,66-(unsigned)strlen(parent.title),heading,reverse);
 footer("[\x18]  [\x19]  [PgUp]  [PgDn]  [Home]  [End]  [T]opics  [S]earch  [C]ontinue  [Esc]");
 cell(1,79,24,reverse);cell(rows-2,79,25,reverse);
 thumb=top?rows-3:2;
 if(rec.lines>page){
  if((unsigned long)top+page>=rec.lines)thumb=rows-3;
  else thumb=2+(unsigned)(((unsigned long)(page-2)*top&65535UL)/(rec.lines-page));
 }
 if(edge_thumb)thumb=edge_thumb==1?2:rows-3;
 cell(thumb,79,178,bold);
 if(help_cursor_begin(&cursor,&document,topic))return 1;
 r=0;
 while((unsigned long)cursor.number<(unsigned long)top+page){
  status=next_line();if(status==HELP_DOC_END)break;if(status!=HELP_DOC_LINE)return 1;
  if(cursor.number<=top)continue;
  ++r;
  for(i=0;i<77&&cursor.line[i];++i)cell(r,i+2,(unsigned char)cursor.line[i],
   hit_valid&&topic==hit_topic&&cursor.number-1==hit_line&&i>=hit_column&&i<hit_column+hit_length?bold:normal);
 }
 set_cursor(idle_cursor,idle_shape);return 0;
}
static void box(unsigned y,unsigned x,unsigned height,unsigned width)
{
 unsigned r;
 for(r=y;r<y+height+2;++r){fill(r,x,x+width+1,' ',reverse);cell(r,x,186,reverse);cell(r,x+width+1,186,reverse);}
 fill(y,x+1,x+width,205,reverse);fill(y+height+1,x+1,x+width,205,reverse);
 cell(y,x,201,reverse);cell(y,x+width+1,187,reverse);
 cell(y+height+1,x,200,reverse);cell(y+height+1,x+width+1,188,reverse);
}
static unsigned topics(void)
{
 unsigned choice=topic,height=rows*2/5,y=(rows-height-2)/2,start,k,i,attr;help_record rec;
 i=topic_row==0xffff?height/2-1:topic_row;
 start=choice<i?0:choice-i;
 for(;;){
  if(draw())return 1;box(y,22,height,34);
  for(i=0;i<height&&start+i<document.header.topics;++i){
   if(record(start+i,&rec))return 1;attr=start+i==choice?normal:reverse;
   fill(y+i+1,24,55,' ',attr);text(y+i+1,25,rec.title,attr);
  }
  footer("[\x18]  [\x19]  [PgUp]  [PgDn]  [Home]  [End]  [Enter]  [Esc]");
  set_cursor(0x64c8,idle_shape);
  k=key();if(!geometry())return 1;
  if(k==27)return draw();
  if(k==13){topic_row=choice-start;topic=choice;top=0;edge_thumb=0;hit_valid=0;return draw();}
  if(k==0x4700)choice=start=0;
  else if(k==0x4f00){choice=document.header.topics-1;start=choice>=height?choice-height+1:0;}
  else if(k==0x4800){if(choice)--choice;if(choice<start)start=choice;}
  else if(k==0x5000){if(choice+1<document.header.topics)++choice;if(choice>=start+height)start=choice-height+1;}
  else if(k==0x4900){choice=start>=height?start-height:0;start=choice;}
  else if(k==0x5100){if(start+height<document.header.topics){choice=start+height;start=choice;}}
 }
}
static unsigned locate(const char *line)
{
 unsigned i,j,n=(unsigned)strlen(query);
 for(i=0;line[i];++i){for(j=0;j<n&&line[i+j]&&fold((unsigned char)line[i+j])==fold((unsigned char)query[j]);++j){}
  if(j==n)return i+1;}
 return 0;
}
static unsigned search(unsigned continuing)
{
 unsigned which=continuing&&hit_valid?hit_topic:topic;
 unsigned first=which,line=continuing&&hit_valid?hit_line+1:0,status,column,k,permission=0;
 if(!query[0])return 0;
 for(;;){
  if(help_cursor_begin(&cursor,&document,which))return 1;
  for(;;){status=next_line();if(status==HELP_DOC_END)break;if(status!=HELP_DOC_LINE)return 1;
   if(cursor.number-1<line)continue;
   column=locate(cursor.line);
   if(column){topic=hit_topic=which;top=hit_line=cursor.number-1;edge_thumb=0;hit_column=column-1;
    hit_length=(unsigned)strlen(query);hit_valid=1;return draw();}
  }
  if(!permission){
   if(draw())return 1;
   {const char *prompt="Text not found \xc4\xc4 Continue searching in other topics? (Y/N) No";
    fill(rows-1,0,79,' ',reverse);text(rows-1,(83-(unsigned)strlen(prompt))/2,prompt,reverse);}
   set_cursor((rows-1)*256+70,idle_shape&~0x2000);
   k=fold(key());if(!geometry())return 1;
   if(k!='Y'){if(!continuing)query[0]=0;return draw();}permission=1;
  }
  if(++which==document.header.topics)which=0;
  if(which==first){hit_valid=0;if(!continuing)query[0]=0;return draw();}line=0;
 }
}
static unsigned new_search(void)
{
 unsigned y=(rows-4)/2,k,n=(unsigned)strlen(query),i;
 for(;;){
  if(draw())return 1;box(y,10,2,57);
  text(y+1,12,"Enter help text to be sought:",reverse);
  fill(y+2,12,66,' ',normal);text(y+2,12,query,normal);
  set_cursor((y+2)*256+12+n,idle_shape&~0x2000);
  k=key();if(!geometry())return 1;
  if(k==27)return draw();
  if(k==13){for(i=0;i<n;++i)query[i]=(char)fold((unsigned char)query[i]);return search(0);}
  if(k==8){if(n)query[--n]=0;}
  else if(k>=32&&k<127&&n<55){query[n++]=(char)k;query[n]=0;}
 }
}
static unsigned run(void)
{
 unsigned k,status=draw();help_record rec;
 while(!status){
  k=key();if(!geometry())return 1;if(k==27)return 0;
  if(record(topic,&rec))return 1;
  if(k==0x4700){top=0;edge_thumb=1;hit_valid=0;}
  else if(k==0x4f00){if((unsigned long)top+page<rec.lines){top=rec.lines-page;edge_thumb=0;}else edge_thumb=2;hit_valid=0;}
  else if(k==0x4800){if(top){--top;edge_thumb=0;}else edge_thumb=1;hit_valid=0;}
  else if(k==0x5000){if((unsigned long)top+page<rec.lines){++top;edge_thumb=0;}else edge_thumb=2;hit_valid=0;}
  else if(k==0x4900){if(top>page){top-=page;edge_thumb=0;}else{top=0;edge_thumb=1;}hit_valid=0;}
  else if(k==0x5100){if((unsigned long)top+page<rec.lines){top+=page;edge_thumb=0;}else edge_thumb=2;hit_valid=0;}
  else if(fold(k)=='T'){status=topics();continue;}
  else if(fold(k)=='S'){status=new_search();continue;}
  else if(fold(k)=='C'){status=search(1);continue;}
  status=draw();
 }
 return status;
}
#ifdef HELP_EMBEDDED
#include "embedded.h"
unsigned help_embedded_open(const char *path,const char *title,unsigned context,
 unsigned normal_attr,unsigned bold_attr,unsigned reverse_attr,const unsigned short *saved)
{
 unsigned status,saved_cursor,saved_shape,i;unsigned long bytes;long length;
 if(!path||!title||!saved||(unsigned long)(unsigned)saved+4000UL>65536UL||strlen(path)>=sizeof(parent.path)||strlen(title)>=sizeof(parent.title))return 2;
 memset(&parent,0,sizeof(parent));strcpy(parent.path,path);strcpy(parent.title,title);
 parent.context.topic=context;
 memset(&document,0,sizeof(document));memset(&cursor,0,sizeof(cursor));memset(query,0,sizeof(query));
 hit_topic=hit_line=hit_column=hit_length=hit_valid=top=edge_thumb=0;topic_row=0xffff;
 file=fopen(parent.path,"rb");if(!file)return 4;
 if(fseek(file,0,SEEK_END)){fclose(file);return 4;}length=ftell(file);
 if(length<0){fclose(file);return 4;}bytes=(unsigned long)length;
 status=help_document_begin(&document,read_at,0,bytes);
 while(status==HELP_DOC_PENDING)status=help_document_step(&document);
 if(status){fclose(file);return 5;}
 rows=*(unsigned char __far *)MK_FP(0x40,0x84)+1;
 if(rows!=25||!geometry()){fclose(file);return 6;}
 video=MK_FP(0xb800,0);saved_cursor=*(unsigned __far *)MK_FP(0x40,0x50);saved_shape=*(unsigned __far *)MK_FP(0x40,0x60);
 idle_cursor=saved_cursor;idle_shape=saved_shape|0x2000;page=rows-2;topic=help_topic_select(context,document.header.topics);
 normal=normal_attr&255;bold=bold_attr&255;reverse=reverse_attr&255;
 status=run();
 if(geometry()){for(i=0;i<2000;++i)video[i]=saved[i];set_cursor(saved_cursor,saved_shape);}else status=1;
 if(fclose(file))status=1;file=0;
 return status?8:0;
}
#else
int main(int argc,char **argv)
{
 unsigned status,segment=0,saved_cursor,saved_shape,i;unsigned long bytes;long length;
 unsigned __far *saved;
 if(argc!=3||strcmp(argv[1],"PCHELP"))return 2;
 if(help_parent_read_dos(argv[2],&parent))return 3;
 file=fopen(parent.path,"rb");if(!file)return 4;
 if(fseek(file,0,SEEK_END)){fclose(file);return 4;}length=ftell(file);
 if(length<0){fclose(file);return 4;}bytes=(unsigned long)length;
 status=help_document_begin(&document,read_at,0,bytes);
 while(status==HELP_DOC_PENDING)status=help_document_step(&document);
 if(status){fclose(file);return 5;}
 rows=*(unsigned char __far *)MK_FP(0x40,0x84)+1;
 if(rows<25||rows>50||!geometry()){fclose(file);return 6;}
 if(_dos_allocmem(rows*10,&segment)){fclose(file);return 7;}
 saved=MK_FP(segment,0);video=MK_FP(0xb800,0);
 for(i=0;i<rows*80;++i)saved[i]=video[i];
 saved_cursor=*(unsigned __far *)MK_FP(0x40,0x50);saved_shape=*(unsigned __far *)MK_FP(0x40,0x60);
 idle_cursor=saved_cursor;idle_shape=saved_shape|0x2000;
 page=rows-2;topic=help_topic_select(parent.context.topic,document.header.topics);
 normal=parent.context.ui_words[1]&255;bold=parent.context.ui_words[2]&255;reverse=parent.context.ui_words[3]&255;
 status=run();
 if(geometry()){for(i=0;i<rows*80;++i)video[i]=saved[i];set_cursor(saved_cursor,saved_shape);}
 else status=1;
 if(fclose(file))status=1;
 if(_dos_freemem(segment))status=1;
 return status?8:0;
}
#endif
