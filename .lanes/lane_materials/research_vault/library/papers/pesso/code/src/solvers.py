import numpy as np
from scipy.integrate import solve_ivp
from scipy.fft import fft, ifft, fftfreq

def solve_burgers(L=1.0, T=2.0, nx=256, nt=100, nu=0.01):
    """
    Solve viscous Burgers equation: u_t + u*u_x = nu*u_xx
    using spectral methods.
    """
    x = np.linspace(0, L, nx, endpoint=False)
    dx = x[1] - x[0]
    t_eval = np.linspace(0, T, nt)
    
    # Initial condition: u(x, 0) = sin(2*pi*x/L) + 0.5*sin(4*pi*x/L)
    u0 = np.sin(2 * np.pi * x / L) + 0.5 * np.sin(4 * np.pi * x / L)
    
    # Wave numbers
    kappa = 2 * np.pi * fftfreq(nx, d=dx)
    
    def rhs(t, u_hat):
        u = ifft(u_hat)
        ux_hat = 1j * kappa * u_hat
        ux = ifft(ux_hat)
        uxx_hat = -kappa**2 * u_hat
        
        # Spectral RHS: -u*u_x + nu*u_xx
        return fft(-u * ux) + nu * uxx_hat
    
    u0_hat = fft(u0)
    sol = solve_ivp(rhs, (0, T), u0_hat, t_eval=t_eval, method='RK45')
    
    u_traj = np.zeros((nt, nx))
    for i in range(nt):
        u_traj[i] = ifft(sol.y[:, i]).real
        
    return x, t_eval, u_traj

def solve_ks(L=32.0, T=50.0, nx=256, nt=200):
    """
    Solve Kuramoto-Sivashinsky: u_t + u*u_x + u_xx + u_xxxx = 0
    Using ETDRK4 (Exponential Time Differencing Fourth-order Runge-Kutta).
    Efficient for stiff systems with linear and nonlinear parts.
    """
    x = np.linspace(0, L, nx, endpoint=False)
    dx = x[1] - x[0]
    dt = T / (nt * 10) # Finer internal steps
    
    # Initial condition
    u = 0.1 * np.cos(x/L * 2 * np.pi) * (1 + np.sin(x/L * 2 * np.pi))
    u_hat = fft(u)
    
    # Wave numbers
    k = 2 * np.pi * fftfreq(nx, d=dx)
    L_hat = k**2 - k**4 # Linear operator in Fourier space
    
    # Precompute ETDRK4 coefficients
    # Using the method of Kassam and Trefethen (2005)
    E = np.exp(dt * L_hat)
    E2 = np.exp(dt * L_hat / 2)
    
    # Avoid division by zero for k=0
    M = 16 # Number of points on contour for Cauchy integral
    phi = np.exp(1j * np.pi * (np.arange(1, M + 1) - 0.5) / M)
    LR = dt * L_hat[:, None] + phi[None, :]
    
    # Compute phi functions
    q = np.mean((np.exp(LR/2) - 1) / LR, axis=1)
    f1 = np.mean((np.exp(LR) - 1) / LR, axis=1)
    f2 = np.mean((np.exp(LR) - (LR + 1)) / LR**2, axis=1)
    f3 = np.mean((np.exp(LR) - (LR**2/2 + LR + 1)) / LR**3, axis=1)
    
    def nl_hat(u_h):
        u = ifft(u_h).real
        return -0.5j * k * fft(u**2)
    
    u_traj = []
    plot_every = 10
    
    for i in range(nt * 10):
        if i % plot_every == 0:
            u_traj.append(ifft(u_hat).real)
            
        Nu = nl_hat(u_hat)
        a = E2 * u_hat + q * Nu
        Na = nl_hat(a)
        b = E2 * u_hat + q * Na
        Nb = nl_hat(b)
        c = E2 * a + q * (2 * Nb - Nu)
        Nc = nl_hat(c)
        
        u_hat = E * u_hat + Nu * f1 + 2*(Na + Nb) * f2 + Nc * f3
        
    return x, np.linspace(0, T, nt), np.array(u_traj)

