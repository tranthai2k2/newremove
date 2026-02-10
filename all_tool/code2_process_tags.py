"""
Module xử lý tags - Khôi phục từ 5_removetag_add_faceless_oldman.py
Sửa 3 điểm:
1. Load wantremove tương đối từ __file__ (như code3)
2. Bỏ print() → dùng log_callback
3. Thêm faceless male khi kiss/lick
"""

import re
from pathlib import Path
from typing import List, Set

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

def log(msg, log_callback=None):
    """Log message dùng callback hoặc print"""
    if log_callback:
        log_callback(msg)
    else:
        print(msg, end='')

def load_remove_tags() -> Set[str]:
    """Đọc tất cả unwanted tags từ wantremove/*.txt (tương đối từ __file__)"""
    remove: Set[str] = set()
    
    # Đường dẫn tương đối tới wantremove (như code3)
    # Nếu code2 ở D:\no\all_tool\code2_process_tags.py
    # Thì wantremove ở D:\no\wantremove (lên 1 cấp)
    script_dir = Path(__file__).parent.parent
    wantremove_folder = script_dir / "wantremove"
    
    if not wantremove_folder.exists():
        print(f"⚠️ Không tìm thấy folder wantremove: {wantremove_folder}")
        return remove
    
    for p in wantremove_folder.glob("*.txt"):
        remove.update(
            t.strip()
            for t in p.read_text(encoding="utf-8").split(",")
            if t.strip()
        )
    return remove

def split_tags(line: str) -> List[str]:
    """Tách tags từ string, bỏ khoảng trắng thừa"""
    return [t.strip() for t in line.strip().split(",") if t.strip()]

def write_lines(path: Path, lines: List[str]) -> None:
    """Ghi danh sách dòng vào file"""
    path.write_text("\n".join(lines), encoding="utf-8")

def is_nsfw(tags: Set[str]) -> bool:
    """Kiểm tra xem tag set có chứa NSFW content không"""
    # Kiểm tra keyword cơ bản
    keyword_match = any(any(k in t.lower() for k in NSFW_KEYWORDS) for t in tags)
    
    # Kiểm tra kết hợp: 1boy/1girl + grabbing/bound + nude/penis/etc
    combo_match = (
        {"1boy", "1girl"} & tags and
        {"grabbing", "bound", "restrained", "groping", "hug from behind"} & tags and
        {"nude", "penis", "pussy", "erection", "nipples"} & tags
    )
    
    return keyword_match or combo_match

def should_remove_xray(tags: Set[str]) -> bool:
    """Xóa x-ray nếu có oral/fellatio"""
    return ("1girl" in tags or "1boy" in tags) and ("oral" in tags or "fellatio" in tags)

def should_keep_tail(tags: Set[str]) -> bool:
    """Giữ tail nếu là cosplay hoặc fake tail"""
    has_cosplay = any("cosplay" in t.lower() for t in tags)
    has_fake_tail = any("fake tail" in t.lower() or "fake_tail" in t.lower() for t in tags)
    return has_cosplay or has_fake_tail

# ──────────────────────────── BƯỚC 1 ────────────────────────────

