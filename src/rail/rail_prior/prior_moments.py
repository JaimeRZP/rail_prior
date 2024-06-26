import numpy as np
from numpy.linalg import eig, cholesky
from scipy.stats import multivariate_normal as mvn
from .prior_base import PriorBase


class PriorMoments(PriorBase):
    """
    Prior for the moments model.
    The moments model assumes that meausred photometric distribution
    is Gaussian meaning that it can be fully described by its mean and
    covariance matrix. Conceptually, this is equavalent to a 
    Gaussian process regressio for a given p(z). The details can be found 
    in the paper: 2301.11978

    Some measured photometric distributions will possess non-invertible
    covariance matrices. If this is the case, PriorMoments will
    attempt regularize the covariance matrix by adding a small jitter
    to its eigen-values. If this fails, the covariance matrix will be
    diagonalized.
    """
    def __init__(self, ens):
        self._prior_base(ens)
        self._find_prior()

    def _find_prior(self):
        self.nz_chol = self._get_chol()

    def _get_chol(self):
        cov = self.nz_cov
        if not self._is_pos_def(cov):
            print('Warning: Covariance matrix is not positive definite')
            print('The covariance matrix will be regularized')
            jitter = 1e-15 * np.eye(cov.shape[0])
            w, v = eig(cov+jitter)
            w = np.real(np.abs(w))
            v = np.real(v)
            cov = v @ np.diag(np.abs(w)) @ v.T
            cov = np.tril(cov) + np.triu(cov.T, 1)
            if not self._is_pos_def(cov):
                print('Warning: regularization failed')
                print('The covariance matrix will be diagonalized')
                jitter = 1e-15
                cov = np.diag(np.diag(self.nz_cov)+jitter)
        chol = cholesky(cov)
        return chol

    def _is_pos_def(self, A):
        try:
            np.linalg.cholesky(A)
            return True
        except np.linalg.linalg.LinAlgError as err:
            return False
        #return np.all(np.linalg.eigvals(A) > 0)

    def evaluate_model(self, nz, args):
        """
        Samples a photometric distribution
        from a Gaussian distribution with mean
        and covariance measured from the data.
        """
        alpha = args
        z = nz[0]
        nz = nz[1]
        return [z, nz + self.nz_chol @ alpha]

    def _get_prior(self):
        return mvn(np.zeros_like(self.nz_mean),
                   np.ones_like(self.nz_mean))
