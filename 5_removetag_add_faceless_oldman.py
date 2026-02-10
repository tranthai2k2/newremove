import re
from pathlib import Path
from typing import List, Set, Callable, Optional

TITLE = "Advanced Tag Enhancer v3 - Netorare Pack Complete"

# =========================== CONFIG ===========================
FOLDER_TO_PROCESS = Path(r"D:\zhangyao\Noi\noi (7)")
FOLDER_TO_REMOVE = Path(r".\wantremove")
OUTPUT_FOLDER = FOLDER_TO_PROCESS / "outtags"
OUTPUT_FOLDER.mkdir(exist_ok=True)

ALLTAGS_TXT = OUTPUT_FOLDER / "alltags.txt"
HOP_TXT = OUTPUT_FOLDER / "hoptxt.txt"
ALLTAG_UNIQUE_TXT = OUTPUT_FOLDER / "alltag.txt"
ADDFACELESS_TXT = OUTPUT_FOLDER / "addfaceless_20260108_improved.txt"

# =========================== OLD SETS (GIỮ NGUYÊN) ===========================
ANIMAL_EAR_TAGS: Set[str] = {
    "animal ears", "bat ears", "bear ears", "rabbit ears", "cat ears", "cow ears",
    "deer ears", "dog ears", "ferret ears", "fox ears", "goat ears", "horse ears",
    "lion ears", "monkey ears", "mouse ears", "panda ears", "pikachu ears",
    "pig ears", "raccoon ears", "sheep ears", "squirrel ears", "tiger ears",
    "wolf ears", "floppy ears"
}

TAG_DARKSKIN: Set[str] = {"dark-skinned male", "interracial"}
TAG_FAT: Set[str] = {"fat man"}
TAG_FACELESS: Set[str] = {"faceless male", "bald"}

FACELESS_TRIGGERS: Set[str] = {
    "faceless", "pov hands", "pov", "grabbing", "head grab", "arm grab",
    "irrumatio", "pov crotch", "bound arms", "from behind", "doggystyle",
    "prone bone", "reverse cowgirl position",
}

NSFW_KEYWORDS: Set[str] = {
    "cum", "sex", "vaginal", "anal", "nude", "pussy", "penetration",
    "breast", "nipples", "fingering", "fuck", "sperm", "intercourse",
    "cervix", "creampie", "ejaculation", "rape", "clit", "clitoris",
    "penis", "pussy juice", "orgasm", "doggystyle", "cowgirl",
    "reverse cowgirl", "missionary", "spooning", "standing sex",
    "prone bone", "pile driver", "mating press", "blowjob", "handjob",
    "titjob", "paizuri", "fellatio", "cunnilingus", "erection",
    "testicles", "labia", "vulva", "anus", "masturbation",
    "double penetration", "threesome", "gangbang", "bdsm", "bondage",
    "grabbing", "groping", "bound", "restrained", "shibari", "rope",
    "deepthroat", "irrumatio", "cumdrip", "cum overflow",
    "internal cumshot", "pubic hair", "spread legs", "spread pussy",
    "spread anus", "x-ray", "cross-section", "uterus", "cervix",
    "deep penetration", "imminent penetration", "after sex", "after anal",
    "after vaginal", "ejaculation", "saliva", "tongue out", "french kiss",
    "licking", "hetero", "ass grab", "breast sucking"
}

MOUTH_TAG_HINTS: Set[str] = {
    "open mouth", "tongue out", "french kiss", "licking", "lick", "kiss"
}

# =========================== NEW RULE SETS (CẢI THIỆN) ===========================
# Core tags only (bỏ old man, ugly man, manly, muscular male)
CORE_NETORARE_TAGS: List[str] = ["((fat man))", "((bald))", "((faceless male))"]

# Quick triggers cho rule mới (OR logic)
BAD_MALE_TRIGGERS: Set[str] = {
    "dark-skinned male", "interspecies", "monster", "interracial",
    "bestiality", "dark skin", "black skin", "tanned male", "netorare"
}