def build_all_tags(folder: Path, base_remove: Set[str], out_path: Path, log_callback=None) -> None:
    """Build all_tags.txt từng file một dòng (như bản gốc)"""
    lines_out: List[str] = []
    
    for txt in sorted(folder.glob("*.txt")):
        raw_tags = split_tags(txt.read_text("utf-8"))
        tag_set = set(raw_tags)
        
        has_fake_ears = "fake animal ears" in tag_set
        
        temp_remove = (
            base_remove - ANIMAL_EAR_TAGS if has_fake_ears
            else base_remove | ANIMAL_EAR_TAGS
        )
        
        # Áp dụng rule: loại bỏ x-ray nếu oral
        if should_remove_xray(tag_set):
            temp_remove.add("x-ray")
        
        # Logic: xử lý tail - xóa nếu không cosplay
        has_tail = any("tail" in t.lower() for t in tag_set)
        if has_tail and not should_keep_tail(tag_set):
            tail_tags = {t for t in tag_set if "tail" in t.lower()}
            temp_remove.update(tail_tags)
            log(f"⚠️ Removed tail tags in {txt.name}: {', '.join(tail_tags)}\n", log_callback)
        
        # ✅ FIX BUG 1: Lọc bỏ unwanted tags đúng
        kept_tags = [t for t in raw_tags if t not in temp_remove]
        tag_string = ", ".join(kept_tags)
        
        # Thêm uncensored vào cuối nếu là NSFW
        if is_nsfw(tag_set) and "uncensored" not in tag_set and "censored" not in tag_set and "mosaic censoring" not in tag_set:
            tag_string += ", uncensored"
            log(f"NSFW detected and uncensored added in all_tags for: {txt.name}\n", log_callback)
        
        # ✅ FIX BUG 2: Nếu có kiss, liếm/lick, hoặc breast sucking → thêm bald + faceless male
        special_keywords = {"kiss", "liếm", "lick", "breast sucking"}
        if any(any(kw in t.lower() for kw in special_keywords) for t in tag_set):
            added = []
            if "bald" not in tag_set:
                tag_string += ", bald"
                added.append("bald")
            if "faceless male" not in tag_set:
                tag_string += ", faceless male"
                added.append("faceless male")
            if added:
                log(f"💋 Added {', '.join(added)}: {txt.name}\n", log_callback)
        
        lines_out.append(tag_string)
        log(f"✓ {txt.name}\n", log_callback)
    
    write_lines(out_path, lines_out)
    log(f"→ Đã tạo ALL_TAGS: {out_path}\n\n", log_callback)

# ──────────────────────────── BƯỚC 2 ────────────────────────────

def extract_parentheses_tags(in_path: Path, out_path: Path, log_callback=None) -> None:
    """Trích xuất các tags có ngoặc đơn (())"""
    tags = {
        t
        for line in in_path.read_text("utf-8").splitlines()
        for t in split_tags(line)
        if "(" in t and ")" in t
    }
    
    write_lines(out_path, [", ".join(sorted(tags))])
    log(f"→ Đã lưu tag có ngoặc: {out_path}\n\n", log_callback)

# ──────────────────────────── BƯỚC 3 ────────────────────────────

def extract_unique_tags(in_path: Path, out_path: Path, log_callback=None) -> None:
    """Trích xuất tất cả unique tags (sorted) từ all_tags.txt"""
    unique = {
        t
        for line in in_path.read_text("utf-8").splitlines()
        for t in split_tags(line)
    }
    
    write_lines(out_path, [", ".join(sorted(unique))])
    log(f"→ Đã lưu tag duy nhất: {out_path}\n\n", log_callback)

# ──────────────────────────── BƯỚC 4 ────────────────────────────

def contains_boy(tags: Set[str]) -> bool:
    """Kiểm tra có boy tag không"""
    return any(re.fullmatch(r"\d*boy[s]?", t) for t in tags)

def should_add_fat(tags: Set[str]) -> bool:
    """Cần thêm fat man tag không"""
    return {"1boy"} & tags and {"fat", "chubby", "overweight", "large", "big"} & tags

def should_add_faceless(tags: Set[str]) -> bool:
    """Cần thêm faceless male tag không"""
    return {"1boy"} & tags and tags & FACELESS_TRIGGERS

def should_add_mask_pull(tags: Set[str]) -> bool:
    """Cần thêm mask_pull tag không"""
    has_mask = any("mask" in t for t in tags)
    mouth_tag = tags & MOUTH_TAG_HINTS or any("lick" in t for t in tags)
    return has_mask and mouth_tag

def advanced_tag_enhance(in_path: Path, out_path: Path, log_callback=None) -> None:
    """Tăng cường tags từ all_tags.txt → addfaceless.txt"""
    lines_out: List[str] = []
    
    for line in in_path.read_text("utf-8").splitlines():
        raw_list = split_tags(line)
        raw: Set[str] = set(raw_list)
        final = set(raw)
        
        # Áp dụng rule: loại bỏ x-ray nếu oral
        if should_remove_xray(raw):
            final.discard("x-ray")
        
        # Xử lý tail
        has_tail = any("tail" in t.lower() for t in raw)
        if has_tail and not should_keep_tail(raw):
            tail_tags = {t for t in raw if "tail" in t.lower()}
            final -= tail_tags
        
        # Xử lý các tag với nhấn mạnh (( ))
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
        
        # Xử lý uncensored: gắn vào CUỐI
        tags_list = sorted(final)
        tag_string = ", ".join(tags_list)
        
        if is_nsfw(raw) and "uncensored" not in raw and "censored" not in raw and "mosaic censoring" not in raw:
            tag_string += ", uncensored"
        
        lines_out.append(tag_string)
    
    write_lines(out_path, lines_out)
    log(f"✅ Đã tăng cường tag: {out_path}\n\n", log_callback)

