import tkinter as tk
from tkinter import filedialog, ttk
from pathlib import Path
import re
import subprocess
import sys
import argparse


DEFAULT_FOLDER = Path.home()


# ===== BƯỚC 1: HÀM CHẠY TAG_ENHANCER v12.6 TRƯỚC =====
def run_tag_enhancer(folder):
    script_dir = Path(__file__).parent
    tag_script = script_dir / "tag_enhancer_v12.6_FINAL.py"
    out_tags = folder / "out_tags"
    out_tags.mkdir(exist_ok=True)
    
    if not tag_script.exists():
        return False, "❌ tag_enhancer_v12.6_FINAL.py không tồn tại"
    
    cmd = [sys.executable, str(tag_script), "--folder", str(folder)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        addfaceless = out_tags / "addfaceless.txt"
        if addfaceless.exists():
            return True, "✅ Tag enhancer hoàn thành"
        else:
            return False, f"❌ Không tạo addfaceless.txt\n{result.stderr}"
    except Exception as e:
        return False, f"💥 Lỗi chạy tag_enhancer: {e}"


# ===== HÀM XỬ LÝ CHARACTER =====
EYE_TAGS = {
    'red_eyes','blue_eyes','green_eyes','brown_eyes','yellow_eyes','purple_eyes',
    'heterochromia','multicolored_eyes','golden_eyes','pink_eyes','grey_eyes',
    'pupils','slit pupils','crossed_eyes','heart-shaped_pupils','glowing_eyes',
    'eyelashes','colored_eyelashes','long_eyelashes','thick_eyelashes',
    'eyeshadow','mascara','eyeliner','makeup','cosmetics'
}

COVERED_EYES_TAGS = {
    'covered_eyes','blindfold','eyepatch','hair_over_eyes','eyes_visible_through_hair',
    'black_blindfold'
}


def extract_lora_fullname(user_prompt):
    match = re.search(r'<lora:([^:]+):', user_prompt)
    return match.group(1) if match else None


def clean_prompt_tags(user_prompt, base_tags):
    prompt_tags = [tag.strip() for tag in user_prompt.split(',')]
    
    if '1girl' in base_tags:
        prompt_tags = [t for t in prompt_tags if t != '1girl']
    
    if 'black_blindfold' in base_tags or any('blindfold' in tag for tag in base_tags):
        eye_block_tags = EYE_TAGS.copy()
    else:
        eye_block_tags = EYE_TAGS if any(tag in COVERED_EYES_TAGS for tag in base_tags) else set()
    
    prompt_tags = [t for t in prompt_tags if t.strip() not in eye_block_tags]
    
    if any(tag in COVERED_EYES_TAGS for tag in base_tags) and 'black_blindfold' not in base_tags:
        return None
    
    return ', '.join(prompt_tags)


def process_character_txt(folder, user_prompt):
    output_folder = folder / "out_tags"
    output_folder.mkdir(exist_ok=True)
    
    addfaceless_file = output_folder / "addfaceless.txt"
    if not addfaceless_file.exists():
        return False, "❌ addfaceless.txt không tồn tại"
    
    lora_full_name = extract_lora_fullname(user_prompt)
    if not lora_full_name:
        return False, "❌ Không tìm <lora:...:1>"
    
    char_filename = f"{lora_full_name}-character.txt"
    char_file = output_folder / char_filename
    
    try:
        with open(addfaceless_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        with open(char_file, 'w', encoding='utf-8') as out:
            processed, skipped, black_blindfold_skip = 0, 0, 0
            for base_line in lines:
                base_tags = set(tag.strip() for tag in base_line.split(','))
                clean_prompt = clean_prompt_tags(user_prompt, base_tags)
                
                if clean_prompt is None:
                    skipped += 1
                    continue
                
                full_prompt = f"{base_line}, {clean_prompt}"
                out.write(full_prompt + '\n')
                processed += 1
                
                if 'black_blindfold' in base_tags:
                    black_blindfold_skip += 1
        
        msg = f"✅ {processed}/{len(lines)} lines (skip {skipped})"
        if black_blindfold_skip > 0:
            msg += f"\n🔒 black_blindfold: {black_blindfold_skip} cases"
        msg += f"\n📁 {char_filename}"
        
        return True, msg
        
    except Exception as e:
        return False, f"💥 Lỗi: {e}"


# ===== CLASS GUI (SẠCH SẼ) =====
class TagEnhancerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Tag Enhancer v12.6 → Character TXT")
        self.root.geometry("900x600")
        self.root.resizable(True, True)
        self.folder_path = tk.StringVar(value=str(DEFAULT_FOLDER))
        self.setup_ui()
        self.log("🎯 Tag Enhancer v12.6 + Character Processor")

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="🎯 PIPELINE: Tag Enhancer v12.6 → Character TXT", 
                 font=("Arial", 18, "bold")).pack(pady=20)

        # Folder
        folder_frame = ttk.LabelFrame(main_frame, text="📁 FOLDER_TO_PROCESS", padding="15")
        folder_frame.pack(fill="x", pady=10)
        entry_frame = ttk.Frame(folder_frame)
        entry_frame.pack(fill="x")
        ttk.Entry(entry_frame, textvariable=self.folder_path, font=("Consolas", 11)).pack(side="left", fill="x", expand=True, padx=(0,10))
        ttk.Button(entry_frame, text="Browse", command=self.browse_folder).pack(side="right")
        
        # Buttons
        btn_frame = ttk.Frame(folder_frame)
        btn_frame.pack(fill="x", pady=10)
        ttk.Button(btn_frame, text="1️⃣ RUN TAG ENHANCER v12.6", 
                  command=self.run_tag_enhancer).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="2️⃣ PROCESS CHARACTER TXT", 
                  command=self.process_character).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🎯 FULL PIPELINE", 
                  command=self.full_pipeline).pack(side="right", padx=5)

        # Prompt
        prompt_frame = ttk.LabelFrame(main_frame, text="💬 PROMPT (cần <lora:...:1>)", padding="15")
        prompt_frame.pack(fill="both", expand=True, pady=10)
        self.prompt_text = tk.Text(prompt_frame, height=5)
        self.prompt_text.pack(fill="both", expand=True)

        # Log
        log_frame = ttk.LabelFrame(main_frame, text="📋 LOG", padding="10")
        log_frame.pack(fill="both", expand=True, pady=10)
        self.log_text = tk.Text(log_frame, state="disabled")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def log(self, message):
        print(message)
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        self.root.update()

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=str(self.folder_path.get()))
        if folder: self.folder_path.set(folder)

    def run_tag_enhancer(self):
        folder = Path(self.folder_path.get())
        self.log("1️⃣ Chạy Tag Enhancer v12.6...")
        success, msg = run_tag_enhancer(folder)
        self.log(msg)

    def process_character(self):
        folder = Path(self.folder_path.get())
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        
        if not prompt:
            return self.log("❌ Nhập prompt!")
        
        self.log("2️⃣ Process Character TXT...")
        success, msg = process_character_txt(folder, prompt)
        self.log(msg)

    def full_pipeline(self):
        folder = Path(self.folder_path.get())
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        
        if not prompt:
            return self.log("❌ Nhập prompt!")
        
        self.log("\n🎯 FULL PIPELINE START")
        self.log("═" * 60)
        
        # Bước 1
        success1, msg1 = run_tag_enhancer(folder)
        self.log(msg1)
        if not success1:
            return self.log("⏹️ Dừng pipeline")
        
        # Bước 2  
        self.log("\n2️⃣ Process Character...")
        success2, msg2 = process_character_txt(folder, prompt)
        self.log(msg2)
        
        self.log("🎉 FULL PIPELINE COMPLETE!" if success2 else "💥 Pipeline failed!")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = TagEnhancerGUI()
    app.run()
