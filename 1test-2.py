import tkinter as tk
from tkinter import filedialog, ttk
from pathlib import Path
import re
import subprocess
import sys
from typing import Set, List, Tuple

DEFAULT_FOLDER = Path.home()

# ===== TIER SYSTEM =====

def extract_tags_for_analysis(line: str) -> Set[str]:
    """
    Extract tags for analysis WITHOUT destroying grouping structure
    Simply remove all parentheses and split
    """
    clean_line = line.replace('(', '').replace(')', '')
    return set(tag.strip() for tag in clean_line.split(',') if tag.strip())


# ===== STATEFUL TIERS (run separately, maintain state across lines) =====

def tier_0_exposure_persistence(current_tags: Set[str], previous_exposed_state: dict) -> Tuple[List[str], dict]:
    """
    TIER 0: Exposure State Persistence
    Maintains exposed body parts across sequential lines
    Returns: (tags_to_add, updated_exposed_state)
    """
    tags_to_add = []
    
    # Define exposure indicators
    EXPOSED_BREASTS = {'breasts out', 'breasts_out', 'nipples', 'nipple', 'areolae'}
    EXPOSED_PUSSY = {'pussy', 'spread pussy', 'spread_pussy', 'pussy juice', 'pussy_juice'}
    EXPOSED_ANUS = {'anus', 'spread anus', 'spread_anus', 'puckered anus', 'puckered_anus'}
    
    # Scene change/reset indicators
    SCENE_RESET = {'solo', 'standing', 'walking', 'sitting', 'fully clothed', 'clothed'}
    COVERAGE_TAGS = {'covered', 'dressed', 'bra', 'panties on'}
    
    # Check if scene reset
    scene_changed = bool(current_tags & SCENE_RESET)
    covered = bool(current_tags & COVERAGE_TAGS)
    
    if scene_changed or covered:
        return [], {'breasts': False, 'pussy': False, 'anus': False}
    
    # Current exposure state
    current_exposed = {
        'breasts': bool(current_tags & EXPOSED_BREASTS),
        'pussy': bool(current_tags & EXPOSED_PUSSY),
        'anus': bool(current_tags & EXPOSED_ANUS)
    }
    
    # Check for sexual context
    SEXUAL_CONTEXT = {'hetero', 'sex', 'vaginal', 'missionary', 'doggystyle', 
                      'imminent penetration', 'imminent vaginal', 'penis', 
                      'rape', 'restrained', 'bound', 'bdsm', 'spread legs'}
    
    in_sexual_context = bool(current_tags & SEXUAL_CONTEXT)
    
    # Maintain exposure from previous state
    if in_sexual_context:
        if previous_exposed_state.get('breasts', False) and not current_exposed['breasts']:
            tags_to_add.extend(['breasts out', 'nipples'])
            current_exposed['breasts'] = True
        
        if previous_exposed_state.get('pussy', False) and not current_exposed['pussy']:
            tags_to_add.append('pussy')
            current_exposed['pussy'] = True
        
        if previous_exposed_state.get('anus', False) and 'anal' in current_tags and not current_exposed['anus']:
            tags_to_add.append('anus')
            current_exposed['anus'] = True
    
    # Update exposure state for next line
    new_state = {
        'breasts': current_exposed['breasts'] or previous_exposed_state.get('breasts', False),
        'pussy': current_exposed['pussy'] or previous_exposed_state.get('pussy', False),
        'anus': current_exposed['anus']
    }
    
    return tags_to_add, new_state


