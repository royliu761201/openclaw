import cv2
import sys
import os

def decode_qr(image_path):
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}")
        return

    img = cv2.imread(image_path)
    if img is None:
        print("Error: Could not read image.")
        return

    detector = cv2.QRCodeDetector()
    data, bbox, _ = detector.detectAndDecode(img)

    if data:
        print(f"QR Code Data: {data}")
    else:
        print("No QR code detected.")

if __name__ == "__main__":
    # Use the specific screenshot we took earlier
    screenshot_path = r"C:\Users\ainemo\.gemini\antigravity\brain\3e767d32-f751-41cc-8df1-24043ce3cc06\feishu_login_page_1771078739245.png"
    decode_qr(screenshot_path)
