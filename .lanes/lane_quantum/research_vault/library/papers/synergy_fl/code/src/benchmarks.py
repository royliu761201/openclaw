import numpy as np

def generate_xor_data(n_samples=2000, noise=0.0):
    x1 = np.random.choice([0, 1], size=n_samples)
    x2 = np.random.choice([0, 1], size=n_samples)
    y = x1 ^ x2
    if noise > 0:
        flip = np.random.rand(n_samples) < noise
        y[flip] = 1 - y[flip]
    return x1, x2, y

def generate_parity_data(n_samples=2000, k=3, noise=0.0):
    X = np.random.choice([0, 1], size=(n_samples, k))
    y = np.bitwise_xor.reduce(X, axis=1)
    if noise > 0:
        flip = np.random.rand(n_samples) < noise
        y[flip] = 1 - y[flip]
    return X, y

def generate_healthcare_data(n_samples=2000, noise=0.1):
    # Simulated interaction between two "institutions" (features)
    # y = 1 if both feature A and feature B are present (high interaction)
    x1 = (np.random.randn(n_samples) > 0).astype(int)
    x2 = (np.random.randn(n_samples) > 0).astype(int)
    
    # Interaction term
    prob = 0.1 + 0.8 * (x1 * x2)
    y = (np.random.rand(n_samples) < prob).astype(int)
    
    return x1, x2, y

def get_lifted_features(x1, x2):
    # Standard lifted features for synergy analysis: [1, x1, x2, x1*x2]
    return np.vstack([np.ones(len(x1)), x1, x2, x1*x2]).T