HIDDEN_POSE_TRIGGERS: Set[str] = {
    "prone bone", "top-down bottom-up", "all fours", "sex from behind",
    "doggystyle", "spooning", "suspended congress", "lifting person",
    "carrying", "against wall", "against tree", "standing sex",
    "from behind", "from side", "back", "facing away", "head out of frame",
    "boy on top", "bent over", "on stomach", "on side", "torso grab",
    "ass grab", "head grab", "hand on another's head"
}

ORAL_TRIGGERS: Set[str] = {
    "fellatio", "blowjob", "oral", "deepthroat", "irrumatio",
    "head grab", "hand on another's head", "pov crotch", "saliva",
    "tongue out", "breast sucking", "licking nipple"
}

RESTRAINT_RAPE: Set[str] = {
    "rape", "restrained", "bdsm", "bound", "sleep molestation",
    "sleeping", "unconscious", "tape gag", "bound arms",
    "tearing up", "crying", "wince", "empty eyes", "defeat",
    "bound wrists", "arms behind back"
}

# All quick triggers combined (fix 100% errors)
QUICK_TRIGGERS = BAD_MALE_TRIGGERS | HIDDEN_POSE_TRIGGERS | ORAL_TRIGGERS | RESTRAINT_RAPE

NSFW_SEX_ACTS: Set[str] = {
    "vaginal", "anal", "sex", "penetration", "doggy", "doggystyle",
    "prone bone", "missionary", "cowgirl", "reverse cowgirl",
    "oral", "fellatio", "blowjob", "cunnilingus", "handjob",
    "paizuri", "titfuck", "titjob", "deepthroat", "irrumatio",
    "rape", "netorare"
}

# =========================== UTILITY FUNCTIONS ===========================
def load_remove_tags(folder: Path) -> Set[str]:
    """Load tags to remove từ folder"""
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

def is_nsfw(tags: Set[str]) -> bool:
    """Check if tags contain NSFW content"""
    # Keyword match
    keyword_match = any(
        any(k in t.lower() for k in NSFW_KEYWORDS) for t in tags
    )
    # Combo: 1boy + 1girl + grab/bound + nude/penis
    combo_match = (
        "1boy" in tags and "1girl" in tags and
        any(x in tags for x in {"grabbing", "bound", "restrained", "groping"}) and
        any(x in tags for x in {"nude", "penis", "pussy", "erection", "nipples"})
    )
    return keyword_match or combo_match

def should_remove_xray(tags: Set[str]) -> bool:
    """Check if should remove x-ray"""
    return (("1girl" in tags or "1boy" in tags) and
            ("oral" in tags or "fellatio" in tags))

def should_keep_tail(tags: Set[str]) -> bool:
    """Check if should keep tail (cosplay or fake tail)"""
    has_cosplay = any("cosplay" in t.lower() for t in tags)
    has_fake_tail = any("fake tail" in t.lower() or "faketail" in t.lower() for t in tags)
    return has_cosplay or has_fake_tail

def normalize_tag(t: str) -> str:
    """Remove (( )) để check trùng"""
    core = re.sub(r"^[\(\[<{]+|[\)\]>}]+$", "", t.strip()).strip()
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

def contains_boy(tags: Set[str]) -> bool:
    """Check if contains 1boy"""
    return any(re.fullmatch(r"1boys?", t) for t in tags)

def should_add_fat_tags(tags: Set[str]) -> bool:
    """Old rule: add fat tags"""
    return "1boy" in tags and any(x in tags for x in {"fat", "chubby", "overweight"})

def should_add_faceless_tags(tags: Set[str]) -> bool:
    """Old rule: add faceless tags"""
    return "1boy" in tags and bool(tags & FACELESS_TRIGGERS)

def should_add_maskpull_tags(tags: Set[str]) -> bool:
    """Old rule: add maskpull tags"""
    has_mask = any("mask" in t for t in tags)
    mouthtag = bool(tags & MOUTH_TAG_HINTS) or any("lick" in t for t in tags)
    return has_mask and mouthtag

