
from rediz.samplers import gaussian_samples, is_process, exponential_bootstrap, sign_changes
import numpy as np
import random

def test_sign():
    assert sign_changes( [7.0, 3.0, -1.0 ] ) ==1
    assert sign_changes([7.0, 0.0, 3.1, 3.0, -1.0]) == 1

def test_samples():
    some_samples()

def some_samples():
    num_samples = random.choice([1000] )
    num_data    = random.choice([500])
    noise = np.random.randn(num_data)
    assert not is_process(noise)
    lagged = 0.5+0.1*np.cumsum(noise)
    assert is_process(lagged)
    g_samples = gaussian_samples(lagged=lagged,num=num_samples)
    b_samples = exponential_bootstrap(lagged=lagged,num=num_samples,decay=0.01)
    return g_samples, b_samples

def dont_test_demo():
    import matplotlib.pyplot as plt
    plt.close('all')
    g_samples, b_samples = some_samples()
    plt.hist(g_samples, bins=50, density=True, range=[np.median(g_samples) - 0.3, np.median(g_samples) + 0.3])
    plt.hist(b_samples, bins=50, alpha=0.5, density=True)
    plt.legend(["Gaussian","Bootstrap"])
    plt.show()





