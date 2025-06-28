import numpy as np

from pytest_approvaltests_geo.differs.difference import calculate_pixel_diff_stats, Stats


def test_empty_arrays():
    assert calculate_pixel_diff_stats(np.array([]), np.array([])).is_empty


def test_all_nan_pixels():
    assert calculate_pixel_diff_stats(np.full((2, 2), np.nan), np.full((2, 2), np.nan)).nans == 0


def test_all_zero_pixels():
    assert calculate_pixel_diff_stats(np.zeros((2, 2)), np.zeros((2, 2))) == Stats()


def test_identical_pixels():
    assert calculate_pixel_diff_stats(np.array([[1, 2], [3, 4]]), np.array([[1, 2], [3, 4]])) == Stats()


def test_pixel_stats():
    stats = calculate_pixel_diff_stats(np.array([[1, 2], [3, 4]]), np.array([[2, 4], [4, 3]]))
    assert stats == Stats(min=1, max=2, mean=1.25, median=1.0, nans=0)