def tier_1_clothing_transition(current_tags: Set[str], previous_had_panty_pull: bool) -> Tuple[List[str], bool]:
    """
    TIER 1: Clothing State Transition
    Rules:
    1. If current line has "panty pull" → add "panties" to current line
    2. If previous line had "panty pull" → add "unworn_panties" to current line (once only)
    Returns: (tags_to_add, current_has_panty_pull)
    """
    tags_to_add = []
    
    # Check if current line has panty pull
    PANTY_PULL_TAGS = {'panty pull', 'panty_pull', 'panties pull', 'panties_pull'}
    current_has_panty_pull = bool(current_tags & PANTY_PULL_TAGS)
    
    # RULE 1: If CURRENT line has panty pull → add "panties"
    if current_has_panty_pull:
        PANTY_TAGS = {'panties', 'panty', 'underwear'}
        if not (current_tags & PANTY_TAGS):
            tags_to_add.append('panties')
    
    # RULE 2: If PREVIOUS line had panty pull → add "unworn_panties" to THIS line
    if previous_had_panty_pull:
        UNWORN_TAGS = {'unworn_panties', 'unworn panties', 'panties aside', 'panties_aside', 
                       'panties around one leg', 'panties_around_one_leg'}
        if not (current_tags & UNWORN_TAGS):
            tags_to_add.append('unworn_panties')
    
    return tags_to_add, current_has_panty_pull


# ===== STATELESS TIERS (single line processing) =====

def tier_4_detect_clothing_pull(tags: Set[str]) -> List[str]:
    """
    TIER 4: Clothing Pull Detection
    Returns: tags_to_add
    """
    tags_to_add = []
    
    # Rule 1: Breasts + Dress → dress lift, breasts out
    if 'breasts' in tags and 'dress' in tags:
        if 'dress lift' not in tags:
            tags_to_add.append('dress lift')
        if 'breasts out' not in tags:
            tags_to_add.append('breasts out')
    
    # Rule 2: Pussy + Pelvic Curtain → pelvic curtain lift
    if 'pussy' in tags and 'pelvic_curtain' in tags:
        if 'pelvic curtain lift' not in tags:
            tags_to_add.append('pelvic curtain lift')
    
    # Rule 3: Pussy + Dress (no pelvic) → dress lift, pussy
    if 'pussy' in tags and 'dress' in tags and 'pelvic_curtain' not in tags:
        if 'dress lift' not in tags:
            tags_to_add.append('dress lift')
        if 'pussy' not in tags:
            tags_to_add.append('pussy')
    
    return tags_to_add


# ===== TIER PROCESSOR =====

def process_stateless_tiers(tags_set: Set[str]) -> Tuple[List[str], dict]:
    """
    Process single line through all stateless tiers
    Returns: (all_new_tags, tier_statistics)
    """
    tiers = [
        ("TIER 4", tier_4_detect_clothing_pull),
        # Add more stateless tiers here:
        # ("TIER 5", tier_5_function),
        # ("TIER 6", tier_6_function),
    ]
    
    tier_stats = {}
    all_new_tags = []
    
    for tier_name, tier_func in tiers:
        new_tags = tier_func(tags_set)
        
        if new_tags:
            all_new_tags.extend(new_tags)
            tier_stats[tier_name] = {
                'added': len(new_tags),
                'tags_added': new_tags.copy()
            }
    
    return all_new_tags, tier_stats


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
    'red_eyes', 'blue_eyes', 'green_eyes', 'brown_eyes', 'yellow_eyes', 'purple_eyes',
    'heterochromia', 'multicolored_eyes', 'golden_eyes', 'pink_eyes', 'grey_eyes',
    'pupils', 'slit pupils', 'crossed_eyes', 'heart-shaped_pupils', 'glowing_eyes',
    'eyelashes', 'colored_eyelashes', 'long_eyelashes', 'thick_eyelashes',
    'eyeshadow', 'mascara', 'eyeliner', 'makeup', 'cosmetics'
}

FACING_AWAY_TAGS = {
    'facing away', 'facing_away', 'from behind', 'back turned', 'back view'
}


def load_tags_from_file(filepath: Path) -> Set[str]:
    """Load comma-separated tags from a txt file, handle parenthetical aliases."""
    tags = set()
    if not filepath.exists():
        return tags
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    for raw in content.split(','):
        raw = raw.strip()
        if not raw:
            continue
        paren_match = re.match(r'^(.+?)\s*\((.+?)\)\s*$', raw)
        if paren_match:
            tags.add(paren_match.group(1).strip().lower())
            tags.add(paren_match.group(2).strip().lower())
        else:
            tags.add(raw.lower())
    return tags


