import unittest

from offaxis.projection import (
    clamp,
    normalize_viewer_offset,
    quad_from_view,
    relative_viewer_offset,
    smooth_viewer_offset,
)


class ProjectionTests(unittest.TestCase):
    def test_clamp(self):
        self.assertEqual(clamp(4, 0, 3), 3)
        self.assertEqual(clamp(-2, 0, 3), 0)
        self.assertEqual(clamp(2, 0, 3), 2)

    def test_normalize_center(self):
        self.assertEqual(normalize_viewer_offset(50, 50, 100, 100), (0.0, 0.0))

    def test_normalize_edges_clamped(self):
        self.assertEqual(normalize_viewer_offset(-10, 120, 100, 100), (-1.0, 1.0))

    def test_normalize_invalid_dimensions(self):
        self.assertEqual(normalize_viewer_offset(10, 10, 0, 100), (0.0, 0.0))
        self.assertEqual(normalize_viewer_offset(10, 10, 100, 0), (0.0, 0.0))

    def test_relative_viewer_offset(self):
        vx, vy = relative_viewer_offset((0.5, -0.4), (0.2, -0.1))
        self.assertAlmostEqual(vx, 0.3)
        self.assertAlmostEqual(vy, -0.3)

    def test_relative_viewer_offset_clamped(self):
        self.assertEqual(relative_viewer_offset((2.5, -2.2), (0.0, 0.0)), (1.0, -1.0))

    def test_smooth_viewer_offset(self):
        self.assertEqual(smooth_viewer_offset((0.0, 0.0), (1.0, -1.0), 0.25), (0.25, -0.25))

    def test_smooth_viewer_offset_alpha_clamped(self):
        self.assertEqual(smooth_viewer_offset((0.2, -0.2), (0.8, -0.8), -1.0), (0.2, -0.2))
        self.assertEqual(smooth_viewer_offset((0.2, -0.2), (0.8, -0.8), 2.0), (0.8, -0.8))

    def test_quad_has_four_points(self):
        quad = quad_from_view(100, 100, 80, 40, 0.2, -0.1)
        self.assertEqual(len(quad), 4)

    def test_quad_changes_with_view(self):
        q1 = quad_from_view(100, 100, 80, 40, 0.0, 0.0)
        q2 = quad_from_view(100, 100, 80, 40, 0.6, 0.3)
        self.assertNotEqual(q1, q2)


if __name__ == "__main__":
    unittest.main()
