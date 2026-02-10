import re
from pathlib import Path
from typing import List, Set, Callable, Optional

TITLE = "Advanced Tag Enhancer v8 - Faceless/Bald/Fat Only (SPEC COMPLIANT)"

# =========================== CONFIG (GIỮ NGUYÊN) ===========================
FOLDER_TO_PROCESS = Path(r"D:\zhangyao\1-old\[PIXIV] Noi [810034] [AI Generated] [12]-1280x\1 đã xuất excel")
FOLDER_TO_REMOVE = Path(r".\wantremove")
OUTPUT_FOLDER = FOLDER_TO_PROCESS / "outtags"
OUTPUT_FOLDER.mkdir(exist_ok=True)

ALLTAGS_TXT = OUTPUT_FOLDER / "alltags.txt"
HOP_TXT = OUTPUT_FOLDER / "hoptxt.txt"
ALLTAG_UNIQUE_TXT = OUTPUT_FOLDER / "alltag.txt"
ADDFACELESS_TXT = OUTPUT_FOLDER / "addfaceless20260108improved.txt"

# =========================== ANIMAL EAR TAGS (GIỮ NGUYÊN) ===========================
ANIMAL_EAR_TAGS: Set[str] = {
    "animal ears", "bat ears", "bear ears", "rabbit ears", "cat ears", "cow ears",
    "deer ears", "dog ears", "ferret ears", "fox ears", "goat ears", "horse ears",
    "lion ears", "monkey ears", "mouse ears", "panda ears", "pikachu ears",
    "pig ears", "raccoon ears", "sheep ears", "squirrel ears", "tiger ears",
    "wolf ears", "floppy ears"
}

# =========================== CORE CONSTANTS (CẬP NHẬT) ===========================
TAG_FAT: Set[str] = {"fat man"}
TAG_FACELESS: Set[str] = {"faceless male", "bald"}

# Triggers (poses ẩn mặt nam - hidden male face)
FACELESS_TRIGGERS: Set[str] = {
    "pov hands", "pov", "grabbing", "head grab", "arm grab", "irrumatio",
    "pov crotch", "bound arms", "from behind", "doggystyle", "prone bone",
    "reverse cowgirl position", "all fours", "sex from behind", "bent over"
}

# NO_ADD (front-facing/visible male)
NON_FACELESS_POSES: Set[str] = {
    "missionary", "mating press", "folded", "legs up", "boy on top",
    "lying", "on back", "from side", "french kiss", "kiss", "deep kiss",
    "oral", "fellatio", "blowjob", "breast sucking"
}

# NSFW keywords (để check prompt NSFW hay không)
NSFW_KEYWORDS: Set[str] = {
    "cum", "sex", "vaginal", "anal", "nude", "pussy", "penetration", "penis",
    "fellatio", "deepthroat", "irrumatio", "bound", "restrained", "rape",
    "creampie", "ejaculation", "orgasm", "breast", "nipples", "fucking",
    "cock", "dick", "fuck", "cunt", "bitch", "whore"
}

# Tags để thêm ở đầu nếu trigger
CORE_ENHANCE_TAGS: List[str] = ["((bald))", "((faceless male))", "((fat man))"]

# =========================== UTILITY FUNCTIONS ===========================

def load_remove_tags(folder: Path) -> Set[str]:
    """Load tags không mong muốn từ wantremove.txt"""
    remove: Set[str] = set()
    for p in folder.glob("*.txt"):
        text = p.read_text(encoding="utf-8")
        remove.update(t.strip() for t in text.split(",") if t.strip())
    return remove

def split_tags(line: str) -> List[str]:
    """Split comma-separated tags"""
    return [t.strip() for t in line.strip().split(",") if t.strip()]

def write_lines(path: Path, lines: List[str]) -> None:
    """Write lines to file"""
    path.write_text("\n".join(lines), encoding="utf-8")

def normalize_tag(t: str) -> str:
    """Remove (( )) để check trùng"""
    core = re.sub(r'^[(\[<{]+|[)\]>}]+$', "", t.strip()).strip()
    return core.lower()

def has_normalized(tags: Set[str], target: str) -> bool:
    """Check if tag exists (plain or weighted)"""
    lower_norm = {normalize_tag(x) for x in tags}
    return normalize_tag(target) in lower_norm

def add_weighted_if_missing(
    tags: Set[str],
    weighted_tag: str,
    log_callback: Optional[Callable[[str], None]] = None
) -> bool:
    """Add weighted tag nếu chưa có - return True if added"""
    if not has_normalized(tags, weighted_tag):
        tags.add(weighted_tag)
        if log_callback:
            log_callback(f"Added: {weighted_tag}")
        return True
    return False

# =========================== HELPER FUNCTIONS (NEW) ===========================

def is_nsfw(tags_set: Set[str]) -> bool:
    """Check if tags contain NSFW content"""
    return any(any(k in t.lower() for k in NSFW_KEYWORDS) for t in tags_set)

