"""
lora_processor.py
─────────────────────────────────────────────────────────────────
Processing module for LoRA Browser.
Adapted from 1test-2.py logic — standalone module.
DO NOT import 1test-2.py directly here.

To add new stateless processing logic:
  1. Write a new tier_N(tags: Set[str]) -> List[str] function
  2. Register it in _STATELESS_TIERS list at the bottom
"""

import re
import sys
import subprocess
from pathlib import Path
from typing import Set, List, Tuple, Optional


# ══════════════════════════════════════════════════════════════
# BREAST SIZE REPLACEMENT
# ══════════════════════════════════════════════════════════════

BREAST_SIZE_TAGS: Set[str] = {
    'flat chest', 'small breasts', 'medium breasts',
    'large breasts', 'huge breasts', 'gigantic breasts',
    'big breasts', 'enormous breasts', 'giant breasts',
}

# Tag chung "breasts" (không có size) → thay bằng size được chọn
_BREAST_GENERIC: Set[str] = {'breasts'}

# Tags chứng tỏ ngực hiện diện trong prompt → cần thêm size nếu chưa có
_BREAST_TRIGGER: Set[str] = {
    'nipples', 'nipple', 'areolae',
    'breasts out', 'breasts_out',
    'between breasts',
}


def replace_breast_size(text: str, target: str) -> str:
    """
    Mỗi dòng:
    - Có specific size tag  → thay bằng target (bỏ trùng)
    - Có generic 'breasts'  → thay bằng target
    - Có trigger tag (nipples, breasts out...) nhưng không có size → append target
    - Không có gì liên quan → giữ nguyên
    """
    result = []
    for line in text.split('\n'):
        if not line.strip():
            result.append(line)
            continue
        out      = []
        inserted = False

        for tag in line.split(','):
            t  = tag.strip()
            tl = t.lower()
            if tl in BREAST_SIZE_TAGS or tl in _BREAST_GENERIC:
                # Thay bằng size được chọn (chỉ 1 lần, bỏ trùng)
                if not inserted:
                    out.append(target)
                    inserted = True
            else:
                if t:
                    out.append(t)

        # Chưa có size → luôn thêm size vào cuối
        if not inserted:
            out.append(target)

        result.append(', '.join(out))
    return '\n'.join(result)


# ══════════════════════════════════════════════════════════════
# TAG EXTRACTION HELPER
# ══════════════════════════════════════════════════════════════

def extract_tags(line: str) -> Set[str]:
    """Return tag set without destroying the original grouping structure."""
    clean = line.replace('(', '').replace(')', '')
    return {t.strip() for t in clean.split(',') if t.strip()}


# ══════════════════════════════════════════════════════════════
# TIER 0 — EXPOSURE PERSISTENCE  (stateful, cross-line)
# ══════════════════════════════════════════════════════════════

# Tags chứng tỏ ngực đang lộ (gồm cả pull/lift quần áo)
_BREASTS_EXPOSED: Set[str] = {
    'breasts out', 'breasts_out', 'nipples', 'nipple', 'areolae',
    # clothes pull / lift → ngực lộ
    'bra pull', 'bra_pull', 'bra lift', 'bra_lift',
    'shirt lift', 'shirt_lift', 'clothes lift', 'clothes_lift',
    'clothes pull', 'clothes_pull', 'top pull', 'top_pull', 'top lift', 'top_lift',
    'bikini pull', 'bikini_pull', 'bikini top pull', 'bikini top lift',
    'dress pull', 'dress_pull',
}


