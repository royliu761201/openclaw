import numpy as np

def sigmoid(x):
    return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

class SynergisticModel:
    def __init__(self, n_features=4):
        self.theta = np.zeros(n_features)
    
    def predict(self, phi):
        logits = phi @ self.theta
        return sigmoid(logits)
    
    def get_loss(self, phi, y):
        probs = self.predict(phi)
        return -np.mean(y * np.log(probs + 1e-12) + (1 - y) * np.log(1 - probs + 1e-12))
    
    def get_gradient(self, phi, y):
        probs = self.predict(phi)
        grad = phi.T @ (probs - y) / len(y)
        return grad

class FederatedClient:
    def __init__(self, x_view, y, client_id):
        self.x_view = x_view # Only sees a subset of features
        self.y = y
        self.client_id = client_id
    
    def compute_local_grad(self, model, phi_full):
        # In a real system, phi_full is reconstructed from secret shares
        # Here we simulate the gradient calculation
        probs = model.predict(phi_full)
        diff = (probs - self.y)
        grad = phi_full.T @ diff / len(self.y)
        return grad

def run_step(model, phi, y, method='fedavg', lr=0.5, dp_noise=0.0):
    grad = model.get_gradient(phi, y)
    
    if method == 'fedavg':
        # Additive models can't see the interaction term
        grad[3] = 0
    
    if dp_noise > 0:
        # Sensitivity of cross-entropy gradient with bounded features is approx 1/n
        noise = np.random.normal(0, dp_noise, size=grad.shape)
        grad += noise
        
    grad = np.clip(grad, -10, 10)
    model.theta -= lr * grad
    return grad
