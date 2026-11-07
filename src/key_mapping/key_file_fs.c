#include <dos.h>
#include "key_file_fs.h"
#include "../directory/directory_replace_fs.h"
unsigned key_file_attr(const char *p,unsigned *a){return _dos_getfileattr(p,a);}
unsigned key_file_open(const char *p,unsigned m,int *h){return _dos_open(p,m,h);}
unsigned key_file_create(const char *p,unsigned a,int *h){return _dos_creatnew(p,a,h);}
unsigned key_file_read(int h,void *p,unsigned n,unsigned *c){return _dos_read(h,p,n,c);}
unsigned key_file_write(int h,const void *p,unsigned n,unsigned *c){return _dos_write(h,p,n,c);}
unsigned key_file_close(int h){return _dos_close(h);}
unsigned key_file_rename(const char *a,const char *b){return directory_replace_rename(a,b);}
unsigned key_file_delete(const char *p){return directory_replace_delete(p);}