def tier_0(cur: Set[str], prev: dict) -> Tuple[List[str], dict]:
    """
    Duy trì trạng thái lộ thân xuyên suốt các dòng.

    Breasts persistence: chỉ carry-forward khi dòng HIỆN TẠI vẫn có
    sexual context — tránh thêm nipples vào scene teaser/non-sexual
    dù dòng trước đã lộ ngực.

    'restrained'/'bound' KHÔNG thuộc SEXUAL vì chỉ là trạng thái bị trói,
    không có nghĩa là đang làm tình.
    """
    PUSSY   = {'pussy', 'spread pussy', 'spread_pussy', 'pussy juice', 'pussy_juice'}
    ANUS    = {'anus', 'spread anus', 'spread_anus', 'puckered anus', 'puckered_anus'}
    RESET   = {'fully clothed', 'clothed'}
    COVER   = {'covered', 'dressed', 'bra', 'panties on'}
    SEXUAL  = {
        'hetero', 'sex', 'vaginal', 'missionary', 'doggystyle',
        'imminent penetration', 'imminent vaginal', 'penis',
        'rape', 'bdsm', 'spread legs',
        # 'restrained', 'bound' đã bỏ — chỉ là trạng thái, không phải sex
    }

    if cur & RESET or cur & COVER:
        return [], {'breasts': False, 'pussy': False, 'anus': False}

    cur_breasts = bool(cur & _BREASTS_EXPOSED)
    cur_pussy   = bool(cur & PUSSY)
    cur_anus    = bool(cur & ANUS)
    has_sexual  = bool(cur & SEXUAL)

    add: List[str] = []

    # Breasts persist CHỈ KHI dòng hiện tại còn trong bối cảnh sexual
    if prev.get('breasts') and not cur_breasts and has_sexual:
        add += ['breasts out', 'nipples']
        cur_breasts = True

    # Pussy / anus: tương tự — chỉ persist khi có sexual context
    if has_sexual:
        if prev.get('pussy') and not cur_pussy:
            add.append('pussy')
            cur_pussy = True
        if prev.get('anus') and 'anal' in cur and not cur_anus:
            add.append('anus')
            cur_anus = True

    # State breasts chỉ tiếp tục nếu dòng này còn sexual hoặc đang lộ
    return add, {
        'breasts': cur_breasts or (prev.get('breasts', False) and has_sexual),
        'pussy':   cur_pussy   or (prev.get('pussy',   False) and has_sexual),
        'anus':    cur_anus,
    }


# ══════════════════════════════════════════════════════════════
# TIER 1 — CLOTHING TRANSITION  (stateful, cross-line)
# ══════════════════════════════════════════════════════════════

def tier_1(cur: Set[str], prev_pull: bool) -> Tuple[List[str], bool]:
    """panty pull → panties on current line; unworn_panties on next line."""
    PULL   = {'panty pull', 'panty_pull', 'panties pull', 'panties_pull'}
    PANTY  = {'panties', 'panty', 'underwear'}
    UNWORN = {
        'unworn_panties', 'unworn panties', 'panties aside', 'panties_aside',
        'panties around one leg', 'panties_around_one_leg',
    }
    has_pull = bool(cur & PULL)
    add: List[str] = []
    if has_pull and not (cur & PANTY):
        add.append('panties')
    if prev_pull and not (cur & UNWORN):
        add.append('unworn_panties')
    return add, has_pull


# ══════════════════════════════════════════════════════════════
# TIER 2 — NIPPLES ↔ BREASTS OUT CO-OCCURRENCE  (stateless)
# ══════════════════════════════════════════════════════════════

def tier_2(tags: Set[str]) -> List[str]:
    """
    Đảm bảo nhất quán cùng dòng:
    - nipples / areolae   → bắt buộc có 'breasts out'
    - breasts out         → bắt buộc có 'nipples'
    - bra pull/lift, shirt lift, clothes pull/lift ... → cả 'breasts out' + 'nipples'
    - leotard / one-piece swimsuit (trừ strapless) → 'nipples' + 'between breasts' + 'breasts out'
    """
    has_nipples       = bool({'nipples', 'nipple', 'areolae'} & tags)
    has_breasts_out   = bool({'breasts out', 'breasts_out'}   & tags)
    has_pull_lift     = bool(_BREASTS_EXPOSED & tags)
    has_btw_breasts   = 'between breasts' in tags

    add: List[str] = []

    # leotard / one-piece swimsuit → nipples + between breasts + breasts out
    # ngoại lệ: strapless leotard hoặc có tag 'strapless' thì bỏ qua
    LEOTARD_TAGS  = {'leotard', 'one-piece swimsuit', 'one-piece_swimsuit'}
    STRAPLESS     = {'strapless', 'strapless leotard', 'strapless_leotard'}
    if (tags & LEOTARD_TAGS) and not (tags & STRAPLESS):
        if not has_nipples:
            add.append('nipples')
            has_nipples = True
        if not has_breasts_out:
            add.append('breasts out')
            has_breasts_out = True
        if not has_btw_breasts:
            add.append('between breasts')

    # nipples ↔ breasts out co-occurrence
    if has_pull_lift or has_nipples or has_breasts_out:
        if not has_nipples:
            add.append('nipples')
        if not has_breasts_out:
            add.append('breasts out')

    return add


