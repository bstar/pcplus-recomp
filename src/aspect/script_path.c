#include "script_path.h"
#include <string.h>
unsigned aspect_script_path(const char *input,char *output)
{
    char staged[ASPECT_SCRIPT_PATH_CAPACITY];
    unsigned n,leaf=0,stem,suffix,result;
    if(!input || !*input)return ASPECT_SCRIPT_PATH_EMPTY;
    if(!output)return ASPECT_SCRIPT_PATH_INVALID;
    for(n=0;n<=80 && input[n];++n){
        unsigned char ch=(unsigned char)input[n];
        staged[n]=(char)((ch>='a' && ch<='z')?ch-('a'-'A'):ch);
        if(ch=='\\' || ch==':')leaf=n+1;
    }
    if(n>80)return ASPECT_SCRIPT_PATH_SIZE;
    staged[n]=0;
    for(stem=0;stem<8 && staged[leaf+stem] && staged[leaf+stem]!='.';++stem){}
    if(!stem)return ASPECT_SCRIPT_PATH_INVALID;
    suffix=leaf+stem;
    if(!staged[suffix]){
        if(n+4>=ASPECT_SCRIPT_PATH_CAPACITY)return ASPECT_SCRIPT_PATH_SIZE;
        memcpy(staged+n,".ASX",5);
        n+=4;result=ASPECT_SCRIPT_PATH_COMPILED;
    }else if(!strcmp(staged+suffix,".ASX"))result=ASPECT_SCRIPT_PATH_COMPILED;
    else if(!strcmp(staged+suffix,".ASP"))result=ASPECT_SCRIPT_PATH_SOURCE;
    else return ASPECT_SCRIPT_PATH_INVALID;
    memcpy(output,staged,n+1);
    return result;
}
