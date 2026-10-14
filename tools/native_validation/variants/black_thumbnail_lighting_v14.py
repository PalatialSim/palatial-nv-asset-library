"""Palatial artifact generation; supplements, never replaces, NVIDIA tests."""
from simready_benchmark.core.decorator import test


@test(
    features=[{'id': 'FET_001_STANDARD', 'version': '>=0.1.0'}],
    name='palatial_black_thumbnail',
    description='Renders the authored asset materials against a black background and saves its 256 px package thumbnail.',
    expected_video='The complete asset is framed with its authored materials, surrounded by black pixels.',
    version='1.4.0', engine={'tags': ['kit'], 'version': '>=2024.2.0'},
    config_defaults={'capture_width': 1024, 'capture_height': 1024},
    max_duration=120,
)
async def black_thumbnail(ctx):
    import hashlib
    from pathlib import Path
    import numpy as np
    from PIL import Image
    from pxr import Sdf,Gf,Usd,UsdGeom,UsdLux
    import omni.usd

    ctx.scene.load_asset(ctx.asset_path)
    ctx.scene.lighting.add_directional(direction=(45, 0, 90), intensity=12000)
    ctx.scene.lighting.add_directional(direction=(45, 0, -90), intensity=3200)
    dome = ctx.scene.lighting.add_dome(intensity=600)
    stage = omni.usd.get_context().get_stage()
    stage.GetPrimAtPath(dome.prim_path).CreateAttribute('visibleInPrimaryRay', Sdf.ValueTypeNames.Bool).Set(False)
    await ctx.settle(count=5)
    # Frame the real visible bounds. The engine helper clamps each dimension
    # to 10 cm, which makes correctly sized small props nearly disappear.
    asset=stage.GetPrimAtPath(ctx.scene.asset.prim_path)
    cache=UsdGeom.BBoxCache(Usd.TimeCode.Default(),[UsdGeom.Tokens.default_,UsdGeom.Tokens.render])
    bounds=Gf.Range3d()
    for prim in Usd.PrimRange(asset):
        if prim.IsA(UsdGeom.Mesh) and UsdGeom.Imageable(prim).ComputeVisibility()!=UsdGeom.Tokens.invisible:
            bounds.UnionWith(cache.ComputeWorldBound(prim).ComputeAlignedRange())
    if bounds.IsEmpty():
        ctx.fail('No visible authored mesh bounds for thumbnail')
        return
    center=bounds.GetMidpoint();size=bounds.GetSize()
    diagonal=max(float(size.GetLength()),1e-6)
    distance=diagonal*1.3/(36.0/35.0)
    eye=center+Gf.Vec3d(0.3,0.8,0.4).GetNormalized()*distance
    ctx.scene.set_camera(position=tuple(eye),target=tuple(center))
    # Broad photographic lights show black glossy surfaces on black.
    # Source materials and all verification thresholds remain unchanged.
    for index,(offset,intensity) in enumerate([((1.4,1.8,1.8),60000),((-1.4,.8,1.0),20000)]):
        light=UsdLux.RectLight.Define(stage,'/World/Lights/ThumbnailSoftbox_'+str(index))
        light.CreateWidthAttr(diagonal*1.5);light.CreateHeightAttr(diagonal)
        light.CreateIntensityAttr(intensity)
        light.GetPrim().CreateAttribute('visibleInPrimaryRay',Sdf.ValueTypeNames.Bool).Set(False)
        transform=Gf.Matrix4d(1).SetLookAt(center+Gf.Vec3d(*offset)*diagonal,center,Gf.Vec3d(0,0,1)).GetInverse()
        UsdGeom.Xformable(light.GetPrim()).AddTransformOp().Set(transform)
    camera=UsdGeom.Camera(stage.GetPrimAtPath('/World/Camera'))
    camera.GetClippingRangeAttr().Set(Gf.Vec2f(max(1e-7,distance*0.001),max(10000,distance*100)))
    await ctx.settle(count=5)
    frame = await ctx.capture_frame(label='authored_materials_black', role='summary', stabilize_frames=8)
    if not frame:
        ctx.fail('Native renderer did not return a frame')
        return
    image = Image.open(frame).convert('RGB')
    pixels = np.asarray(image)
    corners = np.concatenate([pixels[:16,:16].reshape(-1,3), pixels[:16,-16:].reshape(-1,3),
                              pixels[-16:,:16].reshape(-1,3), pixels[-16:,-16:].reshape(-1,3)])
    corner_max = int(corners.max())
    coverage = float((pixels.max(axis=2) > 16).mean())
    ctx.add_metric('background_corner_max_rgb', corner_max)
    ctx.add_metric('nonblack_pixel_coverage', coverage)
    if corner_max > 8 or coverage < 0.01:
        ctx.fail('Black background or asset visibility verification failed')
        return
    thumbnail = Path(ctx.output_dir)/'package-thumbnail.png'
    image.resize((256,256), Image.Resampling.LANCZOS).save(thumbnail)
    with Path(ctx.asset_path).open('rb') as stream:
        source_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    ctx.add_metric('asset_usd_sha256', source_hash)
    ctx.add_metric('thumbnail_sha256', hashlib.sha256(thumbnail.read_bytes()).hexdigest())
    ctx.attach_media(str(thumbnail), role='summary')
    ctx.step('Native black-background thumbnail verified')
