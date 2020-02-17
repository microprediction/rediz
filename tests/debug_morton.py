
from rediz.client import Rediz
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
rdz = Rediz()
from scipy import stats
import math

def rhocov(rho,dim):
    return np.eye(dim)+rho*np.ones([dim,dim])-rho*np.eye(dim)

def _bin(x, width):
    return ''.join(str((x>>i)&1) for i in range(width-1,-1,-1))

def doit(rho):
    dim = 2
    n   = 50000
    mu = [0 for _ in range(dim)]
    cov = rhocov(rho=rho, dim=dim)
    samples = np.random.multivariate_normal(mean=mu, cov=cov, size=n)


def sample(rho,dim,n):
    mu = [0 for _ in range(dim)]
    cov = rhocov(rho=rho,dim=dim)
    samples = np.random.multivariate_normal(mean=mu,cov = cov,size=n )
    std0 = np.nanstd( [ sum(s) for s in samples] )

    zs = list()
    for sample in samples:
        zs.append( to1(sample) )
    return zs, std0

def do2(rho):
    do(rho,dim=3)

def do2(rho):
    do(rho,dim=2)

def do(rho,dim):
    n=5000

    zs, std0 = sample(rho=rho,dim=2,n=5000)

    zok =  [ z for z in zs if not (np.isneginf(z) or np.isinf(z) or np.isnan(z))]
    std1 = np.nanstd( zok )
    if np.isnan(std1):
        pass
    stats.probplot(zs, dist=stats.norm, sparams=(0,std1), plot=plt)
    plt.title("std0="+str(std0)+" std1="+str(std1)+" sq="+str(math.sqrt(1+rho)))
    plt.show()


def to3(x,dim):
    y = rdz.from_zcurve(x,3)
    return rdz.norminv(y)

def to1(x):
    ps = [ rdz.normcdf(xi) for xi in list(x) ]
    return rdz.to_zcurve(ps)




if __name__=="__main__":
    do2(rho=0.3)