def solve_rd_2d(L=1.0, T=10.0, nx=64, nt=50, Du=0.02, Dv=0.01, f=0.025, k=0.055):
    """
    Solve 2D Reaction-Diffusion (Gray-Scott model):
    u_t = Du*nabla^2 u - u*v^2 + f(1-u)
    v_t = Dv*nabla^2 v + u*v^2 - (f+k)v
    """
    dx = L / nx
    u = np.ones((nx, nx))
    v = np.zeros((nx, nx))
    
    # Add initial perturbation
    r = 5
    u[nx//2-r:nx//2+r, nx//2-r:nx//2+r] = 0.5
    v[nx//2-r:nx//2+r, nx//2-r:nx//2+r] = 0.25
    
    def laplacian(Z):
        Ztop = Z[0:-2, 1:-1]
        Zleft = Z[1:-1, 0:-2]
        Zbottom = Z[2:, 1:-1]
        Zright = Z[1:-1, 2:]
        Zcenter = Z[1:-1, 1:-1]
        return (Ztop + Zleft + Zbottom + Zright - 4 * Zcenter) / dx**2

    u_traj = []
    v_traj = []
    
    # Use refined Euler integration for RD stability
    dt = 0.001 # Even smaller dt for stability
    steps = int(T / dt)
    save_every = max(1, steps // nt)
    
    for i in range(steps):
        lu = laplacian(u)
        lv = laplacian(v)
        
        # Clip to prevent explosion
        u_inner = np.clip(u[1:-1, 1:-1], 0, 1)
        v_inner = np.clip(v[1:-1, 1:-1], 0, 1)
        
        uvv = u_inner * v_inner**2
        
        u[1:-1, 1:-1] += dt * (Du * lu - uvv + f * (1 - u_inner))
        v[1:-1, 1:-1] += dt * (Dv * lv + uvv - (f + k) * v_inner)
        
        # Bound check
        if np.isnan(u).any():
            break
            
        if i % save_every == 0:
            u_traj.append(u.copy())
            v_traj.append(v.copy())
            
    return np.array(u_traj), np.array(v_traj)

def solve_wave_2d(L=2.0, T=2.0, nx=128, nt=100, c=1.0):
    """
    Solve 2D Wave Equation: u_tt = c^2 * nabla^2 u
    Simulating a blast wave in a medium with obstacles.
    """
    dx = L / nx
    dt = dx / (2 * c) * 0.9 # CFL condition
    
    u_prev = np.zeros((nx, nx))
    u = np.zeros((nx, nx))
    
    # Gaussian Pulse Initial Condition
    x = np.linspace(0, L, nx)
    y = np.linspace(0, L, nx)
    X, Y = np.meshgrid(x, y)
    u_prev = np.exp(-((X-L/3)**2 + (Y-L/2)**2) / 0.05)
    u = u_prev.copy() # Zero initial velocity
    
    # Obstacles
    mask = np.ones((nx, nx))
    # Wall
    mask[nx//2:nx//2+5, nx//4:3*nx//4] = 0
    
    u_traj = []
    
    steps = int(T / dt)
    save_every = max(1, steps // nt)
    
    for i in range(steps):
        # Laplacian
        u_top = np.roll(u, 1, axis=0)
        u_bottom = np.roll(u, -1, axis=0)
        u_left = np.roll(u, 1, axis=1)
        u_right = np.roll(u, -1, axis=1)
        
        lap = (u_top + u_bottom + u_left + u_right - 4*u) / dx**2
        
        # Verlet Integration
        u_next = 2*u - u_prev + dt**2 * c**2 * lap
        
        # Apply strict boundary/obstacle conditions
        u_next = u_next * mask
        
        u_prev = u
        u = u_next
        
        if i % save_every == 0:
            u_traj.append(u.copy())
            
    return np.array(u_traj)

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    
    # Test Burgers
    x, t, u = solve_burgers()
    plt.imshow(u, aspect='auto', extent=[0, 1, 0, 2])
    plt.title("Burgers Solution")
    plt.savefig("burgers_test.png")
    plt.close()
    print("Burgers test saved.")
