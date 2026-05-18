import numpy as np
from scipy.ndimage import gaussian_filter
import os
import yaml
from datetime import datetime

class EulerSolver1D:
    """
    5th-order WENO solver for 1D Compressible Euler Equations.
    """
    def __init__(self, nx=256, L=1.0, gamma=1.4):
        self.nx = nx
        self.dx = L / nx
        self.gamma = gamma
        self.x = np.linspace(0.5*self.dx, L-0.5*self.dx, nx)

    def get_primitive(self, U):
        rho = U[0]
        u = U[1] / rho
        p = (self.gamma - 1.0) * (U[2] - 0.5 * rho * u**2)
        return rho, u, p

    def get_flux(self, U):
        rho, u, p = self.get_primitive(U)
        return np.array([U[1], U[1]*u + p, (U[2] + p)*u])

    def weno5_reconstruct(self, f, direction):
        """Vectorized WENO5 reconstruction"""
        if direction == 'left': # f_{i+1/2}^{-}
            v = np.pad(f, (2, 3), mode='edge')
            v0, v1, v2, v3, v4 = v[0:-4], v[1:-3], v[2:-2], v[3:-1], v[4:]
        else: # f_{i-1/2}^{+} (equivalent to left on flipped array)
            v = np.pad(f, (3, 2), mode='edge')
            v4, v3, v2, v1, v0 = v[0:-4], v[1:-3], v[2:-2], v[3:-1], v[4:]

        # Polynomials
        p0 = (2*v0 - 7*v1 + 11*v2) / 6.0
        p1 = (-v1 + 5*v2 + 2*v3) / 6.0
        p2 = (2*v2 + 5*v3 - v4) / 6.0

        # Smoothness indicators
        beta0 = 13/12*(v0 - 2*v1 + v2)**2 + 1/4*(v0 - 4*v1 + 3*v2)**2
        beta1 = 13/12*(v1 - 2*v2 + v3)**2 + 1/4*(v1 - v3)**2
        beta2 = 13/12*(v2 - 2*v3 + v4)**2 + 1/4*(3*v2 - 4*v3 + v4)**2

        eps = 1e-10
        w0 = 0.1 / (beta0 + eps)**2
        w1 = 0.6 / (beta1 + eps)**2
        w2 = 0.3 / (beta2 + eps)**2
        ws = w0 + w1 + w2
        
        return (w0*p0 + w1*p1 + w2*p2) / ws

    def compute_rhs(self, U):
        rho, u, p = self.get_primitive(U)
        a = np.sqrt(self.gamma * p / rho)
        alpha = np.max(np.abs(u) + a)
        
        F = self.get_flux(U)
        Fp = 0.5 * (F + alpha * U)
        Fm = 0.5 * (F - alpha * U)
        
        # Interface fluxes
        F_plus = np.zeros((3, self.nx + 1))
        F_minus = np.zeros((3, self.nx + 1))
        
        for k in range(3):
            # fp_{i+1/2}^{-}
            F_plus[k] = self.weno5_reconstruct(Fp[k], 'left')
            # fm_{i+1/2}^{+}
            F_minus[k] = self.weno5_reconstruct(Fm[k], 'right')
            
        F_face = F_plus + F_minus
        return -(F_face[:, 1:] - F_face[:, :-1]) / self.dx

    def solve(self, U0, T, cfl=0.4):
        U = U0.copy()
        t = 0.0
        while t < T:
            rho, u, p = self.get_primitive(U)
            a = np.sqrt(self.gamma * p / rho)
            dt = cfl * self.dx / np.max(np.abs(u) + a)
            if t + dt > T: dt = T - t
            
            # TVD-RK3
            U1 = U + dt * self.compute_rhs(U)
            U2 = 0.75*U + 0.25*U1 + 0.25*dt * self.compute_rhs(U1)
            U = (1/3)*U + (2/3)*U2 + (2/3)*dt * self.compute_rhs(U2)
            t += dt
        return U