# ══════════════════════════════════════════════════════════════
# TIER 4 — CLOTHING PULL DETECTION  (stateless)
# ══════════════════════════════════════════════════════════════

def tier_4(tags: Set[str]) -> List[str]:
    """Detect clothing pull situations and add appropriate tags."""
    add: List[str] = []
    if 'breasts' in tags and 'dress' in tags:
        if 'dress lift' not in tags:    add.append('dress lift')
        if 'breasts out' not in tags:   add.append('breasts out')
    if 'pussy' in tags and 'pelvic_curtain' in tags:
        if 'pelvic curtain lift' not in tags:
            add.append('pelvic curtain lift')
    if 'pussy' in tags and 'dress' in tags and 'pelvic_curtain' not in tags:
        if 'dress lift' not in tags:
            add.append('dress lift')
    return add


# ══════════════════════════════════════════════════════════════
# STATELESS TIER REGISTRY
# Add new stateless tiers here as ("TIER N", function) tuples.
# ══════════════════════════════════════════════════════════════

_STATELESS_TIERS = [
    ("TIER 2", tier_2),
    ("TIER 4", tier_4),
    # ("TIER 5", tier_5),
]


def process_stateless(tags: Set[str]) -> List[str]:
    """Run all registered stateless tiers, return combined new tags."""
    out: List[str] = []
    for _, fn in _STATELESS_TIERS:
        out.extend(fn(tags))
    return out


# ══════════════════════════════════════════════════════════════
# TIER SKIRT — SKIRT LIFT  (stateful, cross-line)
# ══════════════════════════════════════════════════════════════

def tier_skirt(btags: Set[str], cp_tags: Set[str], prev_sl: bool) -> Tuple[List[str], bool]:
    """
    Thêm 'skirt lift' khi:
      - Base có skirt tag
      - Base KHÔNG có pull/lift tag (tránh double)
      - User prompt có 'panty pull' / 'panties pull'

    Carry-forward: nếu dòng trước đã trigger skirt lift
      + dòng hiện tại vẫn có skirt + NSFW context → tiếp tục thêm skirt lift
    """
    has_skirt       = any('skirt' in t for t in btags)
    no_block        = not bool(btags & _SKIRT_BLOCK)
    pull_in_prompt  = bool(cp_tags & _PROMPT_PULL)
    has_nsfw        = bool(btags & _NSFW_SKIRT_CARRY)
    already_has     = 'skirt lift' in btags or 'skirt_lift' in btags

    trigger = (
        (has_skirt and no_block and pull_in_prompt) or
        (prev_sl and has_skirt and has_nsfw)
    )

    add = ['skirt lift'] if (trigger and not already_has) else []
    return add, trigger


# ══════════════════════════════════════════════════════════════
# EYE / FACE / AWAY HELPERS  (internal)
# ══════════════════════════════════════════════════════════════

_EYE_TAGS: Set[str] = {
    'red_eyes', 'blue_eyes', 'green_eyes', 'brown_eyes', 'yellow_eyes', 'purple_eyes',
    'heterochromia', 'multicolored_eyes', 'golden_eyes', 'pink_eyes', 'grey_eyes',
    'pupils', 'slit pupils', 'crossed_eyes', 'heart-shaped_pupils', 'glowing_eyes',
    'eyelashes', 'colored_eyelashes', 'long_eyelashes', 'thick_eyelashes',
    'eyeshadow', 'mascara', 'eyeliner', 'makeup', 'cosmetics',
}
_FACING_AWAY: Set[str] = {
    'facing away', 'facing_away', 'from behind', 'back turned', 'back view',
}
_HEAD_BACK: Set[str] = {'head back', 'head_back'}

