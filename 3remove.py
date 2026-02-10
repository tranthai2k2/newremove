# FULL TAG-TOOL v2.8 - Nhận folder từ command line argument
# ───────────────────────────── IMPORTS ──────────────────────────
import sys
import re
from pathlib import Path
from typing import List, Set

# ──────────────────── CẤU HÌNH THƯ MỤC & FILE ──────────────────

# ✅ NHẬN FOLDER TỪ COMMAND LINE ARGUMENT
if len(sys.argv) > 1:
    FOLDER_TO_PROCESS = Path(sys.argv[1])
    print(f"\n{'='*60}")
    print(f"📁 Processing folder: {FOLDER_TO_PROCESS}")
    print(f"📁 Output sẽ lưu tại: {FOLDER_TO_PROCESS / 'out_tags'}")
    print(f"{'='*60}\n")
else:
    print("❌ Lỗi: Chưa truyền đường dẫn folder!")
    print("📖 Cách dùng: python 5_removetag_add_faceless_oldman.py /path/to/folder")
    sys.exit(1)

# Kiểm tra folder có tồn tại không
if not FOLDER_TO_PROCESS.exists():
    print(f"❌ Lỗi: Folder không tồn tại: {FOLDER_TO_PROCESS}")
    sys.exit(1)

# Các path khác relative với FOLDER_TO_PROCESS
FOLDER_TO_REMOVE = FOLDER_TO_PROCESS / "wantremove"
OUTPUT_FOLDER = FOLDER_TO_PROCESS / "out_tags"
OUTPUT_FOLDER.mkdir(exist_ok=True)

ALL_TAGS_TXT = OUTPUT_FOLDER / "all_tags.txt"
HOP_TXT = OUTPUT_FOLDER / "hop_txt.txt"
ALL_TAG_UNIQUE_TXT = OUTPUT_FOLDER / "all_tag.txt"
ADDFACELESS_TXT = OUTPUT_FOLDER / "addfaceless.txt"

# ──────────────────────────── HẰNG SỐ ───────────────────────────
ANIMAL_EAR_TAGS: Set[str] = {
    "animal ears", "bat ears", "bear ears", "rabbit ears", "cat ears",
    "cow ears", "deer ears", "dog ears", "ferret ears", "fox ears",
    "goat ears", "horse ears", "lion ears", "monkey ears", "mouse ears",
    "panda ears", "pikachu ears", "pig ears", "raccoon ears", "sheep ears",
    "squirrel ears", "tiger ears", "wolf ears", "floppy ears",
}

TAG_DARKSKIN = {"dark-skinned male", "interracial"}
TAG_FAT = {"fat man"}
TAG_FACELESS = {"faceless male", "bald"}

FACELESS_TRIGGERS: Set[str] = {
    "faceless", "pov hands", "pov", "grabbing", "head grab",
    "arm grab", "irrumatio", "pov crotch", "bound arms",
    "from behind", "doggystyle", "prone bone", "reverse cowgirl position",
}

NSFW_KEYWORDS: Set[str] = {
    "cum", "sex", "vaginal", "anal", "nude", "pussy", "penetration",
    "breast", "nipples", "fingering", "fuck", "sperm", "intercourse",
    "cervix", "creampie", "ejaculation", "rape", "clit", "clitoris",
    "penis", "pussy juice", "orgasm",
    "doggystyle", "cowgirl", "reverse cowgirl", "missionary", "spooning",
    "standing sex", "prone bone", "pile driver", "mating press", "blowjob",
    "handjob", "titjob", "paizuri", "fellatio", "cunnilingus",
    "erection", "testicles", "labia", "vulva", "anus", "masturbation",
    "double penetration", "threesome", "gangbang", "bdsm", "bondage",
    "grabbing", "groping", "bound", "restrained", "shibari", "rope",
    "deepthroat", "irrumatio", "cumdrip", "cum overflow", "internal cumshot",
    "pubic hair", "spread legs", "spread pussy", "spread anus", "x-ray",
    "cross-section", "uterus", "cervix", "deep penetration", "imminent penetration",
    "after sex", "after anal", "after vaginal", "ejaculation", "saliva",
    "tongue out", "french kiss", "licking", "hetero", "ass grab", "breast sucking"
}

MOUTH_TAG_HINTS: Set[str] = {
    "open mouth", "tongue out", "french kiss", "licking", "lick", "kiss",
}