def has_pose(tags_set: Set[str], pose_set: Set[str]) -> bool:
    """Check if any pose in pose_set exists in tags"""
    return any(pose in tags_set for pose in pose_set)

def has_closed_eyes_or_side(tags_set: Set[str]) -> bool:
    """Check if has closed eyes or from side (NO ADD condition)"""
    return "closed eyes" in tags_set or "from side" in tags_set

def is_visible_male(tags_set: Set[str]) -> bool:
    """Check if male is visible (looking at viewer)"""
    return "looking at viewer" in tags_set

def is_kiss(tags_set: Set[str]) -> bool:
    """Check if kiss-related tags present"""
    return any(t in tags_set for t in {"kiss", "french kiss", "deep kiss"})

def is_sucking(tags_set: Set[str]) -> bool:
    """Check if sucking/oral-related tags present"""
    return any(t in tags_set for t in {"fellatio", "oral", "sucking", "deepthroat", "blowjob"})

def should_remove_xray(tags_set: Set[str]) -> bool:
    """Check if should remove x-ray tag"""
    return ("1girl" in tags_set or "1boy" in tags_set) and ("oral" in tags_set or "fellatio" in tags_set)

def should_keep_tail(tags_set: Set[str]) -> bool:
    """Check if should keep tail (cosplay or fake tail)"""
    has_cosplay = any("cosplay" in t.lower() for t in tags_set)
    has_fake_tail = any("fake tail" in t.lower() or "faketail" in t.lower() for t in tags_set)
    return has_cosplay or has_fake_tail

# =========================== BUILD ALLTAGS (GIỮ NGUYÊN LOGIC CŨ) ===========================

def build_all_tags(folder: Path, base_remove: Set[str], outpath: Path) -> None:
    """Build all_tags.txt từ folder - giữ nguyên logic xóa/lọc"""
    lines_out: List[str] = []
    
    for txt in sorted(folder.glob("*.txt")):
        raw_tags = split_tags(txt.read_text(encoding="utf-8"))
        tagset = set(raw_tags)
        
        # ========== LOGIC CŨ: Xử lý animal ears ==========
        has_fake_ears = "fake animal ears" in tagset
        temp_remove = base_remove - ANIMAL_EAR_TAGS if has_fake_ears else base_remove | ANIMAL_EAR_TAGS
        
        # ========== LOGIC CŨ: Xóa x-ray nếu oral ==========
        if should_remove_xray(tagset):
            temp_remove.add("x-ray")
        
        # ========== LOGIC CŨ: Xử lý tail ==========
        has_tail = any("tail" in t.lower() for t in tagset)
        if has_tail and not should_keep_tail(tagset):
            tailtags = {t for t in tagset if "tail" in t.lower()}
            temp_remove.update(tailtags)
        
        # ========== LOGIC CŨ: Lọc tags + thêm uncensored ==========
        kepttags = [t for t in raw_tags if t not in temp_remove]
        tagstring = ", ".join(kepttags)
        
        # Thêm uncensored nếu NSFW
        if is_nsfw(tagset) and "uncensored" not in tagset and "censored" not in tagset and "mosaic censoring" not in tagset:
            tagstring = tagstring + ", uncensored"
        
        # ========== LOGIC CŨ: Thêm bald cho kiss/lick ==========
        special_keywords = {"kiss", "lim", "lick", "breast sucking"}
        if any(any(kw in t.lower() for kw in special_keywords) for t in tagset) and "bald" not in tagset:
            tagstring = tagstring + ", bald"
        
        lines_out.append(tagstring)
        print(f"  ✓ {txt.name}")
    
    write_lines(outpath, lines_out)
    print(f"✅ Built {outpath}\n")

# =========================== EXTRACT FUNCTIONS (GIỮ NGUYÊN) ===========================

def extract_parentheses_tags(inpath: Path, outpath: Path) -> None:
    """Extract tags có ngoặc"""
    tags = {
        t
        for line in inpath.read_text(encoding="utf-8").splitlines()
        for t in split_tags(line)
        if "(" in t and ")" in t
    }
    write_lines(outpath, [", ".join(sorted(tags))])
    print(f"✅ Extracted parentheses → {outpath}\n")

def extract_unique_tags(inpath: Path, outpath: Path) -> None:
    """Extract unique tags"""
    unique = {
        t
        for line in inpath.read_text(encoding="utf-8").splitlines()
        for t in split_tags(line)
    }
    write_lines(outpath, [", ".join(sorted(unique))])
    print(f"✅ Extracted unique → {outpath}\n")

# =========================== ADVANCED TAG ENHANCE (LOGIC MỚI - SPEC COMPLIANT) ===========================

