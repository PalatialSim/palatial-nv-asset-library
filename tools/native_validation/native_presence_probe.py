"""Independent evidence for presence-only SDK camera framing findings."""
from pathlib import Path
import hashlib,math
import numpy as np
from PIL import Image

def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def measurements(paths):
 values={}
 shapes=[]
 for key,path in paths.items():
  p=np.asarray(Image.open(path).convert('RGB'),dtype=np.float32)/255
  shapes.append(p.shape)
  # The SDK's orange control has red and green over blue. Requiring red
  # to dominate green instead rejects the lit yellow-orange highlight.
  mask=(p[:,:,0]>.2)&(p[:,:,1]>.2)&(p[:,:,0]>=p[:,:,1])&(p[:,:,0]>p[:,:,2]*1.5)&(p[:,:,1]>p[:,:,2]*1.5)
  values[key+'_orange_pixels']=int(mask.sum())
 if len(set(shapes))!=1:raise RuntimeError('Presence frame dimensions differ')
 return values

def verify_presence_probe(c,root):
 dims=c['actual_visible_bounds_size_m']
 if len(dims)!=3 or not all(0<float(v)<.1 for v in dims) or math.sqrt(sum(float(v)**2 for v in dims))>=.1:
  raise RuntimeError('Source dimensions do not establish the camera minimum issue')
 if c.get('static_validation_passed') is not True or c.get('manual_native_capture_review') is not True or c.get('benchmark_config_modified') is not False or len(c.get('sdk_camera_source_sha256',''))!=64:
  raise RuntimeError('Presence framing proof is incomplete')
 if not 0<c['presence_diff_ratio']<.01 or c['semantic_labels_on_coverage']<.005 or c['silhouette_pixels']<5000 or c['preview_surface_coverage']<.98:
  raise RuntimeError('Independent SDK semantic and surface checks must pass')
 paths={k:Path(root)/v['path'] for k,v in c['captures'].items()}
 if set(paths)!={'visible','hidden'} or any(sha(paths[k])!=v['sha256'] for k,v in c['captures'].items()):raise RuntimeError('Presence capture bytes differ')
 m=measurements(paths)
 if m!=c['measurements'] or m['visible_orange_pixels']<5000 or m['hidden_orange_pixels']>m['visible_orange_pixels']*.01:
  raise RuntimeError('Orange visibility toggle does not independently establish visible geometry')
 return m
