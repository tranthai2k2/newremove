import re
from pathlib import Path
from typing import List, Set, Callable, Optional

TITLE = "Advanced Tag Enhancer v8.1 - Missionary Rules Updated ✅"

# =========================== CONFIG ===========================
FOLDER_TO_PROCESS = Path(r"D:\zhangyao\1-old\[PIXIV] Noi [810034] [AI Generated] [12]-1280x\2 đã xuất excel")
FOLDER_TO_REMOVE = Path(r".\wantremove")

OUTPUT_FOLDER = FOLDER_TO_PROCESS / "out_tags"
OUTPUT_FOLDER.mkdir(exist_ok=True)

ALLTAGS_TXT = OUTPUT_FOLDER / "all_tags.txt"
HOP_TXT = OUTPUT_FOLDER / "hop_txt.txt"
ALLTAG_UNIQUE_TXT = OUTPUT_FOLDER / "all_tag.txt"
ADDFACELESS_TXT = OUTPUT_FOLDER / "addfaceless.txt"

# =========================== CORE TAGS ===========================
CORE_FAT_MAN = ["((fat man))"]
CORE_FACELESS = ["((faceless male))", "((bald))"]

# Missionary special triggers
MISSIONARY_TRIGGERS = {"missionary"}
KISS_TRIGGERS = {"kiss", "french kiss", "deep kiss"}
BREAST_SUCKING_TRIGGERS = {"breast sucking", "breast_sucking", "breastfeeding", "licking nipple", "nipple sucking"}

# Face hiding triggers (giữ nguyên)
FACELESS_TRIGGERS = {
    "pov hands", "pov", "grabbing", "head grab", "arm grab", "irrumatio",
    "pov crotch", "bound arms", "from behind", "doggystyle", "prone bone",
    "reverse cowgirl position", "all fours", "sex from behind", "bent over"
}

NON_FACELESS_POSES = {
    "cowgirl position", "missionary", "mating press", "breast sucking"
}

NSFW_KEYWORDS = {
    "cum", "sex", "vaginal", "anal", "nude", "pussy", "penetration", "penis",
    "fellatio", "deepthroat", "irrumatio", "bound", "restrained", "rape"
}

ANIMAL_EAR_TAGS = {
    "animal ears", "bat ears", "bear ears", "rabbit ears", "cat ears", 
    "cow ears", "deer ears", "dog ears", "fox ears", "wolf ears"
}

# =========================== UTILITY FUNCTIONS ===========================
def load_remove_tags(folder: Path) -> Set[str]:
    remove = set()
    for p in folder.glob("*.txt"):
        text = p.read_text(encoding="utf-8")
        remove.update(t.strip() for t in text.split(",") if t.strip())
    return remove

def split_tags(line: str) -> List[str]:
    return [t.strip() for t in line.strip().split(",") if t.strip()]

def write_lines(path: Path, lines: List[str]) -> None:
    path.write_text("\n".join(lines), encoding="utf-8")

def normalize_tag(t: str) -> str:
    core = re.sub(r'^[(\[<{]+|[)\]>}]+$', "", t.strip()).strip()
    return core.lower()

def has_normalized(tags: Set[str], target: str) -> bool:
    lower_norm = {normalize_tag(x) for x in tags}
    return normalize_tag(target) in lower_norm

def add_weighted_if_missing(tags: Set[str], weighted_tag: str) -> bool:
    if not has_normalized(tags, weighted_tag):
        tags.add(weighted_tag)
        return True
    return False

def is_nsfw(tags_set: Set[str]) -> bool:
    return any(any(k in t.lower() for k in NSFW_KEYWORDS) for t in tags_set)

def has_pose(tags_set: Set[str], pose_set: Set[str]) -> bool:
    return any(pose in tags_set for pose in pose_set)

# =========================== BUILD ALLTAGS ===========================
def build_all_tags(folder: Path, base_remove: Set[str], outpath: Path) -> None:
    lines_out = []
    for txt in sorted(folder.glob("*.txt")):
        raw_tags = split_tags(txt.read_text(encoding="utf-8"))
        tagset = set(raw_tags)
        
        # Animal ears logic
        has_fake_ears = "fake animal ears" in tagset
        temp_remove = base_remove - ANIMAL_EAR_TAGS if has_fake_ears else base_remove | ANIMAL_EAR_TAGS
        
        # X-ray removal
        if ("1girl" in tagset or "1boy" in tagset) and ("oral" in tagset or "fellatio" in tagset):
            temp_remove.add("x-ray")
        
        # Tail removal
        has_tail = any("tail" in t.lower() for t in tagset)
        if has_tail and not any("cosplay" in t.lower() or "fake tail" in t.lower() for t in tagset):
            tailtags = {t for t in tagset if "tail" in t.lower()}
            temp_remove.update(tailtags)
        
        kepttags = [t for t in raw_tags if t not in temp_remove]
        tagstring = ", ".join(kepttags)
        
        # Add uncensored for NSFW
        if is_nsfw(tagset) and "uncensored" not in tagset:
            tagstring += ", uncensored"
        
        lines_out.append(tagstring)
    
    write_lines(outpath, lines_out)