# ────────────────────── HÀM TIỆN ÍCH CHUNG ──────────────────────
def load_remove_tags(folder: Path) -> Set[str]:
    """Load các tag cần remove từ folder wantremove"""
    remove: Set[str] = set()
    if not folder.exists():
        print(f"⚠️  Cảnh báo: Folder wantremove không tồn tại: {folder}")
        return remove
    
    for p in folder.glob("*.txt"):
        remove.update(
            t.strip()
            for t in p.read_text(encoding="utf-8").split(",")
            if t.strip()
        )
    print(f"📝 Loaded {len(remove)} tags từ wantremove")
    return remove

def split_tags(line: str) -> List[str]:
    return [t.strip() for t in line.strip().split(",") if t.strip()]

def write_lines(path: Path, lines: List[str]) -> None:
    path.write_text("\n".join(lines), encoding="utf-8")

def is_nsfw(tags: Set[str]) -> bool:
    """Hàm kiểm tra NSFW (dùng chung cho cả hai hàm)"""
    keyword_match = any(any(k in t.lower() for k in NSFW_KEYWORDS) for t in tags)
    
    combo_match = (
        ({"1boy", "1girl"} & tags) and
        ({"grabbing", "bound", "restrained", "groping", "hug from behind"} & tags) and
        ({"nude", "penis", "pussy", "erection", "nipples"} & tags)
    )
    
    return keyword_match or combo_match

def should_remove_xray(tags: Set[str]) -> bool:
    """Hàm kiểm tra điều kiện để loại bỏ x-ray"""
    return ("1girl" in tags or "1boy" in tags) and ("oral" in tags or "fellatio" in tags)

# ──────────────────────────── BƯỚC 1 ────────────────────────────
def build_all_tags(folder: Path, base_remove: Set[str], out_path: Path) -> None:
    """Build file all_tags.txt từ các file txt trong folder"""
    lines_out: List[str] = []
    txt_files = list(folder.glob("*.txt"))
    
    if not txt_files:
        print(f"⚠️  Không tìm thấy file .txt nào trong: {folder}")
        return
    
    print(f"\n🔄 BƯỚC 1: Build ALL_TAGS từ {len(txt_files)} files...")
    
    for txt in sorted(txt_files):
        raw_tags = split_tags(txt.read_text("utf-8"))
        tag_set = set(raw_tags)
        has_fake_ears = "fake animal ears" in tag_set
        
        temp_remove = (
            base_remove - ANIMAL_EAR_TAGS if has_fake_ears
            else base_remove | ANIMAL_EAR_TAGS
        )
        
        # Áp dụng rule: loại bỏ x-ray nếu thỏa điều kiện
        if should_remove_xray(tag_set):
            temp_remove.add("x-ray")
        
        kept_tags = [t for t in raw_tags if t not in temp_remove]
        tag_string = ", ".join(kept_tags)
        
        # Thêm uncensored vào cuối nếu là NSFW
        if is_nsfw(tag_set) and "uncensored" not in tag_set and "censored" not in tag_set and "mosaic censoring" not in tag_set:
            tag_string += ", uncensored"
            print(f"  ✓ {txt.name} - Added uncensored")
        
        # Logic: Nếu có kiss/lick/breast sucking, thêm bald
        special_keywords = {"kiss", "liếm", "lick", "breast sucking"}
        if any(any(kw in t.lower() for kw in special_keywords) for t in tag_set) and "bald" not in tag_set:
            tag_string += ", bald"
            print(f"  ✓ {txt.name} - Added bald")
        
        lines_out.append(tag_string)
    
    write_lines(out_path, lines_out)
    print(f"✅ Đã tạo {out_path.name} với {len(lines_out)} dòng\n")

# ──────────────────────────── BƯỚC 2 ────────────────────────────
def extract_parentheses_tags(in_path: Path, out_path: Path) -> None:
    """Extract các tag có dấu ngoặc ()"""
    if not in_path.exists():
        print(f"⚠️  File không tồn tại: {in_path}")
        return
    
    print(f"🔄 BƯỚC 2: Extract tag có ngoặc ()...")
    tags = {
        t
        for line in in_path.read_text("utf-8").splitlines()
        for t in split_tags(line)
        if "(" in t and ")" in t
    }
    
    write_lines(out_path, [", ".join(sorted(tags))])
    print(f"✅ Đã tạo {out_path.name} với {len(tags)} tags\n")