# ── Skirt lift persistence ────────────────────────────────────
# Nếu base đã có các tag pull/lift này → không thêm skirt lift (đã xử lý)
_SKIRT_BLOCK: Set[str] = {
    'panty pull', 'panty_pull', 'panties pull', 'panties_pull',
    "pulling another's clothes", "lifting another's clothes",
    "lifting_another's_clothes",
    'skirt lift', 'skirt_lift', 'skirt pull', 'skirt_pull',
}
# Nếu user prompt có những tag này → trigger skirt lift
_PROMPT_PULL: Set[str] = {
    'panty pull', 'panty_pull', 'panties pull', 'panties_pull',
}
# NSFW context để carry-forward skirt lift sang dòng tiếp theo
_NSFW_SKIRT_CARRY: Set[str] = {
    'hetero', 'sex', 'vaginal', 'missionary', 'doggystyle', 'rape',
    'penis', 'nipples', 'breasts out', 'pussy', 'spread legs',
    'bdsm', 'fingering', 'oral', 'fellatio', 'breast sucking',
    'licking nipple', 'nipple stimulation', 'spread pussy',
}
# ── Leotard aside ────────────────────────────────────────────
# Pull phần dưới khi đang mặc leotard → (((leotard aside, pussy)))
_LEOTARD_LOWER_PULL: Set[str] = {
    'shorts pull', 'shorts_pull',
    'pants pull',  'pants_pull',
    'panty pull',  'panty_pull',
    'panties pull','panties_pull',
    'leotard pull','leotard_pull',
    'leotard aside','leotard_aside',
}

_COVERED_EYE: Set[str] = {
    'covered_eyes', 'blindfold', 'eyepatch', 'hair_over_eyes',
    'eyes_visible_through_hair', 'black_blindfold',
}


def _load_file_tags(fp: Path) -> Set[str]:
    if not fp.exists():
        return set()
    tags: Set[str] = set()
    for raw in fp.read_text(encoding='utf-8').split(','):
        raw = raw.strip()
        if not raw:
            continue
        m = re.match(r'^(.+?)\s*\((.+?)\)\s*$', raw)
        if m:
            tags.add(m.group(1).strip().lower())
            tags.add(m.group(2).strip().lower())
        else:
            tags.add(raw.lower())
    return tags


def _facing_away_remove_tags(script_dir: Path) -> Set[str]:
    head_dir = script_dir / "wantremove-head"
    tags: Set[str] = set()
    for fname in ("eyes.txt", "face.txt", "bangs.txt", "head.txt"):
        tags |= _load_file_tags(head_dir / fname)
    return tags


def _clean_prompt(prompt: str, base_tags: Set[str]) -> Optional[str]:
    if 'black_blindfold' in base_tags:
        return None
    # Tách <lora:...> ra trước (tên lora có thể chứa dấu phẩy)
    lora_parts = re.findall(r'<[^>]+>', prompt)
    text = re.sub(r'<[^>]+>', '', prompt).strip().lstrip(',').strip()
    # Dùng list để giữ thứ tự
    pts = [t.strip() for t in text.split(',') if t.strip()]
    if base_tags & _COVERED_EYE:
        pts = [t for t in pts if t.lower() not in _EYE_TAGS]
    if base_tags & _EYE_TAGS:
        pts = [t for t in pts if t.lower() not in _COVERED_EYE]
    return ', '.join(lora_parts + pts)


# ══════════════════════════════════════════════════════════════
# PULL / LIFT / ASIDE  →  "clothes pull"  (normalize)
# ══════════════════════════════════════════════════════════════