# =========================== EXTRACT FUNCTIONS ===========================
def extract_parentheses_tags(inpath: Path, outpath: Path) -> None:
    tags = {t for line in inpath.read_text(encoding="utf-8").splitlines() 
            for t in split_tags(line) if "(" in t and ")" in t}
    write_lines(outpath, [", ".join(sorted(tags))])

def extract_unique_tags(inpath: Path, outpath: Path) -> None:
    unique = {t for line in inpath.read_text(encoding="utf-8").splitlines() 
              for t in split_tags(line)}
    write_lines(outpath, [", ".join(sorted(unique))])

# =========================== V8.1 ENHANCEMENT LOGIC ===========================
def advanced_tag_enhance_v81(inpath: Path, outpath: Path) -> None:
    print("=" * 70)
    print("🚀 V8.1 ADVANCED ENHANCE - NEW MISSIONARY RULES")
    print("   ✅ Missionary → ALWAYS ((fat man))")
    print("   ✅ Missionary + kiss/breast sucking → ((faceless male)) + ((bald))")
    print("=" * 70)
    
    lines_out = []
    enhanced_count = 0
    
    for line_num, line in enumerate(inpath.read_text(encoding="utf-8").splitlines(), 1):
        raw_list = split_tags(line)
        tags_set = set(raw_list)
        final_tags: Set[str] = set(tags_set)
        
        added_this_line = []
        
        # ========== NEW V8.1: MISSIONARY RULES ==========
        has_missionary = has_pose(tags_set, MISSIONARY_TRIGGERS)
        
        if has_missionary:
            # ALWAYS add fat man for missionary
            for tag in CORE_FAT_MAN:
                if add_weighted_if_missing(final_tags, tag):
                    added_this_line.append("fat_man")
            
            # Check special triggers: kiss OR breast sucking
            has_special_trigger = (
                has_pose(tags_set, KISS_TRIGGERS) or 
                has_pose(tags_set, BREAST_SUCKING_TRIGGERS)
            )
            
            if has_special_trigger:
                for tag in CORE_FACELESS:
                    if add_weighted_if_missing(final_tags, tag):
                        added_this_line.append(f"{tag.replace('((', '').replace('))', '')}")
                print(f"L{line_num:3d}: MISSIONARY + {'KISS' if has_pose(tags_set, KISS_TRIGGERS) else 'BREAST SUCKING'} → faceless+bald")
            
            enhanced_count += 1
        
        # ========== ORIGINAL FACELESS LOGIC (kept for other poses) ==========
        has_faceless_trigger = has_pose(tags_set, FACELESS_TRIGGERS)
        has_non_faceless_pose = has_pose(tags_set, NON_FACELESS_POSES)
        
        if has_faceless_trigger and not has_non_faceless_pose and is_nsfw(tags_set):
            for tag in CORE_FACELESS + CORE_FAT_MAN:
                if add_weighted_if_missing(final_tags, tag):
                    added_this_line.append(f"{tag.replace('((', '').replace('))', '')}")
        
        # Uncensored for NSFW
        if is_nsfw(tags_set) and not has_normalized(tags_set, "uncensored"):
            final_tags.add("uncensored")
        
        # Build output
        output_tags = sorted(final_tags)
        tagstring = ", ".join(output_tags)
        lines_out.append(tagstring)
        
        if added_this_line:
            preview = line[:50]
            print(f"L{line_num:3d}: +{', '.join(added_this_line)} | {preview}...")
    
    write_lines(outpath, lines_out)
    
    print("\n" + "=" * 70)
    print(f"✅ V8.1 COMPLETE! Enhanced: {enhanced_count} lines")
    print(f"💾 Output: {outpath}")
    print("=" * 70)

# =========================== MAIN ===========================
def main():
    print(f"\n{TITLE}\n")
    
    # Step 1: Load remove tags
    print("1️⃣ Loading remove tags...")
    base_remove = load_remove_tags(FOLDER_TO_REMOVE)
    print(f"   ✓ {len(base_remove)} tags loaded\n")
    
    # Step 2: Build all_tags
    print("2️⃣ Building all_tags...")
    build_all_tags(FOLDER_TO_PROCESS, base_remove, ALLTAGS_TXT)
    
    # Step 3: Extract hop tags
    print("3️⃣ Extracting hop tags...")
    extract_parentheses_tags(ALLTAGS_TXT, HOP_TXT)
    
    # Step 4: Extract unique tags
    print("4️⃣ Extracting unique tags...")
    extract_unique_tags(ALLTAGS_TXT, ALLTAG_UNIQUE_TXT)
    
    # Step 5: V8.1 Enhancement
    print("5️⃣ Running V8.1 enhancement...")
    advanced_tag_enhance_v81(ALLTAGS_TXT, ADDFACELESS_TXT)
    
    print("🎉 ALL COMPLETE!")
    print(f"📁 Output folder: {OUTPUT_FOLDER}")
    print("\nFiles created:")
    print(f"  📄 {ALLTAGS_TXT}")
    print(f"  📄 {HOP_TXT}") 
    print(f"  📄 {ALLTAG_UNIQUE_TXT}")
    print(f"  ⭐ {ADDFACELESS_TXT} ← MAIN OUTPUT")

if __name__ == "__main__":
    main()
