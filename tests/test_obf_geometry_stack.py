import unittest

import numpy as np

import obanalyser.get_build_order as get_build_order
from obanalyser.analyse_obf_geometry import (
    DEFAULT_BACKGROUND_RGB,
    DEFAULT_SINTERED_RGB,
    analyse_obf_geom,
)


class TestObfGeometryStack(unittest.TestCase):
    def test_analyse_obf_geom_creates_colored_layer_stack(self):
        build_path = r"tests\input\cubes_test\buildInfo.json"
        build_sequence, _ = get_build_order.get_layer_execution_sequence(build_path)

        image_stack, origin_xy, pixel_um = analyse_obf_geom(
            build_path,
            pixel_um=200,
            close_gap_um=50,
        )

        self.assertEqual(image_stack.shape[0], len(build_sequence))
        self.assertEqual(image_stack.shape[-1], 3)
        self.assertGreater(image_stack.shape[1], 1)
        self.assertGreater(image_stack.shape[2], 1)
        self.assertEqual(origin_xy.__class__, tuple)
        self.assertEqual(pixel_um, 200)

        first_layer = image_stack[0]
        unique_colors = {
            tuple(color.tolist())
            for color in np.unique(first_layer.reshape(-1, 3), axis=0)
        }

        self.assertIn(DEFAULT_BACKGROUND_RGB, unique_colors)
        self.assertIn(DEFAULT_SINTERED_RGB, unique_colors)

        part_colors = unique_colors - {DEFAULT_BACKGROUND_RGB, DEFAULT_SINTERED_RGB}
        self.assertEqual(len(part_colors), 4)
        self.assertTrue(np.array_equal(image_stack[0], image_stack[-1]))


if __name__ == "__main__":
    unittest.main()
