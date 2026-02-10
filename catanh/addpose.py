import tkinter as tk
from tkinter import scrolledtext, ttk

def clean_base(base):
    face_tags = {'blush', 'crying', 'one eye closed', 'tears', 'open mouth', 'closed eyes', 'wide eyes', 'v-shaped eyebrows', 'ahegao', 'tongue out'}
    tags = [t.strip() for t in base.split(',') if t.strip() not in face_tags]
    return ', '.join(tags)

def has_mouth_block(base):
    mouth_block = {'tape gag', 'gag', 'muzzle gag', 'ball gag', 'mouth gag'}
    tags = [t.strip().lower() for t in base.split(',')]
    return any(block in t for t in tags for block in mouth_block)

def generate():
    base = entry.get("1.0", tk.END).strip()
    clean_base_prompt = clean_base(base)
    pose = pose_var.get()
    mouth_blocked = has_mouth_block(base)
    
    motion = "motion lines, motion blur"
    sfx = "sound_effect"
    
    # Stages với motion + sfx
    stage1 = f"clenched teeth, wide eyes, v-shaped eyebrows, uterus, {sfx}"
    stage2 = f"uterus, one eye closed, clenched teeth, {motion}, {sfx}" 
    stage3 = f"{motion}, uneven eyes, open mouth, {sfx}"
    stage4 = f"cum, ahegao, tongue out, {motion}, {sfx}"
    
    if mouth_blocked:
        stage1 = stage1.replace("clenched teeth", "gagged")
        stage2 = stage2.replace("clenched teeth", "gagged")
        stage3 = stage3.replace("open mouth", "gagged") 
        stage4 = stage4.replace("ahegao, tongue out", "gagged")
    
    # Stage 5
    after_sex = "1girl, after sex, cum, cum in pussy, cumdrip, ejaculation, female pubic hair, groin, navel, nude, pubic hair, pussy juice, solo, sweat, thighs, x-ray, pussy, completely nude, nipples, solo focus"
    if pose == "Missionary":
        after_sex += ", lying"
    else:
        after_sex += ", all fours"
    
    stages = [
        f"{clean_base_prompt}, x-ray, {stage1}",
        f"{clean_base_prompt}, x-ray, {stage2}",
        f"{clean_base_prompt}, x-ray, {stage3}",
        f"{clean_base_prompt}, x-ray, {stage4}",
        f"{after_sex}"
    ]
    
    output.delete("1.0", tk.END)
    for i, stage in enumerate(stages, 1):
        output.insert(tk.END, f"{i}. {stage}\n")

root = tk.Tk()
root.title("Danbooru Stages Pro")
root.geometry("900x700")

tk.Label(root, text="Base Prompt:").pack(pady=5)
entry = scrolledtext.ScrolledText(root, height=5)
entry.pack(pady=5, padx=20)

tk.Label(root, text="Pose giai đoạn 5:").pack(pady=(20,5))
pose_var = tk.StringVar(value="Missionary")
ttk.Combobox(root, textvariable=pose_var, values=["Missionary", "All Fours"], state="readonly").pack()

tk.Button(root, text="Generate", command=generate, bg="#4CAF50", fg="white").pack(pady=20)

output = scrolledtext.ScrolledText(root, height=28)
output.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)

root.mainloop()
