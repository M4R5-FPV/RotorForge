"""Z-buffer render of exact native reference meshes in the guide palette."""
from pathlib import Path
import sys,json,math,numpy as np
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[1];scenes=json.loads(Path(sys.argv[1]).read_text())
W,H=1900,700*((len(scenes)+1)//2);canvas=np.full((H,W,3),255,dtype=np.uint8)
for i,scene in enumerate(scenes):
 tri=np.array([v['points'] for v in scene['triangles']]);col=np.array([v['colour'] for v in scene['triangles']])
 eye=np.array([.8,1.1,.9]) if 'LiPo' in scene['title'] else np.array([.8,-1.1,.9]) if i!=3 else np.array([.8,1.1,.6]);eye/=np.linalg.norm(eye)
 right=np.cross([0,0,1],eye);right/=np.linalg.norm(right);up=np.cross(eye,right);basis=np.array([right,up,eye]);xyz=tri@basis.T
 lo=xyz[:,:,:2].min(axis=(0,1));hi=xyz[:,:,:2].max(axis=(0,1));centre=(hi+lo)/2;scale=min(800/(hi[0]-lo[0]),530/(hi[1]-lo[1]))
 xyz[:,:,:2]-=centre;xyz[:,:,:2]*=scale;xyz[:,:,0]+=i%2*950+475;xyz[:,:,1]*=-1;xyz[:,:,1]+=i//2*700+380
 n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-10);light=np.array([.3,.4,.86]);shade=.68+.32*np.abs(n@light);rgb=np.clip((col*shade[:,None]+.025)*255,0,255).astype(np.uint8)
 depth=np.full((H,W),-np.inf)
 for t,c in zip(xyz,rgb):
  xmin=max(0,int(np.floor(t[:,0].min())));xmax=min(W-1,int(np.ceil(t[:,0].max())));ymin=max(0,int(np.floor(t[:,1].min())));ymax=min(H-1,int(np.ceil(t[:,1].max())))
  if xmin>xmax or ymin>ymax:continue
  a,b,d=t;den=(b[1]-d[1])*(a[0]-d[0])+(d[0]-b[0])*(a[1]-d[1])
  if abs(den)<1e-9:continue
  X,Y=np.meshgrid(np.arange(xmin,xmax+1)+.5,np.arange(ymin,ymax+1)+.5)
  u=((b[1]-d[1])*(X-d[0])+(d[0]-b[0])*(Y-d[1]))/den
  v=((d[1]-a[1])*(X-d[0])+(a[0]-d[0])*(Y-d[1]))/den;w=1-u-v;z=u*a[2]+v*b[2]+w*d[2]
  buf=depth[ymin:ymax+1,xmin:xmax+1];mask=(u>=-1e-8)&(v>=-1e-8)&(w>=-1e-8)&(z>buf);buf[mask]=z[mask];canvas[ymin:ymax+1,xmin:xmax+1][mask]=c
im=Image.fromarray(canvas);draw=ImageDraw.Draw(im);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',32)
for i,s in enumerate(scenes):draw.text((i%2*950+475,i//2*700+30),s['title'],font=font,fill='#262a2f',anchor='mt')
im.save(root/'docs'/(sys.argv[2] if len(sys.argv)>2 else 'DetailedReferences.png'))
