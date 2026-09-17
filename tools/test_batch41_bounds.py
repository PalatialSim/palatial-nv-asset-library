"""Regression checks for visible collider meshes, purpose and transforms."""
import unittest

import numpy as np
from pxr import Usd, UsdGeom, UsdPhysics
from standardize_batch41 import mesh_bounds


class BoundsTests(unittest.TestCase):
    def test_visible_collider_is_measured_but_proxy_is_excluded(self):
        stage = Usd.Stage.CreateInMemory()
        parent = UsdGeom.Xform.Define(stage, "/Asset")
        parent.AddTranslateOp().Set((100, 200, 300))
        mesh = UsdGeom.Mesh.Define(stage, "/Asset/Visual")
        mesh.CreatePointsAttr([(0, 0, 0), (10, 20, 30)])
        UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
        proxy = UsdGeom.Mesh.Define(stage, "/Asset/Proxy")
        proxy.CreatePointsAttr([(-1000, -1000, -1000), (1000, 1000, 1000)])
        proxy.CreatePurposeAttr("proxy")
        bounds = mesh_bounds(stage, 0.01)
        np.testing.assert_allclose(bounds["min"], [1, 2, 3])
        np.testing.assert_allclose(bounds["size"], [0.1, 0.2, 0.3])

    def test_mixed_visual_and_collision_meshes_both_contribute(self):
        stage = Usd.Stage.CreateInMemory()
        for name, points in [("A", [(0, 0, 0), (1, 1, 1)]),
                             ("B", [(2, 2, 2), (3, 3, 3)])]:
            mesh = UsdGeom.Mesh.Define(stage, "/" + name)
            mesh.CreatePointsAttr(points)
            if name == "B":
                UsdPhysics.CollisionAPI.Apply(mesh.GetPrim())
        np.testing.assert_allclose(mesh_bounds(stage, 1)["size"], [3, 3, 3])


if __name__ == "__main__":
    unittest.main()
