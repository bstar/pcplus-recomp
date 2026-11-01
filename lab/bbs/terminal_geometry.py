"""Read coherent initial screen geometry from a validated source-built MZ/map."""
import re
import struct
from pathlib import Path
from product_inputs import sha

def terminal_geometry(binary):
    binary=Path(binary);data=binary.read_bytes();listing=binary.parent/'terminal.map'
    symbols={n:(int(seg,16),int(off,16)) for seg,off,n in re.findall(r'^([0-9a-f]{4}):([0-9a-f]{4})[*+ ]+\s+(\w+)\s*$',listing.read_text(),re.M|re.I)}
    assert data[:2]==b'MZ'
    header=struct.unpack_from('<14H',data);start=header[4]*16
    size=(header[2]-1)*512+(header[1] or 512)
    assert start<size<=len(data)
    values={};offsets={}
    for name in ['csi_column_count','csi_row_count','csi_last_row','screen_first_row','screen_last_row','csi_origin_bottom','erase_cell_count','ui_flow_video_base','ui_flow_suppressed']:
        seg,off=symbols[name];at=start+seg*16+off
        assert start<=at and at+2<=size
        offsets[name]=at;values[name]=struct.unpack_from('<H',data,at)[0]
    rows=values['csi_row_count'];cols=values['csi_column_count']
    assert cols==80 and rows in (24,25) and values['screen_first_row']==0
    assert values['csi_last_row']==values['screen_last_row']==values['csi_origin_bottom']==rows-1
    assert values['erase_cell_count']==cols*rows and values['ui_flow_video_base']==3840 and values['ui_flow_suppressed']==0
    return dict(columns=cols,rows=rows,values=values,file_offsets=offsets,binary_sha256=sha(binary),map_sha256=sha(listing))