# Tất cả biến thể pull/lift/aside → chuẩn hóa về "clothes pull"
_TO_CLOTHES_PULL: Set[str] = {
    # pull
    'clothes pull', 'clothes_pull',
    'skirt pull', 'skirt_pull',
    'pantyhose pull', 'pantyhose_pull',
    'pants pull', 'pants_pull',
    'sweater pull', 'sweater_pull',
    'kimono pull', 'kimono_pull',
    'leotard pull', 'leotard_pull',
    'bikini pull', 'bikini_pull',
    'dress pull', 'dress_pull',
    'top pull', 'top_pull',
    # lift
    'clothes lift', 'clothes_lift',
    'shirt lift', 'shirt_lift',
    'skirt lift', 'skirt_lift',
    'dress lift', 'dress_lift',
    'sweater lift', 'sweater_lift',
    'kimono lift', 'kimono_lift',
    'hoodie lift', 'hoodie_lift',
    'jacket lift', 'jacket_lift',
    'bra lift', 'bra_lift',
    'sports bra lift', 'sports_bra_lift',
    'bikini top lift', 'bikini_top_lift',
    'top lift', 'top_lift',
    # aside / only
    'panties aside', 'panties_aside',
    'bikini bottom aside', 'bikini_bottom_aside',
    'thong aside', 'thong_aside',
    'leotard aside', 'leotard_aside',
    'swimsuit aside', 'swimsuit_aside',
    'buruma aside', 'buruma_aside',
    'clothing aside', 'clothing_aside',
}


def _normalize_pull(line: str) -> str:
    """Thay thế các pull/lift/aside tag bằng 'clothes pull', loại trùng."""
    tags   = [t.strip() for t in line.split(',') if t.strip()]
    out    = []
    seen   = set()
    for t in tags:
        mapped = 'clothes pull' if t.lower() in _TO_CLOTHES_PULL else t
        key    = mapped.lower()
        if key not in seen:
            out.append(mapped)
            seen.add(key)
    return ', '.join(out)


# ══════════════════════════════════════════════════════════════
# LORA PROMPT BUILDER
# ══════════════════════════════════════════════════════════════

def extract_lora_name(prompt: str) -> str:
    """Extract lora name from <lora:name:weight> syntax."""
    m = re.search(r'<lora:([^:>]+):', prompt)
    return m.group(1) if m else "unknown"


def build_lora_prompt(name: str, weight: float, activation: str) -> str:
    """
    Build '<lora:name:weight> activation_text' prompt string.
    If preferred_weight == 0, use 1.0 as default (webui behavior).
    """
    w = weight if weight else 1.0
    w_str = int(w) if w == int(w) else w   # 1.0 → "1", 0.8 → "0.8"
    base = f"<lora:{name}:{w_str}>"
    return f"{base} {activation.strip()}" if activation.strip() else base


# ══════════════════════════════════════════════════════════════
# RUN TAG ENHANCER  (subprocess)
# ══════════════════════════════════════════════════════════════

def run_tag_enhancer(folder: Path) -> Tuple[bool, str]:
    """Run tag_enhancer_v12.6_FINAL.py --folder <folder> as subprocess."""
    script_dir = Path(__file__).parent
    script = script_dir / "tag_enhancer_v12.6_FINAL.py"
    if not script.exists():
        return False, f"Not found: {script}"

    (folder / "out_tags").mkdir(exist_ok=True)
    try:
        r = subprocess.run(
            [sys.executable, str(script), "--folder", str(folder)],
            capture_output=True, text=True, timeout=300,
        )
        if (folder / "out_tags" / "addfaceless.txt").exists():
            return True, "tag_enhancer OK"
        return False, f"addfaceless.txt not created\n{r.stderr[:300]}"
    except Exception as e:
        return False, f"Error: {e}"


# ══════════════════════════════════════════════════════════════
# PROCESS CHARACTER TXT
# ══════════════════════════════════════════════════════════════