# ───────────────────────────── MAIN ─────────────────────────────

def process_tags(folder_path, log_callback=None):
    """
    Xử lý tags trong folder
    
    Args:
        folder_path (str): Đường dẫn folder chứa file tags (ví dụ: D:\no)
        log_callback (function): Hàm callback để ghi log
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        log(f"❌ Folder không tồn tại: {folder_path}\n", log_callback)
        return
    
    # Tạo output folder
    output_folder = folder / "out_tags"
    output_folder.mkdir(exist_ok=True)
    
    # Output files
    ALL_TAGS_TXT = output_folder / "all_tags.txt"
    HOP_TXT = output_folder / "hop_txt.txt"
    ALL_TAG_UNIQUE_TXT = output_folder / "all_tag.txt"
    ADDFACELESS_TXT = output_folder / "addfaceless.txt"
    
    log(f"📁 Xử lý folder: {folder}\n", log_callback)
    log(f"📂 Output folder: {output_folder}\n\n", log_callback)
    
    # Load unwanted tags from wantremove/ (tương đối từ __file__)
    log("🗑️ Đang load unwanted tags từ wantremove/...\n", log_callback)
    base_remove = load_remove_tags()
    
    # Bảo đảm "fake animal ears" không bị xóa
    for variant in ("fake animal ears", "fake_animal_ears", "fake anime ears"):
        base_remove.discard(variant)
    
    log(f"✓ Loaded {len(base_remove)} unwanted tags\n\n", log_callback)
    
    # ════════════════════════════════════════════
    # BƯỚC 1: BUILD ALL_TAGS.TXT
    # ════════════════════════════════════════════
    log("=" * 50 + "\n", log_callback)
    log("BƯỚC 1: BUILD ALL_TAGS.TXT\n", log_callback)
    log("=" * 50 + "\n", log_callback)
    build_all_tags(folder, base_remove, ALL_TAGS_TXT, log_callback)
    
    # ════════════════════════════════════════════
    # BƯỚC 2: EXTRACT PARENTHESES TAGS
    # ════════════════════════════════════════════
    log("=" * 50 + "\n", log_callback)
    log("BƯỚC 2: EXTRACT PARENTHESES TAGS\n", log_callback)
    log("=" * 50 + "\n", log_callback)
    extract_parentheses_tags(ALL_TAGS_TXT, HOP_TXT, log_callback)
    
    # ════════════════════════════════════════════
    # BƯỚC 3: EXTRACT UNIQUE TAGS
    # ════════════════════════════════════════════
    log("=" * 50 + "\n", log_callback)
    log("BƯỚC 3: EXTRACT UNIQUE TAGS\n", log_callback)
    log("=" * 50 + "\n", log_callback)
    extract_unique_tags(ALL_TAGS_TXT, ALL_TAG_UNIQUE_TXT, log_callback)
    
    # ════════════════════════════════════════════
    # BƯỚC 4: ADVANCED TAG ENHANCE
    # ════════════════════════════════════════════
    log("=" * 50 + "\n", log_callback)
    log("BƯỚC 4: ADVANCED TAG ENHANCE\n", log_callback)
    log("=" * 50 + "\n", log_callback)
    advanced_tag_enhance(ALL_TAGS_TXT, ADDFACELESS_TXT, log_callback)
    
    log("=" * 50 + "\n", log_callback)
    log("✅ HOÀN THÀNH XỬ LÝ TAGS!\n", log_callback)
    log("=" * 50 + "\n", log_callback)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        process_tags(sys.argv[1])
    else:
        print("Usage: python code2_process_tags.py <folder_path>")
