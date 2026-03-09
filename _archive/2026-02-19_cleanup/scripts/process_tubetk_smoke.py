import SimpleITK as sitk
import os
import glob
import numpy as np

def main():
    print("🚀 Starting TubeTK Preprocessing (Smoke Test Mode)...")
    
    src_root = "/root/data/TubeTK/Designed Database of MR Brain Images of Healthy Volunteers"
    dst_root = "/root/data/TubeTK"
    
    train_lbl = os.path.join(dst_root, "train", "labels")
    train_img = os.path.join(dst_root, "train", "images")
    test_lbl = os.path.join(dst_root, "test", "labels") 
    test_img = os.path.join(dst_root, "test", "images")
    
    for d in [train_lbl, train_img, test_lbl, test_img]:
        os.makedirs(d, exist_ok=True)
        
    cases = sorted(glob.glob(os.path.join(src_root, "Normal-*")))
    print(f"Found {len(cases)} cases total.")
    
    subset = cases[:7]
    
    for i, case_path in enumerate(subset):
        case_name = os.path.basename(case_path)
        mra_files = glob.glob(os.path.join(case_path, "MRA", "*.mha"))
        if not mra_files:
            continue
            
        mra_path = mra_files[0]
        print(f"Processing {case_name}...")
        
        try:
            img = sitk.ReadImage(mra_path)
            
            if i < 5:
                out_img_dir = train_img
                out_lbl_dir = train_lbl
            else:
                out_img_dir = test_img
                out_lbl_dir = test_lbl
                
            out_name = f"{case_name}.nii.gz"
            out_img_path = os.path.join(out_img_dir, out_name)
            sitk.WriteImage(img, out_img_path)
            
            otsu_filter = sitk.OtsuThresholdImageFilter()
            otsu_filter.SetInsideValue(0)
            otsu_filter.SetOutsideValue(1)
            mask = otsu_filter.Execute(img)
            
            out_lbl_path = os.path.join(out_lbl_dir, out_name)
            sitk.WriteImage(mask, out_lbl_path)
        except Exception as e:
            print(f"Error processing {case_name}: {e}")

    print("✅ TubeTK Preprocessing Complete.")

if __name__ == "__main__":
    main()