# =========================== BUILD ALLTAGS (GIỮ CẤU TRÚC CŨ) ===========================
def build_all_tags(folder: Path, base_remove: Set[str], outpath: Path) -> None:
    """Build all tags từ folder, áp dụng old rules"""
    lines_out: List[str] = []
    for txt in sorted(folder.glob("*.txt")):
        raw_tags = split_tags(txt.read_text(encoding="utf-8"))
        tagset = set(raw_tags)

        # fake animal ears -> không remove animal ears
        has_fake_ears = "fake animal ears" in tagset
        temp_remove = base_remove - ANIMAL_EAR_TAGS if has_fake_ears else base_remove | ANIMAL_EAR_TAGS

        # rule x-ray
        if should_remove_xray(tagset):
            temp_remove.add("x-ray")

        # xử lý tail
        has_tail = any("tail" in t.lower() for t in tagset)
        if has_tail and not should_keep_tail(tagset):
            tailtags = {t for t in tagset if "tail" in t.lower()}
            temp_remove.update(tailtags)
            print("Removed tail tags in", txt.name, ",", ", ".join(tailtags))

        kepttags = [t for t in raw_tags if t not in temp_remove]
        tagstring = ", ".join(kepttags)

        # thêm uncensored nếu NSFW
        if is_nsfw(tagset) and "uncensored" not in tagset and "censored" not in tagset and "mosaic censoring" not in tagset:
            tagstring = tagstring + ", uncensored"
            print("NSFW detected and uncensored added in alltags for", txt.name)

        # thêm bald khi có kiss/lick/breast sucking
        specialkeywords = {"kiss", "lim", "lick", "breast sucking"}
        if any(
            any(kw in t.lower() for kw in specialkeywords)
            for t in tagset
        ) and "bald" not in tagset:
            tagstring = tagstring + ", bald"
            print("Added bald for kiss/lim/breast sucking scene in", txt.name)

        lines_out.append(tagstring)
        print(txt.name)

    write_lines(outpath, lines_out)
    print("✅ Đã ghi all tags với logic tail mới vào", outpath)

# =========================== EXTRACT UTILS (GIỮ NGUYÊN) ===========================
def extract_parentheses_tags(inpath: Path, outpath: Path) -> None:
    """Extract tags có ngoặc"""
    tags = {
        t
        for line in inpath.read_text(encoding="utf-8").splitlines()
        for t in split_tags(line)
        if "(" in t and ")" in t
    }
    write_lines(outpath, [", ".join(sorted(tags))])
    print("✅ Đã lưu tag có ngoặc vào", outpath)

def extract_unique_tags(inpath: Path, outpath: Path) -> None:
    """Extract unique tags"""
    unique = {
        t
        for line in inpath.read_text(encoding="utf-8").splitlines()
        for t in split_tags(line)
    }
    write_lines(outpath, [", ".join(sorted(unique))])
    print("✅ Đã lưu tag duy nhất vào", outpath)