def advanced_tag_enhance(
    inpath: Path,
    outpath: Path,
    log_callback: Optional[Callable[[str], None]] = print
) -> None:
    """
    ⭐ Advanced enhancement với logic SPEC COMPLIANT:
    
    RULE 1: Nhấn mạnh bound/restrained
    RULE 2: Check kiss/sucking special cases
    RULE 3: Check pose-based rules (FACELESS_TRIGGERS vs NON_FACELESS_POSES)
    RULE 4: Thêm core tags (faceless, bald, fat) nếu đủ điều kiện
    RULE 5: Đảm bảo bound ở đầu prompts
    """
    lines_out: List[str] = []
    added_count = 0
    
    print("=" * 70)
    print("🚀 ADVANCED TAG ENHANCE - SPEC COMPLIANT")
    print("   Logic: Pose-based (FACELESS_TRIGGERS vs NON_FACELESS_POSES)")
    print("   Core Tags: ((faceless male)), ((bald)), ((fat man))")
    print("   NO: dark-skinned, old man, ugly man, interracial")
    print("=" * 70 + "\n")
    
    for line_num, line in enumerate(inpath.read_text(encoding="utf-8").splitlines(), 1):
        raw_list = split_tags(line)
        tags_set = set(raw_list)
        final_tags: Set[str] = set(tags_set)
        
        added_this_line = []
        
        # ========== RULE 1: Nhấn mạnh Bound/Restrained ==========
        if "bound" in tags_set or "restrained" in tags_set:
            if add_weighted_if_missing(final_tags, "((1girl, bound, restrained))", log_callback):
                added_this_line.append("BOUND")
        
        # ========== RULE 2: Check Special Cases (Kiss/Sucking) ==========
        is_kiss_scene = is_kiss(tags_set)
        is_sucking_scene = is_sucking(tags_set)
        has_closed = has_closed_eyes_or_side(tags_set)
        is_visible = is_visible_male(tags_set)
        
        # ========== RULE 3: Decide NO_ADD Condition ==========
        has_non_faceless_pose = has_pose(tags_set, NON_FACELESS_POSES)
        
        no_add_faceless = (
            has_non_faceless_pose or
            (is_kiss_scene and has_closed) or
            (is_sucking_scene and has_closed and not is_visible)
        )
        
        # ========== RULE 4: Decide SHOULD_ADD Faceless ==========
        should_add_faceless = (
            (has_pose(tags_set, FACELESS_TRIGGERS) or is_kiss_scene or is_sucking_scene) and
            not no_add_faceless and
            is_nsfw(tags_set)
        )
        
        # ========== ADD CORE TAGS ==========
        if should_add_faceless:
            for tag in CORE_ENHANCE_TAGS:
                if add_weighted_if_missing(final_tags, tag, log_callback):
                    added_this_line.append(tag.replace("((", "").replace("))", ""))
        
        # ========== ADD UNCENSORED nếu NSFW ==========
        if is_nsfw(tags_set):
            if add_weighted_if_missing(final_tags, "uncensored", log_callback):
                if "uncensored" not in added_this_line:
                    added_this_line.append("uncensored")
        
        # ========== RULE 5: BUILD OUTPUT (Bound ở Đầu) ==========
        bound_tag = None
        other_tags = []
        for t in final_tags:
            if "bound" in t.lower() and "restrained" in t.lower() and "1girl" in t.lower():
                bound_tag = t
            else:
                other_tags.append(t)
        
        if bound_tag:
            output_tags = [bound_tag] + sorted(other_tags)
        else:
            output_tags = sorted(final_tags)
        
        tagstring = ", ".join(output_tags)
        lines_out.append(tagstring)
        
        # ========== LOG ==========
        if added_this_line:
            added_count += 1
            preview = line[:55].replace(",", ", ")
            log_callback(f"L{line_num:4d}: +{', '.join(added_this_line):20s} | {preview}...")
    
    write_lines(outpath, lines_out)
    
    print("\n" + "=" * 70)
    print(f"✅ HOÀN THÀNH!")
    print(f"   📊 Lines được enhance: {added_count}")
    print(f"   💾 Output: {outpath}")
    print("=" * 70 + "\n")

# =========================== MAIN PROCESS ===========================

def process_tags(callback=print):
    """Main process - chạy tất cả steps"""
    print(f"\n{TITLE}\n")
    
    print("1️⃣ Load remove tags...")
    base_remove = load_remove_tags(FOLDER_TO_REMOVE)
    for variant in {"fake animal ears", "fakeanimalears", "fake anime ears"}:
        base_remove.discard(variant)
    callback(f"✓ Loaded {len(base_remove)} remove tags\n")
    
    print("2️⃣ Build all_tags (với logic cũ)...")
    build_all_tags(FOLDER_TO_PROCESS, base_remove, ALLTAGS_TXT)
    
    print("3️⃣ Extract parentheses tags...")
    extract_parentheses_tags(ALLTAGS_TXT, HOP_TXT)
    
    print("4️⃣ Extract unique tags...")
    extract_unique_tags(ALLTAGS_TXT, ALLTAG_UNIQUE_TXT)
    
    print("5️⃣ Advanced enhance (logic mới)...")
    advanced_tag_enhance(ALLTAGS_TXT, ADDFACELESS_TXT, callback)
    
    callback("🎉 ALL DONE!\n")

# =========================== MAIN ===========================

if __name__ == "__main__":
    process_tags()
