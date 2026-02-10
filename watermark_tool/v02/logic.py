import os
import pickle
from PIL import Image, ImageFilter

def save_config(config_file, config):
    """
    Lưu cấu hình watermark vào file.
    """
    try:
        with open(config_file, "wb") as f:
            pickle.dump(config, f)
    except Exception as e:
        raise Exception(f"Error saving config: {e}")

def load_config(config_file):
    """
    Tải cấu hình watermark từ file.
    """
    if os.path.exists(config_file):
        try:
            with open(config_file, "rb") as f:
                config = pickle.load(f)
            return config
        except Exception as e:
            raise Exception(f"Error loading config: {e}")
    return None

def save_registered_watermarks(registered_watermarks_file, registered_watermarks):
    """
    Lưu danh sách watermark đã đăng ký.
    """
    try:
        with open(registered_watermarks_file, "wb") as f:
            pickle.dump(registered_watermarks, f)
    except Exception as e:
        raise Exception(f"Error saving registered watermarks: {e}")

def load_registered_watermarks(registered_watermarks_file):
    """
    Tải danh sách watermark đã đăng ký.
    """
    if os.path.exists(registered_watermarks_file):
        try:
            with open(registered_watermarks_file, "rb") as f:
                data = pickle.load(f)
            registered = []
            if data and isinstance(data, list) and data and isinstance(data[0], dict):
                registered = data
            else:
                for item in data:
                    if len(item) == 3:
                        wm = {"filename": item[0], "path": item[1], "wm_size": item[2]}
                    else:
                        wm = {"filename": item[0], "path": item[1], "wm_size": 50}
                    registered.append(wm)
            return registered
        except Exception as e:
            raise Exception(f"Error loading registered watermarks: {e}")
    return []

def resize_watermark(original_watermark_image, wm_size):
    """
    Thay đổi kích thước watermark giữ tỉ lệ ban đầu.
    """
    if original_watermark_image is None:
        return None
    width, height = original_watermark_image.size
    aspect_ratio = width / height
    new_width = wm_size
    new_height = int(wm_size / aspect_ratio)
    return original_watermark_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

def apply_watermark(img, original_img_size, preview_size, wm_position, wm_size, original_watermark_image):
    """
    Áp dụng watermark lên ảnh với việc tính toán tỉ lệ phù hợp từ ảnh gốc và ảnh preview.
    """
    if original_watermark_image is None or original_img_size is None or preview_size is None:
        return img
    orig_w, _ = original_img_size
    preview_w, _ = preview_size
    scale = orig_w / preview_w
    actual_position = (int(wm_position[0] * scale), int(wm_position[1] * scale))
    wm_resized = resize_watermark(original_watermark_image, int(wm_size * scale))
    img.paste(wm_resized, actual_position, wm_resized)
    return img

def apply_blur_effect(img):
    """
    Áp dụng hiệu ứng làm mờ và pixelate cho ảnh.
    """
    img_blurred = img.filter(ImageFilter.GaussianBlur(5))
    pixel_size = 10
    img_pixelated = img_blurred.resize(
        (img.width // pixel_size, img.height // pixel_size), Image.NEAREST
    ).resize(img.size, Image.NEAREST)
    return img_pixelated