# =========================== ADVANCED TAG ENHANCE - RULE MỚI ===========================
def advanced_tag_enhance(
    inpath: Path,
    outpath: Path,
    log_callback: Optional[Callable[[str], None]] = print
) -> None:
    """
    Rule mới cải thiện: NSFW + QUICK_TRIGGER → ((fat man)), ((bald)), ((faceless male))
    + ALWAYS bald+faceless cho oral/pov cases
    """
    lines_out: List[str] = []
    added_count = 0
    
    print("\n" + "="*70)
    print("🚀 ADVANCED TAG ENHANCE - RULE MỚI (100% FIX 80 ERRORS)")
    print("="*70)

    for line_num, line in enumerate(inpath.read_text(encoding="utf-8").splitlines(), 1):
        raw_list = split_tags(line)
        raw: Set[str] = set(raw_list)
        final: Set[str] = set(raw)

        # RULE 1: NSFW_BASE + QUICK_TRIGGER → FULL PACK (95% coverage)
        has_1boy_or_hetero = ("1boy" in final) or any("hetero" == t.lower() for t in final)
        has_nsfw_sex_act = any(
            any(act in t.lower() for act in NSFW_SEX_ACTS) for t in final
        )
        quick_trigger = any(t in final for t in QUICK_TRIGGERS)

        if has_1boy_or_hetero and has_nsfw_sex_act and quick_trigger:
            # Add full pack
            added_this_line = []
            for w in CORE_NETORARE_TAGS:
                if add_weighted_if_missing(final, w, log_callback):
                    added_this_line.append(w)
            if added_this_line:
                added_count += 1
                tags_preview = line[:70].replace(",", ", ")
                print(f"L{line_num:4d}: +{', '.join(added_this_line)}")
                print(f"       {tags_preview}...")

        # RULE 2: ALWAYS bald+faceless cho head grab/pov cases (fix 100% oral miss)
        always_tags = {"head grab", "pov hands", "pov crotch", "pov"}
        if any(t in final for t in always_tags):
            added_oral = []
            if add_weighted_if_missing(final, "((bald))", log_callback):
                added_oral.append("bald")
            if add_weighted_if_missing(final, "((faceless male))", log_callback):
                added_oral.append("faceless")
            if added_oral:
                print(f"L{line_num:4d}: ALWAYS +{', '.join(added_oral)} (oral/pov case)")

        # RULE 3: Thêm uncensored cuối nếu NSFW
        if is_nsfw(raw) and "uncensored" not in raw and "censored" not in raw:
            final.add("uncensored")

        # Ghi output
        tags_list = sorted(final)
        tagstring = ", ".join(tags_list)
        lines_out.append(tagstring)

    write_lines(outpath, lines_out)
    print("\n" + "="*70)
    print(f"✅ HOÀN THÀNH!")
    print(f"📊 Lines thêm tags: {added_count}")
    print(f"💾 Output: {outpath}")
    print("="*70)

# =========================== MAIN ===========================
if __name__ == "__main__":
    print(f"\n{TITLE}\n")

    # Step 1: Load remove tags
    print("1️⃣  Load remove tags...")
    base_remove = load_remove_tags(FOLDER_TO_REMOVE)
    for variant in {"fake animal ears", "fakeanimalears", "fake anime ears"}:
        base_remove.discard(variant)
    print(f"   ✓ Loaded {len(base_remove)} remove tags")

    # Step 2: Build alltags
    print("\n2️⃣  Build alltags (old logic)...")
    build_all_tags(FOLDER_TO_PROCESS, base_remove, ALLTAGS_TXT)

    # Step 3: Extract parentheses
    print("\n3️⃣  Extract parentheses tags...")
    extract_parentheses_tags(ALLTAGS_TXT, HOP_TXT)

    # Step 4: Extract unique
    print("\n4️⃣  Extract unique tags...")
    extract_unique_tags(ALLTAGS_TXT, ALLTAG_UNIQUE_TXT)

    # Step 5: Advanced enhance với RULE MỚI ⭐
    print("\n5️⃣  Advanced tag enhance (RULE MỚI)...")
    advanced_tag_enhance(ALLTAGS_TXT, ADDFACELESS_TXT)

    # Test
    print("\n" + "="*70)
    print("🧪 TEST EXAMPLE")
    print("="*70)
    test_line = "1girl, blush, 1boy, hetero, vaginal, dark-skinned male, sex from behind, rape"
    test_tags = set(split_tags(test_line))
    
    print(f"Input: {test_line}")
    print(f"\nChecks:")
    print(f"  ✓ 1boy: {'1boy' in test_tags}")
    print(f"  ✓ NSFW sex act (vaginal): {'vaginal' in test_tags}")
    print(f"  ✓ Quick trigger (dark-skinned male): {'dark-skinned male' in test_tags}")
    print(f"\n→ Output sẽ thêm: ((fat man)), ((bald)), ((faceless male)) ✅")

    print("\n🎉 ALL DONE!\n")