# ──────────────────────────── BƯỚC 3 ────────────────────────────
def extract_unique_tags(in_path: Path, out_path: Path) -> None:
    """Extract tất cả các tag unique"""
    if not in_path.exists():
        print(f"⚠️  File không tồn tại: {in_path}")
        return
    
    print(f"🔄 BƯỚC 3: Extract unique tags...")
    unique = {
        t
        for line in in_path.read_text("utf-8").splitlines()
        for t in split_tags(line)
    }
    
    write_lines(out_path, [", ".join(sorted(unique))])
    print(f"✅ Đã tạo {out_path.name} với {len(unique)} tags unique\n")

# ──────────────────────────── BƯỚC 4 ────────────────────────────
def contains_boy(tags: Set[str]) -> bool:
    return any(re.fullmatch(r"\d*boy[s]?", t) for t in tags)

def should_add_fat(tags: Set[str]) -> bool:
    return {"1boy"} & tags and {"fat", "chubby", "overweight", "large", "big"} & tags

def should_add_faceless(tags: Set[str]) -> bool:
    return {"1boy"} & tags and tags & FACELESS_TRIGGERS

def should_add_mask_pull(tags: Set[str]) -> bool:
    has_mask = any("mask" in t for t in tags)
    mouth_tag = tags & MOUTH_TAG_HINTS or any("lick" in t for t in tags)
    return has_mask and mouth_tag

def advanced_tag_enhance(in_path: Path, out_path: Path) -> None:
    """Tăng cường tag với nhấn mạnh (( ))"""
    if not in_path.exists():
        print(f"⚠️  File không tồn tại: {in_path}")
        return
    
    print(f"🔄 BƯỚC 4: Advanced tag enhancement...")
    lines_out: List[str] = []
    
    for line in in_path.read_text("utf-8").splitlines():
        raw_list = split_tags(line)
        raw: Set[str] = set(raw_list)
        final = set(raw)
        
        # Loại bỏ x-ray nếu thỏa điều kiện
        if should_remove_xray(raw):
            final.discard("x-ray")
        
        # Xử lý các tag khác với nhấn mạnh (( ))
        if contains_boy(raw) and not any(t in raw or f"(({t}))" in raw for t in TAG_DARKSKIN):
            for t in TAG_DARKSKIN:
                final.add(f"(({t}))")
        
        if should_add_fat(raw) and not any(t in raw or f"(({t}))" in raw for t in TAG_FAT):
            for t in TAG_FAT:
                final.add(f"(({t}))")
        
        if should_add_faceless(raw) and not any(t in raw or f"(({t}))" in raw for t in TAG_FACELESS):
            for t in TAG_FACELESS:
                final.add(f"(({t}))")
        
        if should_add_mask_pull(raw) and "mask_pull" not in raw and "((mask_pull))" not in raw:
            final.add("((mask_pull))")
        
        # Xử lý uncensored: gắn vào cuối
        tags_list = sorted(final)
        tag_string = ", ".join(tags_list)
        
        if is_nsfw(raw) and "uncensored" not in raw and "censored" not in raw and "mosaic censoring" not in raw:
            tag_string += ", uncensored"
        
        lines_out.append(tag_string)
    
    write_lines(out_path, lines_out)
    print(f"✅ Đã tạo {out_path.name} với enhancement\n")

# ───────────────────────────── MAIN ─────────────────────────────
if __name__ == "__main__":
    try:
        print(f"\n🚀 Bắt đầu xử lý folder: {FOLDER_TO_PROCESS}")
        
        # Load remove tags
        base_remove = load_remove_tags(FOLDER_TO_REMOVE)
        
        # Bảo đảm "fake animal ears" không bao giờ bị xóa
        for variant in ("fake animal ears", "fake_animal_ears", "fake anime ears"):
            base_remove.discard(variant)
        
        # Chạy các bước
        build_all_tags(FOLDER_TO_PROCESS, base_remove, ALL_TAGS_TXT)
        extract_parentheses_tags(ALL_TAGS_TXT, HOP_TXT)
        extract_unique_tags(ALL_TAGS_TXT, ALL_TAG_UNIQUE_TXT)
        advanced_tag_enhance(ALL_TAGS_TXT, ADDFACELESS_TXT)
        
        print(f"\n{'='*60}")
        print(f"✅ HOÀN THÀNH! Tất cả file đã được tạo trong:")
        print(f"📂 {OUTPUT_FOLDER}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\n❌ LỖI: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
