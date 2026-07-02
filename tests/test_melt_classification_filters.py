import unittest

from obanalyser.analyse_obp_geometry import is_melt_scan
from obanalyser.config import config


class TestMeltClassificationFilters(unittest.TestCase):
    def setUp(self):
        self._original_speed_threshold = config.melt_speed_threshold
        self._original_dwell_threshold = config.melt_dwell_time_threshold

    def tearDown(self):
        config.melt_speed_threshold = self._original_speed_threshold
        config.melt_dwell_time_threshold = self._original_dwell_threshold

    def test_default_behavior_unchanged_when_optional_filters_disabled(self):
        config.melt_speed_threshold = None
        config.melt_dwell_time_threshold = None

        self.assertTrue(is_melt_scan(average_spot_size=120.0, average_power=660.0))
        self.assertFalse(is_melt_scan(average_spot_size=800.0, average_power=660.0))

    def test_speed_filter_blocks_fast_scans(self):
        config.melt_speed_threshold = 2_000_000.0
        config.melt_dwell_time_threshold = None

        self.assertFalse(
            is_melt_scan(
                average_spot_size=120.0,
                average_power=660.0,
                average_speed=3_500_000.0,
                average_dwell_time=0.0,
            )
        )
        self.assertTrue(
            is_melt_scan(
                average_spot_size=120.0,
                average_power=660.0,
                average_speed=1_500_000.0,
                average_dwell_time=0.0,
            )
        )

    def test_dwell_filter_requires_long_enough_exposure(self):
        config.melt_speed_threshold = None
        config.melt_dwell_time_threshold = 200_000.0

        self.assertFalse(
            is_melt_scan(
                average_spot_size=120.0,
                average_power=660.0,
                average_speed=0.0,
                average_dwell_time=50_000.0,
            )
        )
        self.assertTrue(
            is_melt_scan(
                average_spot_size=120.0,
                average_power=660.0,
                average_speed=0.0,
                average_dwell_time=500_000.0,
            )
        )


if __name__ == "__main__":
    unittest.main()
