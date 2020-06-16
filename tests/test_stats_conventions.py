from rediz import Rediz
from rediz.rediz_test_config import REDIZ_TEST_CONFIG
import numpy as np

def test_conv():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    xs = rdz.percentile_abscissa()
    assert len(xs)>5

def test_cdf_invcdf():
    normcdf = Rediz._normcdf_function()
    norminv = Rediz._norminv_function()
    for x in np.random.randn(100):
        x1 = norminv(normcdf(x))
        assert abs(x-x1)<1e-4

def test_mean_percentile():
    zscores = np.random.randn(100)
    normcdf = Rediz._normcdf_function()
    norminv = Rediz._norminv_function()
    p = [ normcdf(z) for z in zscores ]
    avg_p = Rediz.zmean_percentile(p)
    implied_avg = norminv(avg_p)
    actual_avg  = np.mean(zscores)
    assert abs(implied_avg-actual_avg)<1e-4


def test_cdf_invcdf_again():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    normcdf = rdz._normcdf_function()
    norminv = rdz._norminv_function()
    for x in np.random.randn(100):
        x1 = norminv(normcdf(x))
        assert abs(x-x1)<1e-4

def test_mean_percentile_again():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    zscores = np.random.randn(100)
    normcdf = rdz._normcdf_function()
    norminv = rdz._norminv_function()
    p = [ normcdf(z) for z in zscores ]
    avg_p = rdz.zmean_percentile(p)
    implied_avg = norminv(avg_p)
    actual_avg  = np.mean(zscores)
    assert abs(implied_avg-actual_avg)<1e-4