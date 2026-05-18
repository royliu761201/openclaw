import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np
import os
import h5py

class H5Dataset(Dataset):
    """
    Dataloader for standard HDF5 benchmark datasets (PDEBench, etc.)
    """
    def __init__(self, h5_path, task='burgers', split='train'):
        self.h5_path = h5_path
        self.task = task
        self.f = h5py.File(h5_path, 'r')
        # Structure depends on PDEBench version, typically nested.
        # This is a generic loader for 1D data.
        self.u = self.f[f'{split}/u']
        self.t = self.f[f'{split}/t']
        self.x = self.f[f'{split}/x']

    def __len__(self):
        return len(self.u)

    def __getitem__(self, idx):
        # We return (u0, u_target) or (params, u_target)
        return {
            'u0': torch.from_numpy(self.u[idx, 0]).float(),
            'targets': torch.from_numpy(self.u[idx, -1]).float()
        }

class BlastDataset(Dataset):
    """
    Dataset loader for GibbsNeural blast simulations.
    Loads raw/mollified targets and input parameters.
    """
    def __init__(self, data_root, task='sod', mode='mollified'):
        self.data_root = data_root
        self.task = task
        self.mode = mode
        
        # Load parameters (Input for Branch)
        params_file = os.path.join(data_root, 'processed', f'1d_{task}_params.npy')
        self.params = np.load(params_file).astype(np.float32)
        
        # Load targets (Output for training)
        if mode == 'mollified':
            target_file = os.path.join(data_root, 'processed', f'1d_{task}_mollified.npy')
        else:
            target_file = os.path.join(data_root, 'raw_sims', f'1d_{task}_raw.npy')
        self.targets = np.load(target_file).astype(np.float32)
        
        # Normalize params across the dataset
        self.p_mean = self.params.mean(axis=0)
        self.p_std = self.params.std(axis=0) + 1e-6
        self.params_norm = (self.params - self.p_mean) / self.p_std
        
        # Normalize targets (optional but recommended for DeepONet stability)
        self.t_mean = self.targets.mean()
        self.t_std = self.targets.std() + 1e-6
        self.targets_norm = (self.targets - self.t_mean) / self.t_std

    def __len__(self):
        return len(self.params)

    def __getitem__(self, idx):
        return {
            'params': torch.from_numpy(self.params_norm[idx]),
            'targets': torch.from_numpy(self.targets_norm[idx])
        }

def get_dataloaders(data_root, task='sod', mode='mollified', batch_size=64, split=0.8):
    full_dataset = BlastDataset(data_root, task=task, mode=mode)
    train_size = int(split * len(full_dataset))
    test_size = len(full_dataset) - train_size
    train_dataset, test_dataset = torch.utils.data.random_split(full_dataset, [train_size, test_size])
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
    
    return train_loader, test_loader, full_dataset
