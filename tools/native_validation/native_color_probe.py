"""Read-only analysis of saved SDK frames; never changes a benchmark or its config."""
from pathlib import Path
import hashlib,math
import numpy as np
from PIL import Image
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def measurements(paths):
 images={k:np.asarray(Image.open(v).convert('RGB'),dtype=np.float32)/255 for k,v in paths.items()}
 if len({x.shape for x in images.values()})!=1:raise RuntimeError('Diagnostic frame sizes differ')
 def mask(key,ratio):
  im=images[key];return (im[:,:,0]>im[:,:,1]*ratio)&(im[:,:,2]>im[:,:,1]*ratio)&(im[:,:,0]>.2)&(im[:,:,2]>.2)
 baseline=mask('baseline',1.5);weak=mask('weak',1.5);strong=mask('strong',1.5);ws=mask('weak',3);ss=mask('strong',3)
 return {'baseline_default_pixels':int(baseline.sum()),'weak_default_pixels':int(weak.sum()),'strong_default_pixels':int(strong.sum()),
         'baseline_weak_overlap_ratio':float((baseline&weak).sum()/max(1,weak.sum())),
         'strong_stricter_pixels':int(ss.sum()),'weak_stricter_pixels':int(ws.sum()),
         'strong_footprint_retained_ratio':float(ss.sum()/max(1,strong.sum())),
         'stricter_diagnostic_coverage':float(1-ws.sum()/max(1,ss.sum())),
         'baseline_to_weak_changed_pixels':int((np.max(np.abs(images['baseline']-images['weak']),axis=2)>.04).sum())}
def verify_color_probe(c,root):
 if c.get('static_validation_passed') is not True or c.get('all_visible_meshes_resolve_preview_surface') is not True or c.get('manual_native_capture_review') is not True or c.get('benchmark_config_modified') is not False:
  raise RuntimeError('Color probe proof is incomplete')
 paths={k:Path(root)/v['path'] for k,v in c['captures'].items()}
 if set(paths)!={'baseline','weak','strong'} or any(sha(paths[k])!=v['sha256'] for k,v in c['captures'].items()):raise RuntimeError('Color capture bytes differ')
 m=measurements(paths)
 if m!=c['measurements']:raise RuntimeError('Independent color measurements differ')
 if m['strong_default_pixels']<5000 or m['weak_default_pixels']<=0 or abs(m['baseline_default_pixels']-m['weak_default_pixels'])/m['weak_default_pixels']>.05 or m['baseline_weak_overlap_ratio']<.9:
  raise RuntimeError('Source texture does not establish probe ambiguity')
 if m['strong_footprint_retained_ratio']<.98 or m['stricter_diagnostic_coverage']<.98:
  raise RuntimeError('Color diagnostic does not retain the control footprint')
 return m
