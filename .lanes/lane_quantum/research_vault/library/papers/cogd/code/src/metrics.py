import torch
import numpy as np
from scipy.spatial.distance import cdist
from scipy.ndimage import binary_erosion, generate_binary_structure

def compute_hd95(pred, gt, spacing=None):
    """
    Compute Hausdorff Distance 95th percentile.
    pred, gt: numpy arrays (H, W) or (D, H, W), binary (0/1 or boolean)
    spacing: spatial resolution (optional)
    """
    # 1. Edge Extraction
    pred_border = pred ^ binary_erosion(pred, structure=generate_binary_structure(pred.ndim, 1))
    gt_border = gt ^ binary_erosion(gt, structure=generate_binary_structure(gt.ndim, 1))
    
    pred_pts = np.argwhere(pred_border)
    gt_pts = np.argwhere(gt_border)
    
    if len(pred_pts) == 0 or len(gt_pts) == 0:
        # One mask is empty. If both empty, 0. If one, max dist?
        if len(pred_pts) == 0 and len(gt_pts) == 0:
            return 0.0
        else:
            # Standard penalty: Max possible distance (diagonal of image)
            return np.sqrt(np.sum(np.array(pred.shape)**2))
            
    # 2. Distance Calculation (Symmetric)
    # Use cdist for small sets, or KDTree for large. cdist is fine for 2D boundaries usually.
    # Note: KDTree is faster for large sets.
    from scipy.spatial import cKDTree
    
    # Distances from Pred to GT
    tree_gt = cKDTree(gt_pts)
    d_pg, _ = tree_gt.query(pred_pts)
    
    # Distances from GT to Pred
    tree_pred = cKDTree(pred_pts)
    d_gp, _ = tree_pred.query(gt_pts)
    
    # 3. Percentile
    all_dists = np.concatenate([d_pg, d_gp])
    hd95 = np.percentile(all_dists, 95)
    
    return hd95

def calculate_metrics(pred_mask, gt_mask, calc_hd95=False):
    """
    Calculate Dice, IoU, Sensitivity, Precision, and optionally HD95.
    pred_mask: Tensor [B, 1, H, W] or [B, H, W], probabilities [0,1]
    gt_mask: Tensor [B, 1, H, W] or [B, H, W], binary [0,1]
    """
    # Ensure standard shape [B, H, W]
    if pred_mask.ndim == 4: pred_mask = pred_mask.squeeze(1)
    if gt_mask.ndim == 4: gt_mask = gt_mask.squeeze(1)
    
    # Binarize
    pred_bin = (pred_mask > 0.5).float()
    gt_bin = (gt_mask > 0.5).float()
    
    # --- Soft Metrics (Batch-wise aggregation for Dice/IoU is common, but here we avg per sample) ---
    # Intersection & Union per sample
    intersection = (pred_bin * gt_bin).sum(dim=(1, 2))
    pred_sum = pred_bin.sum(dim=(1, 2))
    gt_sum = gt_bin.sum(dim=(1, 2))
    
    # Dice
    dice = (2. * intersection + 1e-6) / (pred_sum + gt_sum + 1e-6)
    
    # IoU
    union = pred_sum + gt_sum - intersection
    iou = (intersection + 1e-6) / (union + 1e-6)
    
    # Sensitivity (Recall)
    sens = (intersection + 1e-6) / (gt_sum + 1e-6) # TP / (TP + FN)
    
    # Precision
    prec = (intersection + 1e-6) / (pred_sum + 1e-6) # TP / (TP + FP)
    
    metrics = {
        "dice": dice.mean(),
        "iou": iou.mean(),
        "sens": sens.mean(),
        "prec": prec.mean(),
        "hd95": torch.tensor(0.0)
    }
    
    if calc_hd95:
        # Move to CPU for Scipy
        pred_np = pred_bin.detach().cpu().numpy().astype(bool)
        gt_np = gt_bin.detach().cpu().numpy().astype(bool)
        
        hd95_sum = 0.0
        count = 0
        batch_size = pred_mask.size(0)
        
        for i in range(batch_size):
            h = compute_hd95(pred_np[i], gt_np[i])
            hd95_sum += h
            count += 1
            
        metrics["hd95"] = torch.tensor(hd95_sum / max(count, 1))
        
    return metrics
