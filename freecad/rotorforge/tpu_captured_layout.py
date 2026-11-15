"""Pure layout for TPU cage captured inserts, including flush exterior lips.

The same axial intervals are used for the printable inserts and cage seats.
Coordinates are global X; the left/right sides mirror about the frame centre.
"""

def outside_lip_length(p):
    return max(.6,min(1.2,float(p.FlexInsertLip)))


def flush_outside(p):
    return (getattr(p,'CameraCageStyle','')=='TPU cage' and
            getattr(p,'FlexCameraMode','')=='Captured inserts' and
            bool(getattr(p,'CameraTPUFlushInserts',False)) and
            p.FlexInsertLipSide in ('Outside only','Both sides'))


def insert_x_spans(p,mount,sign):
    """Return neck and optional outside-lip spans for the actual cage wall.

    Flush removes *all* outward neck overhang, sinks the complete outside
    retaining flange into the wall, and leaves its outer face coplanar with
    the cage exterior. Off mode retains the original projecting flange.
    """
    a,b=map(float,mount['plate_x'])
    if not a<b or sign not in (-1,1):
        raise ValueError('Invalid TPU captured-insert wall limits.')
    flush=flush_outside(p)
    lip=outside_lip_length(p)
    if flush and b-a<lip+.8:
        raise ValueError('Flush TPU inserts need %.2f mm of side-wall stock; only %.2f mm is available. Increase wall width or disable flush exterior inserts.'%(lip+.8,b-a))
    if sign<0:
        neck=(a if flush else a-.45,b+.45)
        flange=(a,a+lip) if flush else (a-lip,a)
    else:
        neck=(a-.45,b if flush else b+.45)
        flange=(b-lip,b) if flush else (b,b+lip)
    return dict(neck=neck,flange=flange,flush=flush,lip=lip,
                outside=a if sign<0 else b,
                inside=b if sign<0 else a)


def flush_flange_cutter_span(p,mount,sign):
    """Cutter passes through the outside face, only to flange-seat depth.

    Slight axial clearance is deliberate. Radial print clearance belongs to
    the wider YZ profile of the seat and not to the insert itself.
    """
    span=insert_x_spans(p,mount,sign)
    if not span['flush']:
        return None
    a,b=span['flange']
    return (a-.06,b+.045) if sign<0 else (a-.045,b+.06)