def build_facing_away_remove_tags(script_dir: Path) -> Set[str]:
    """Load eyes + face + bangs tags to remove when facing away detected."""
    head_dir = script_dir / "wantremove-head"
    tags = set()
    for fname in ("eyes.txt", "face.txt", "bangs.txt"):
        tags |= load_tags_from_file(head_dir / fname)
    return tags

COVERED_EYES_TAGS = {
    'covered_eyes', 'blindfold', 'eyepatch', 'hair_over_eyes', 'eyes_visible_through_hair',
    'black_blindfold'
}


def extract_lora_fullname(user_prompt):
    match = re.search(r'<lora:([^:>]+):', user_prompt)
    if match:
        return match.group(1)
    return "unknown"


def clean_prompt_tags(user_prompt, base_tags):
    """
    Clean user prompt by removing conflicting eye/covered_eyes tags
    Returns None if should skip line, otherwise returns cleaned prompt
    """
    prompt_tags = set(tag.strip() for tag in user_prompt.split(','))
    
    # Check black_blindfold
    if 'black_blindfold' in base_tags:
        return None
    
    # Remove eye tags if covered_eyes in base
    if base_tags & COVERED_EYES_TAGS:
        prompt_tags -= EYE_TAGS
    
    # Remove covered_eyes if eye tags in base
    if base_tags & EYE_TAGS:
        prompt_tags -= COVERED_EYES_TAGS
    
    return ', '.join(tag for tag in prompt_tags if tag)