def process_character_txt(
    folder: Path,
    user_prompt: str,
) -> Tuple[bool, str, Optional[Path]]:
    """
    Read addfaceless.txt, apply tier system, write <lora_name>-character.txt.
    Returns (success, message, output_path_or_None).
    """
    script_dir   = Path(__file__).parent
    addfaceless  = folder / "out_tags" / "addfaceless.txt"
    if not addfaceless.exists():
        return False, "addfaceless.txt not found", None

    lora_name  = extract_lora_name(user_prompt)
    char_file  = folder / "out_tags" / f"{lora_name}-character.txt"
    facing_rm  = _facing_away_remove_tags(script_dir)

    try:
        raw_lines = [
            l.strip()
            for l in addfaceless.read_text(encoding='utf-8').splitlines()
            if l.strip()
        ]
        out_lines: List[str] = []
        exposed        = {'breasts': False, 'pussy': False, 'anus': False}
        prev_pull      = False
        prev_skirt_lift = False
        processed      = skipped = 0

        for base in raw_lines:
            btags = extract_tags(base)

            # Skip: mating press + ass focus combo
            if (
                {'mating press', 'ass focus'}   <= btags or
                {'mating_press', 'ass_focus'}   <= btags or
                {'mating press', 'ass_focus'}   <= btags or
                {'mating_press', 'ass focus'}   <= btags
            ):
                skipped += 1
                continue

            cp = _clean_prompt(user_prompt, btags)
            if cp is None:
                skipped += 1
                continue

            # Collect new tags from all tiers
            # Extract cp tags for skirt check (before any modification)
            cp_tags_lower = {t.strip().lower() for t in cp.split(',') if t.strip()}

            add: List[str] = []
            t0_tags, exposed    = tier_0(btags, exposed);                     add.extend(t0_tags)
            t1_tags, prev_pull  = tier_1(btags, prev_pull);                   add.extend(t1_tags)
            ts_tags, prev_skirt_lift = tier_skirt(btags, cp_tags_lower, prev_skirt_lift); add.extend(ts_tags)
            add.extend(process_stateless(btags))

            # leotard (character) + pull phần dưới trong user prompt → (((leotard aside, pussy)))
            if 'leotard' in btags:
                if cp_tags_lower & _LEOTARD_LOWER_PULL:
                    if '(((leotard aside, pussy)))' not in btags:
                        add.append('(((leotard aside, pussy)))')

            # Deduplicate (loại trùng trong add và trùng với btags)
            seen   = set(btags)
            unique = []
            for t in add:
                if t not in seen:
                    unique.append(t)
                    seen.add(t)
            raw    = f"{base}, {', '.join(unique)}" if unique else base
            final  = _normalize_pull(raw)

            # one breast out + breast out → xóa one breast out (redundant)
            _all_tags_lower = {t.strip().lower() for t in final.split(',')}
            _all_tags_lower |= cp_tags_lower
            if 'breast out' in _all_tags_lower or 'breasts out' in _all_tags_lower:
                final = ', '.join(
                    t for t in (p.strip() for p in final.split(','))
                    if t.lower() not in {'one breast out', 'one_breast_out'}
                )
                cp = ', '.join(
                    t for t in (p.strip() for p in cp.split(','))
                    if t.lower() not in {'one breast out', 'one_breast_out'}
                )

            # facing away / head back: remove head/face/eye/bangs tags
            if btags & (_FACING_AWAY | _HEAD_BACK):
                # remove from user prompt part
                cp = ', '.join(
                    t for t in (p.strip() for p in cp.split(','))
                    if t.lower() not in facing_rm
                )
                # remove from base tags part (final)
                final_parts = [t.strip() for t in final.split(',') if t.strip()]
                final_parts = [t for t in final_parts if t.lower() not in facing_rm]
                final = ', '.join(final_parts)

            # head back → replace with (((head back, facing away)))
            if btags & _HEAD_BACK:
                final_parts = [t.strip() for t in final.split(',') if t.strip()]
                seen_rep: set = set()
                replaced: List[str] = []
                for t in final_parts:
                    if t.lower() in _HEAD_BACK:
                        key = '(((head back, facing away)))'
                        if key not in seen_rep:
                            replaced.append(key)
                            seen_rep.add(key)
                    else:
                        if t.lower() not in seen_rep:
                            replaced.append(t)
                            seen_rep.add(t.lower())
                final = ', '.join(replaced)

            out_lines.append(f"{final}, {cp}")
            processed += 1

        char_file.write_text('\n'.join(out_lines), encoding='utf-8')
        msg = f"{processed}/{len(raw_lines)} lines, skipped {skipped} → {char_file.name}"
        return True, msg, char_file

    except Exception as e:
        return False, f"Error: {e}", None