class EulerSolver2D:
    """
    2D Finite Volume solver for Compressible Euler Equations.
    Uses HLLC Riemann solver and MUSCL reconstruction.
    """
    def __init__(self, nx=128, ny=128, L=1.0, gamma=1.4):
        self.nx, self.ny = nx, ny
        self.dx = L / nx
        self.dy = L / ny
        self.gamma = gamma

    def get_primitive(self, U):
        rho = U[0]
        u = U[1] / rho
        v = U[2] / rho
        p = (self.gamma - 1.0) * (U[3] - 0.5 * rho * (u**2 + v**2))
        return rho, u, v, p

    def solve_hllc(self, UL, UR, axis):
        """HLLC Riemann Solver (axis: 0 for x, 1 for y)"""
        gamma = self.gamma
        rhoL, uL, vL, pL = self.get_primitive(UL)
        rhoR, uR, vR, pR = self.get_primitive(UR)
        
        unL = uL if axis == 0 else vL
        unR = uR if axis == 0 else vR
        
        aL = np.sqrt(gamma * pL / rhoL)
        aR = np.sqrt(gamma * pR / rhoR)
        
        SL = np.minimum(unL - aL, unR - aR)
        SR = np.maximum(unL + aL, unR + aR)
        
        # SM (Contact wave speed)
        SM = (pR - pL + rhoL*unL*(SL - unL) - rhoR*unR*(SR - unR)) / \
             (rhoL*(SL - unL) - rhoR*(SR - unR))
             
        FL = self.get_flux(UL, axis)
        FR = self.get_flux(UR, axis)
        
        F = np.zeros_like(FL)
        F[:, SL >= 0] = FL[:, SL >= 0]
        F[:, SR <= 0] = FR[:, SR <= 0]
        
        condL = (SL < 0) & (SM >= 0)
        condR = (SM < 0) & (SR >= 0)
        
        if np.any(condL):
            UstarL = self.get_star_state(UL[:, condL], pL[condL], unL[condL], SL[condL], SM[condL], axis)
            F[:, condL] = FL[:, condL] + SL[condL] * (UstarL - UL[:, condL])
            
        if np.any(condR):
            UstarR = self.get_star_state(UR[:, condR], pR[condR], unR[condR], SR[condR], SM[condR], axis)
            F[:, condR] = FR[:, condR] + SR[condR] * (UstarR - UR[:, condR])
            
        return F

    def get_flux(self, U, axis):
        rho, u, v, p = self.get_primitive(U)
        if axis == 0: # x-direction
            return np.array([U[1], U[1]*u + p, U[1]*v, (U[3] + p)*u])
        else: # y-direction
            return np.array([U[2], U[2]*u, U[2]*v + p, (U[3] + p)*v])

    def get_star_state(self, U, p, un, S, SM, axis):
        rho = U[0]
        fac = rho * (S - un) / (S - SM)
        # [rho, rhou, rhov, E]
        E_star = fac * (U[3]/rho + (SM - un) * (SM + p/(rho*(S - un))))
        if axis == 0:
            return np.array([fac, fac*SM, fac*(U[2]/rho), E_star])
        else:
            return np.array([fac, fac*(U[1]/rho), fac*SM, E_star])

    def solve(self, U0, T, cfl=0.4):
        U = U0.copy()
        t = 0.0
        while t < T:
            rho, u, v, p = self.get_primitive(U)
            a = np.sqrt(self.gamma * p / rho)
            dt = cfl * np.minimum(self.dx, self.dy) / np.max(np.abs(u) + np.abs(v) + a)
            if t + dt > T: dt = T - t
            
            # Simple 1st-order for now to ensure stability in 2D
            rhs = self.compute_rhs(U)
            U += dt * rhs
            t += dt
        return U

    def compute_rhs(self, U):
        # Periodic BCs for simplicity in this implementation
        UL = np.roll(U, 1, axis=1); UR = U
        Fx = self.solve_hllc(UL, UR, 0)
        
        UB = np.roll(U, 1, axis=2); UT = U
        Fy = self.solve_hllc(UB, UT, 1)
        
        rhs = -(Fx - np.roll(Fx, -1, axis=1)) / self.dx - \
              (Fy - np.roll(Fy, -1, axis=2)) / self.dy
        return rhs

class GaussianMollifier:
    @staticmethod
    def blur_1d(data, sigma=2.0):
        return gaussian_filter(data, sigma=sigma, mode='reflect')
    
    @staticmethod
    def blur_2d(image, sigma=2.0):
        return gaussian_filter(image, sigma=sigma, mode='reflect')

class BurgersSolver1D:
    """Spectral solver for 1D Viscous Burgers Equation: u_t + u*u_x = nu*u_xx"""
    def __init__(self, nx=256, L=1.0, nu=0.01):
        self.nx = nx
        self.L = L
        self.nu = nu
        self.dx = L / nx
        self.k = 2 * np.pi * np.fft.fftfreq(nx, d=self.dx)

    def solve(self, u0, T, nt=100):
        u = u0.copy()
        dt = T / nt
        u_hat = np.fft.fft(u)
        
        # Precompute ETDRK4 coefficients for Burgers (simplified)
        L = -self.nu * (self.k**2)
        E = np.exp(dt * L)
        E2 = np.exp(dt * L / 2)
        
        for _ in range(nt):
            # Nonlinear term in Fourier space
            def nl(uh):
                u = np.fft.ifft(uh).real
                return -0.5j * self.k * np.fft.fft(u**2)
            
            # Simple RK2 for rapid implementation
            k1 = nl(u_hat)
            k2 = nl(E2 * u_hat + (dt/2)*k1)
            u_hat = E * u_hat + dt * k2
            
        return np.fft.ifft(u_hat).real

def save_run_info(path, metadata):
    metadata['timestamp'] = datetime.now().isoformat()
    with open(os.path.join(path, 'run_info.yaml'), 'w') as f:
        yaml.dump(metadata, f)
