import unittest

from offaxis.projection import normalize_viewer_offset, quad_from_view


class ProjectionTests(unittest.TestCase):
    def test_normalize_center(self):
        self.assertEqual(normalize_viewer_offset(50, 50, 100, 100), (0.0, 0.0))

    def test_normalize_edges_clamped(self):
        self.assertEqual(normalize_viewer_offset(-10, 120, 100, 100), (-1.0, 1.0))

    def test_quad_has_four_points(self):
        quad = quad_from_view(100, 100, 80, 40, 0.2, -0.1)
        self.assertEqual(len(quad), 4)

    def test_quad_changes_with_view(self):
        q1 = quad_from_view(100, 100, 80, 40, 0.0, 0.0)
        q2 = quad_from_view(100, 100, 80, 40, 0.6, 0.3)
        self.assertNotEqual(q1, q2)


if __name__ == "__main__":
    unittest.main()
