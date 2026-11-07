; Transient Meta bank ABI: explicit stack words and Watcom register imports.
; DS=SS throughout. Names/targets below describe the diagnostic resident C
; build (-ecc); production bindings must adapt its actual helper conventions.
META_ENTRY _meta_editor_open,10
META_ENTRY _meta_editor_key,3
META_ENTRY _meta_editor_step,3
META_ENTRY _meta_editor_draw,5
META_ENTRY _meta_editor_cursor,2
META_ENTRY _meta_editor_shape,2
META_ENTRY _meta_editor_stop,2
META_ENTRY _meta_editor_matches,6
META_ENTRY _meta_editor_proposal,8
META_REGISTER meta_bank_memcpy_, memcpy_
META_REGISTER meta_bank_memset_, memset_
META_REGISTER meta_bank_memcmp_, memcmp_
META_REGISTER meta_bank_strchr_, strchr_
META_REGISTER meta_bank_strcmp_, strcmp_
META_REGISTER meta_bank_strlen_, strlen_
META_COUNT meta_bank_fmemcpy_, _fmemcpy_
META_REGISTER meta_bank_fmemset_, _fmemset_
META_COUNT meta_bank_fmemcmp_, _fmemcmp_
META_REGISTER meta_bank_fstrcmp_, _fstrcmp_
META_CDECL _meta_bank_canonical, _capture_fs_canonical,2
META_CDECL _meta_bank_attributes, _capture_fs_attributes,2
META_CDECL _meta_bank_paths, _directory_replace_paths,3
META_CDECL _meta_bank_resource, _resource_pcplus_path,3
META_CDECL _meta_bank_actions, _key_actions_dos_read,3
