#include "get_runtime.h"
#include "get_context.h"
#include "runtime.h"
extern void __cdecl runtime_get_field_abort(void);
unsigned runtime_get_cursor(void)
{
 unsigned position=runtime_get_field_position();
 if(position==65535U){runtime_set_error(ASPECT_RUN_STATE);runtime_get_field_abort();}
 return position;
}
void runtime_get_adopt(unsigned row,unsigned column)
{
 unsigned position=runtime_get_cursor();
 /* Checked normal field retirement already adopted the parent cursor. The
  * recovered owner then repeats1BBE with the viewport origin added. Validate
  * that repeat instead of applying origin twice or sending stale coordinates. */
 if(row!=(position>>8) || column!=(position&255)+runtime_get_origin){
  runtime_set_error(ASPECT_RUN_STATE);runtime_get_field_abort();
 }
}