def process_character_txt(folder, user_prompt):
    """
    Process addfaceless.txt → character.txt with tier system
    PRESERVES GROUPING STRUCTURE - only appends new tags
    """
    output_folder = folder / "out_tags"
    addfaceless_file = output_folder / "addfaceless.txt"
    
    if not addfaceless_file.exists():
        return False, "❌ Không tìm thấy addfaceless.txt"
    
    lora_full_name = extract_lora_fullname(user_prompt)
    char_filename = f"{lora_full_name}-character.txt"
    char_file = output_folder / char_filename

    script_dir = Path(__file__).parent
    facing_away_remove = build_facing_away_remove_tags(script_dir)

    try:
        with open(addfaceless_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        with open(char_file, 'w', encoding='utf-8') as out:
            processed = 0
            skipped = 0
            black_blindfold_skip = 0
            
            # Tier statistics aggregation
            tier_stats_summary = {
                'TIER 0': 0,
                'TIER 1': 0
            }
            facing_away_count = 0
            mating_press_skip = 0
            stateless_tier_stats = {}
            
            # TIER 0: Track exposure state across lines
            exposed_state = {'breasts': False, 'pussy': False, 'anus': False}
            
            # TIER 1: Track panty pull state
            previous_had_panty_pull = False
            
            for base_line in lines:
                # Extract tags for analysis WITHOUT destroying structure
                base_tags = extract_tags_for_analysis(base_line)
                
                # Skip: mating press + ass focus
                if {'mating press', 'ass focus'} <= base_tags or \
                   {'mating_press', 'ass_focus'} <= base_tags or \
                   ({'mating press', 'ass_focus'} <= base_tags) or \
                   ({'mating_press', 'ass focus'} <= base_tags):
                    skipped += 1
                    mating_press_skip += 1
                    continue

                # Clean prompt
                clean_prompt = clean_prompt_tags(user_prompt, base_tags)
                if clean_prompt is None:
                    skipped += 1
                    if 'black_blindfold' in base_tags:
                        black_blindfold_skip += 1
                    continue
                
                # Collect all new tags to append
                tags_to_append = []
                
                # ===== STATEFUL TIERS =====
                
                # TIER 0: Exposure persistence
                tier0_tags, exposed_state = tier_0_exposure_persistence(
                    base_tags, exposed_state
                )
                if tier0_tags:
                    tags_to_append.extend(tier0_tags)
                    tier_stats_summary['TIER 0'] += len(tier0_tags)
                
                # TIER 1: Clothing transition (panty pull → panties + unworn_panties)
                tier1_tags, current_has_panty_pull = tier_1_clothing_transition(
                    base_tags, previous_had_panty_pull
                )
                if tier1_tags:
                    tags_to_append.extend(tier1_tags)
                    tier_stats_summary['TIER 1'] += len(tier1_tags)
                
                # Update panty pull state for NEXT line
                previous_had_panty_pull = current_has_panty_pull
                
                # ===== STATELESS TIERS =====
                
                # Apply all stateless tiers
                stateless_new_tags, stateless_stats = process_stateless_tiers(base_tags)
                if stateless_new_tags:
                    tags_to_append.extend(stateless_new_tags)
                
                # Aggregate stateless tier statistics
                for tier_name, stats in stateless_stats.items():
                    if tier_name not in stateless_tier_stats:
                        stateless_tier_stats[tier_name] = {'added': 0}
                    stateless_tier_stats[tier_name]['added'] += stats['added']
                
                # ===== BUILD FINAL LINE =====
                
                # PRESERVE original + append new tags
                final_line = base_line
                
                if tags_to_append:
                    # Remove duplicates
                    unique_new_tags = []
                    for tag in tags_to_append:
                        if tag not in base_tags:
                            unique_new_tags.append(tag)
                    
                    if unique_new_tags:
                        final_line = f"{base_line}, {', '.join(unique_new_tags)}"
                
                # ===== FACING AWAY: loại tags mắt/face/bangs khỏi prompt =====
                if base_tags & FACING_AWAY_TAGS:
                    prompt_parts = [t.strip() for t in clean_prompt.split(',')]
                    prompt_parts = [t for t in prompt_parts if t.lower() not in facing_away_remove]
                    clean_prompt = ', '.join(prompt_parts)
                    facing_away_count += 1

                # Add user prompt
                full_prompt = f"{final_line}, {clean_prompt}"
                
                out.write(full_prompt + '\n')
                processed += 1
            
            # Build result message
            msg = f"✅ {processed}/{len(lines)} lines (skip {skipped})"
            
            if black_blindfold_skip > 0:
                msg += f"\n🔒 black_blindfold: {black_blindfold_skip} cases"

            if mating_press_skip > 0:
                msg += f"\n⛔ mating press+ass focus (skipped): {mating_press_skip} lines"

            if facing_away_count > 0:
                msg += f"\n👁️ facing away (removed eyes/face/bangs): {facing_away_count} lines"
            
            # Add stateful tier statistics
            if tier_stats_summary['TIER 0'] > 0:
                msg += f"\n🔧 TIER 0 (Exposure Persistence): +{tier_stats_summary['TIER 0']} tags"
            
            if tier_stats_summary['TIER 1'] > 0:
                msg += f"\n🔧 TIER 1 (Clothing Transition): +{tier_stats_summary['TIER 1']} tags"
            
            # Add stateless tier statistics
            for tier_name, stats in stateless_tier_stats.items():
                if stats['added'] > 0:
                    msg += f"\n🔧 {tier_name}: +{stats['added']} tags"
            
            msg += f"\n📁 {char_filename}"
            
            return True, msg
            
    except Exception as e:
        return False, f"💥 Lỗi: {e}"


# ===== CLASS GUI =====

class TagEnhancerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Tag Enhancer v12.6 → Character TXT (TIER 0+1+4)")
        self.root.geometry("900x600")
        self.root.resizable(True, True)
        self.folder_path = tk.StringVar(value=str(DEFAULT_FOLDER))
        self.setup_ui()
        self.log("🎯 Tag Enhancer v12.6 + Character Processor (TIER 0+1+4)")
    
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
        
        ttk.Entry(entry_frame, textvariable=self.folder_path, 
                  font=("Consolas", 11)).pack(side="left", fill="x", expand=True, padx=(0,10))
        ttk.Button(entry_frame, text="Browse", 
                   command=self.browse_folder).pack(side="right")
        
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
        prompt_frame = ttk.LabelFrame(main_frame, text="💬 PROMPT (cần <lora:...>)", padding="15")
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
        if folder:
            self.folder_path.set(folder)
    
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
