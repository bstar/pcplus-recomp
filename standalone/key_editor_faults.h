enum {KF_NONE=0,KF_OPEN,KF_READ,KF_SHORT_READ,KF_CREATE,KF_WRITE,KF_SHORT_WRITE,
 KF_CLOSE_FIRST,KF_CLOSE_STAGE,KF_CLOSE_RECHECK,KF_CLOSE_BEFORE,KF_MOVE,KF_INSTALL,
 KF_ROLLBACK,KF_DELETE_BACKUP,KF_DELETE_STAGE,KF_STALE_RECHECK,KF_CREATE_RACE};
extern unsigned key_fault,key_calls,key_opens,key_closes,key_creates,key_renames,key_deletes;
extern int key_uncertain;
void key_fault_reset(unsigned);
void key_fault_cleanup(void);
