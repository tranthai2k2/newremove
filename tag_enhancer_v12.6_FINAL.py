#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import re
import sys
import random
from pathlib import Path
from typing import Set, Tuple, List, Dict
from collections import defaultdict
from datetime import datetime

from pathlib import Path
import argparse

DEFAULT_FOLDER = Path(r"D:\zhangyao\Noi\noi (24)")

# Parser arguments
parser = argparse.ArgumentParser(description="Tag Enhancer")
parser.add_argument(
    "--folder",
    type=Path,
    default=DEFAULT_FOLDER,
    help="Đường dẫn folder để process (mặc định: {})".format(DEFAULT_FOLDER),
)

args = parser.parse_args()

# DÙNG GIÁ TRỊ TỪ ARG, fallback về DEFAULT_FOLDER
FOLDER_TO_PROCESS = args.folder

FOLDER_TO_REMOVE = Path(r".\wantremove")
OUTPUT_FOLDER = FOLDER_TO_PROCESS / "out_tags"
OUTPUT_FOLDER.mkdir(exist_ok=True)

ALLTAGS_TXT = OUTPUT_FOLDER / "all_tags.txt"
HOP_TXT = OUTPUT_FOLDER / "hop_txt.txt"
ALLTAG_UNIQUE_TXT = OUTPUT_FOLDER / "all_tag.txt"
ADDFACELESS_TXT = OUTPUT_FOLDER / "addfaceless.txt"

LYING_INDICATORS = {
    "lying", "sleeping", "sleep molestation", "on back", "on bed", "on floor", 
    "on ground", "on stomach", "on side", "unconscious", "head on pillow"
}
IMMINENT_ORAL_TAGS = {
    "penis on face",
    "penis awe",
    "looking at penis",
}

SPREAD_EXPOSURE_TAGS = {
    "spread anus",
    "spread ass",
    "spread pussy",
    "anus spread",
    "ass spread"
}
CUM_ORAL_TAGS = {
    "cum in mouth",
    "cum in nose",
    "cum on tongue",
    "mouth full"
}

tags_to_remove = {
    "1boy", "2boys", "multiple boys",
    "hetero",                        # ← Removes!
    "clothed female nude male",      # ← Removes!
    "imminent rape",                 # ← Removes!
    "fat man", "faceless male", "bald"
}
EXISTING_GRAB_TAGS = {
    # Head/neck
    "head grab", "hand on another's head", "neck grab",
    
    # Arms/shoulders
    "arm grab", "shoulder grab",
    
    # Torso
    "torso grab", "chest grab", "belly grab",
    
    # Breast/ass (conflicts with GROPING_OPTIONS)
    "grabbing another's breast", "groping", "breast grab",
    "ass grab", "grabbing another's ass",
    
    # Breast actions (NEW)
    "breast sucking",
    "breast pressing",
    "nipple stimulation",
    
    # Legs
    "leg grab", "thigh grab",
    
    # General
    "grabbing", "grabbing from behind"
}
CONTACT_ACTIONS = {
    "grabbing another's breast", "lifting another's clothes", "pulling another's clothes", 
    "undressing another", "breast sucking", "hand on another's head", "hand on another's breast", 
    "hand on another's ass", "leg grab", "ass grab", "arm grab", "fingering", "groping", 
    "licking another's", "kissing", "tongue", "breast pressing", "nipple stimulation", 
    "assisted exposure", "grabbing from behind", "grabbing", "hand on another's stomach", 
    "torso grab", "chest grab", "belly grab", "shoulder grab", "neck grab",  "arm grab"
}
# NEW V12.7-ALPHA: Clothing manipulation tags
CLOTHING_MANIPULATION_TAGS = {
    "panty pull",
    "pulling another's clothes",
    "shirt lift",
    "clothes lift",
    "clothes pull",
    "skirt lift",
    "lifting another's clothes",
    "assisted exposure",
    "clothes tug",
    "undressing another"
}
SEX_POSITIONS = {
    "missionary", "boy on top", "cowgirl position", "girl on top", "reverse cowgirl", 
    "reverse upright straddle", "doggystyle", "sex from behind", "mating press", "prone bone", 
    "standing sex", "spooning", "just the tip", "straddling", "seated", "suspended congress"
}
PENETRATION_TAGS = {
    "vaginal", "anal", "penis", "cum", "ejaculation", "internal cumshot", 
    "cum in pussy", "cum in mouth", "penetration", "imminent penetration", 
    "deep penetration", "vaginal penetration", "anal penetration"
}
ORAL_TAGS = {
    "oral", "fellatio", "deepthroat", "irrumatio", "imminent fellatio", 
    "blowjob", "handjob", "cunnilingus", "oral sex"
}

RAPE_TAGS = {
    "rape", "sleep molestation", "imminent rape", "sexual assault", 
    "molestation", "non-consensual", "forced"
}

DOGGYSTYLE_TAGS = {
    "doggystyle", "all_fours", "all fours", "sex from behind", "from behind"
}

POV_TAGS = {
    "pov hands", "pov crotch", "pov", "pov feet"
}
# ==================== NEW V12.6 CONSTANTS ====================
RESTRAINT_TAGS = {
    "bound arms", "restrained", "bound wrists", "arms behind back",
    "bound", "bondage", "tied up", "rope bondage", "bound legs", 
    "wrist cuffs", "leg cuffs", "cuffs"
}

GROPING_OPTIONS = [
    {"ass grab", "grabbing another's ass"},
    {"grabbing another's breast", "groping"}
]

NSFW_KEYWORDS = {
    "cum", "sex", "vaginal", "anal", "nude", "pussy", "penetration", "breast", "nipples", 
    "fingering", "fuck", "sperm", "intercourse", "cervix", "creampie", "ejaculation", "rape", 
    "clit", "clitoris", "penis", "pussy juice", "orgasm", "blowjob", "handjob", "titjob", 
    "paizuri", "fellatio", "cunnilingus", "erection", "testicles", "labia", "vulva", "anus", 
    "masturbation", "bondage", "restrained", "shibari", "rope", "deepthroat", "irrumatio", 
    "cumdrip", "cum overflow", "pubic hair", "spread legs", "spread pussy", "spread anus", 
    "x-ray", "cross-section", "uterus", "saliva", "tongue out", "french kiss", "licking", 
    "hetero", "ass grab", "uncensored", "rape", "molestation"
}

ANIMAL_EAR_TAGS = {
    "animal ears", "bat ears", "bear ears", "rabbit ears", "cat ears", "cow ears", 
    "deer ears", "dog ears", "fox ears", "wolf ears", "horse ears", "sheep ears", 
    "goat ears", "pig ears", "ferret ears", "mouse ears", "squirrel ears", "tiger ears", 
    "lion ears", "monkey ears", "panda ears", "pikachu ears", "floppy ears"
}
# Define all torn tags
TORN_TAGS = {
    "torn apron", "torn armband", "torn ascot", "torn bike shorts", 
    "torn bikini", "torn bodystocking", "torn bodysuit", "torn bra", 
    "torn buruma", "torn camisole", "torn cape", "torn capelet", 
    "torn choker", "torn cloak", "torn coat", "torn dress", 
    "torn gloves", "torn hakama", "torn hat", "torn headband", 
    "torn hoodie", "torn jacket", "torn jumpsuit", "torn kimono", 
    "torn leggings", "torn leotard", "torn loincloth", "torn neckerchief", 
    "torn necktie", "torn overalls", "torn panties", "torn pants", 
    "torn pantyhose", "torn robe", "torn sarong", "torn scarf", 
    "torn shirt", "torn shorts", "torn skirt", "torn sleeves", 
    "torn socks", "torn sports bra", "torn sweater", "torn sweater vest", 
    "torn swimsuit", "torn tabard", "torn tank top", "torn thighhighs", 
    "torn tube top", "torn unitard", "torn veil", "torn leg warmers",
    "torn boots", "torn shoes", "torn wings", "torn towel",
    "ripped clothes", "ripped clothing", "torn clothing"
}
# ==================== TIER 0.5 (NEW): COLORED PUBIC HAIR CONSOLIDATION ====================

COLORED_PUBIC_HAIR_TAGS = {
    "aqua pubic hair",
    "blonde pubic hair",
    "blue pubic hair",
    "green pubic hair",
    "grey pubic hair",
    "multicolored pubic hair",
    "orange pubic hair",
    "pink pubic hair",
    "purple pubic hair",
    "red pubic hair",
    "white pubic hair",
    "colored pubic hair"  # Include parent tag if present
}

def tier_0_5_colored_pubic_hair_consolidation(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-NEW: Consolidate all colored pubic hair variants → 'colored pubic hair'"""
    
    found_colored_tags = []
    
    # Check for any colored pubic hair variants
    for tag in list(tags):
        if tag in COLORED_PUBIC_HAIR_TAGS and tag != "colored pubic hair":
            found_colored_tags.append(tag)
            tags.discard(tag)
    
    # Add parent tag if any variant found
    if found_colored_tags:
        if "colored pubic hair" not in tags:
            tags.add("colored pubic hair")
        return True, f"colored_pubic_hair_consolidation: {len(found_colored_tags)} tags → colored_pubic_hair"
    
    return False, ""

def tier_new_torn_clothes_consolidation(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-ALPHA: Consolidate all torn tags into 'torn clothes'"""
    
    found_torn_tags = []
    
    # Check for any torn tags
    for tag in list(tags):
        if tag in TORN_TAGS:
            found_torn_tags.append(tag)
            tags.discard(tag)
    
    # Add "torn clothes"
    if found_torn_tags:
        if "torn clothes" not in tags:
            tags.add("torn clothes")
        
        return True, f"torn_consolidation: {len(found_torn_tags)} tags → torn_clothes"
    
    return False, ""

def normalize_tag(t: str) -> str:
    return re.sub(r"[(){}]", "", t.strip()).lower()

def check_tag_exists(tags_set: Set[str], target: str) -> bool:
    norm_target = normalize_tag(target)
    return any(normalize_tag(tag) == norm_target for tag in tags_set)

def has_any_tag(tags_set: Set[str], tag_list: Set[str]) -> bool:
    return any(tag in tags_set for tag in tag_list)

def is_self_exposure(tags: Set[str]) -> bool:
    """Check if solo/self-exposure (no male character)"""
    # Original: POV + solo focus
    if "pov" in tags and "solo focus" in tags:
        return True
    
    # NEW: solo focus + assisted exposure
    if "solo focus" in tags:
        has_assisted = any(t in tags for t in {
            "assisted exposure", 
            "panty pull", 
            "skirt pull",
            "pulling another's clothes", 
            "clothes pull",
            "dress pull"
        })
        if has_assisted:
            return True
    
    return False

def tier_2l_kissing_faceless_bald(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-NEW: French kiss/kissing → add faceless male + bald"""
    
    # Check for kissing tags
    has_kissing = any(t in tags for t in {
        "french kiss", "kissing", "kiss", "deep kiss"
    })
    
    if not has_kissing:
        return False, ""
    
    # Block if self-exposure (POV + solo)
    if is_self_exposure(tags):
        return False, ""
    
    # Require hetero context: ANY boy tag + 1girl
    has_boy = any(check_tag_exists(tags, boy_tag) for boy_tag in [
        "1boy", "2boys", "multiple boys"
    ])
    has_1girl = check_tag_exists(tags, "1girl")
    
    if not (has_boy and has_1girl):
        return False, ""
    
    added = []
    
    # Add faceless male (with emphasis)
    if not check_tag_exists(tags, "faceless male"):
        tags.add("((faceless male))")
        added.append("faceless_male")
    
    # Add bald
    if "bald" not in tags and "((bald))" not in tags:
        tags.add("((bald))")
        added.append("bald")
    
    if added:
        return True, f"kissing: added {', '.join(added)}"
    
    return False, ""

def tier_new_solo_assisted_exposure_cleanup(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-ALPHA: Remove sex tags from solo + assisted exposure"""
    has_solo = "solo focus" in tags
    has_assisted = any(t in tags for t in {
        "assisted exposure", "panty pull", "skirt pull",
        "pulling another's clothes", "clothes pull", "dress pull"
    })
    
    if not (has_solo and has_assisted):
        return False, ""
    
    # Remove wrong sex tags
    removed = []
    sex_tags_to_remove = {
        "hetero", "1boy", "imminent rape", "imminent penetration",
        "clothed female nude male", "sex", "penetration", "vaginal", "rape"
    }
    
    for tag in sex_tags_to_remove:
        if tag in tags:
            tags.discard(tag)
            removed.append(tag)
    
    if removed:
        return True, f"solo_assisted_exposure: removed {', '.join(removed)}"
    
    return False, ""

def has_explicit_sex_position(tags_set: Set[str]) -> bool:
    """NEW V12.6: Check if has explicit sex position to bypass pov+solo blocking"""
    return has_any_tag(tags_set, SEX_POSITIONS)

def split_tags(line: str) -> List[str]:
    return [t.strip() for t in line.split(",") if t.strip()] if line else []

def write_file(path: Path, lines: List[str]) -> None:
    try:
        path.write_text("\n".join(lines), encoding="utf-8")
    except Exception as e:
        print(f"❌ Error writing {path}: {e}")

def load_remove_tags(folder: Path) -> Set[str]:
    tags = set()
    if not folder.exists():
        return tags
    for txt_file in folder.glob("*.txt"):
        try:
            content = txt_file.read_text(encoding="utf-8")
            for line in content.split("\n"):
                for tag in line.split(","):
                    clean = tag.strip()
                    if clean:
                        tags.add(clean)
        except Exception:
            pass
    return tags
def tier_new_nipples_breasts_out(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-NEW: nipples → breasts out (với blocking conditions)"""
    
    # Check if has nipples
    if "nipples" not in tags:
        return False, ""
    
    # Block if already has breasts out
    if "breasts out" in tags or "breast out" in tags:
        return False, ""
    
    # Block if nude/topless (không cần breasts out)
    blocking_tags = {
        "nude",
        "completely nude",
        "topless",
        "naked",
        "undressed"
    }
    
    if has_any_tag(tags, blocking_tags):
        return False, ""
    
    # Block if female focus without male (solo scene)
    has_boy = any(check_tag_exists(tags, boy_tag) for boy_tag in [
        "1boy", "2boys", "multiple boys"
    ])
    
    # Only add if hetero context OR lesbian context
    has_girl = "1girl" in tags or "2girls" in tags or "multiple girls" in tags
    
    if not (has_boy or "2girls" in tags or "multiple girls" in tags):
        return False, ""
    
    # Add breasts out
    tags.add("breasts out")
    return True, "nipples_visible: added breasts_out"

def tier_0_arms_up(tags: Set[str]) -> Tuple[bool, str]:
    added = []
    removed = []

    if "spread pussy" in tags:
        if not check_tag_exists(tags, "arms up"):
            tags.add("arms up")
            added.append("arms_up")

    if is_self_exposure(tags):
        has_oral = has_any_tag(tags, ORAL_TAGS)
        if not has_oral:
            return (False, "")

    if "all fours" in tags or "all_fours" in tags:
        tags.discard("(1girl, arms up)")
        tags.discard("arms up")
        return (False, "")
    
    if "arm grab" in tags:
        tags.discard("arm grab")
        removed.append("arm_grab")
    if "lying" in tags:
        if "on stomach" in tags and "prone bone" in tags:
             tags.discard("(1girl, arms up)")
             tags.discard("arms up")
             return (False, "")

    has_lying = has_any_tag(tags, LYING_INDICATORS)
    has_contact = has_any_tag(tags, CONTACT_ACTIONS)
    has_fellatio = has_any_tag(tags, ORAL_TAGS)
    has_sex_pos = has_any_tag(tags, SEX_POSITIONS)
    has_cowgirl = has_any_tag(tags, {"cowgirl position", "girl on top"})
    has_penetration = has_any_tag(tags, PENETRATION_TAGS)
    
    if has_lying and has_contact and not has_fellatio:
        if has_penetration or has_sex_pos:
            if not check_tag_exists(tags, "arms up"):
                tags.add("arms up")
                added.append("arms_up")
    
    if has_cowgirl and has_contact and has_penetration:
        if not check_tag_exists(tags, "arms up"):
            tags.add("arms up")
            added.append("arms_up")
    
    messages = []
    if removed:
        messages.append(f"removed {', '.join(removed)}")
    if added:
        messages.append(f"added {', '.join(added)}")
    
    if messages:
        return (True, f"arms_up: {' | '.join(messages)}")
    else:
        return (False, "")

def tier_1_faceless_wrapping(tags: Set[str]) -> Tuple[bool, str]:
    if is_self_exposure(tags):
        return False, ""
    
    if "faceless male" in tags and "((faceless male))" not in tags:
        tags.discard("faceless male")
        tags.add("((faceless male))")
    
    if "bald" in tags and "((bald))" not in tags:
        tags.discard("bald")
        tags.add("((bald))")
    
    if "((faceless male))" in tags and "((bald))" not in tags and "bald" not in tags:
        tags.add("((bald))")
        return True, "faceless pair requirement: added ((bald))"
    
    return False, ""

def tier_1_5_clothed_female_nude_male(tags: Set[str]) -> Tuple[bool, str]:
    # Skip if already present
    if check_tag_exists(tags, "clothed female nude male"):
        return False, ""
    
    # Block POV + solo scenes
    if is_self_exposure(tags):
        return False, ""
    
    # Block fingering POV solo
    if is_fingering_self_exposure(tags):
        return False, ""
    
    # ✅ FIX: Use check_tag_exists
    has_1boy = check_tag_exists(tags, "1boy")
    has_1girl = check_tag_exists(tags, "1girl")
    
    has_faceless = check_tag_exists(tags, "faceless male")
    has_penetration = has_any_tag(tags, PENETRATION_TAGS)
    has_contact = has_any_tag(tags, CONTACT_ACTIONS)
    has_oral = has_any_tag(tags, ORAL_TAGS)
    # ✅ REMOVED: has_pov
    
    if has_1boy and has_1girl:
        # ✅ FIX: Removed has_pov
        if has_faceless or has_penetration or has_contact or has_oral:
            tags.add("clothed female nude male")
            return True, "clothed_female_nude_male: added"
    
    return False, ""

# Define helper function
def is_fingering_self_exposure(tags: Set[str]) -> bool:
    """Check if fingering + pov + solo"""
    return "fingering" in tags and "pov" in tags and "solo focus" in tags

# ==================== TIER 1.6: POV FINGERING - ARMS BEHIND BACK ====================
def tier_1_6_pov_fingering_arms_behind_back(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-ALPHA: POV fingering solo → arms behind back"""
    has_fingering = "fingering" in tags
    has_pov = "pov" in tags  # ← FIX: Only exact "pov" tag
    has_solo = "solo focus" in tags
    has_spread_legs = "spread legs" in tags
    
    if not (has_fingering and has_pov and has_solo and has_spread_legs):
        return False, ""
    
    if "1girl" not in tags:
        return False, ""
    
    if check_tag_exists(tags, "arms behind back"):
        return False, ""
    
    tags.discard("1girl")
    tags.add("((1girl, arms behind back))")
    return True, "pov_fingering: wrapped 1girl with arms behind back"

def tier_new_pov_solo_cleanup(tags: Set[str]) -> Tuple[bool, str]:
    """NEW V12.6: Remove hetero and imminent rape when pov+solo"""
    if not is_self_exposure(tags):
        return False, ""
    removed = []
    if "hetero" in tags:
        tags.discard("hetero")
        removed.append("hetero")
    if "imminent rape" in tags:
        tags.discard("imminent rape")
        removed.append("imminent_rape")
    if removed:
        return True, f"pov_solo_cleanup: removed {', '.join(removed)}"
    return False, ""

# def tier_new_restraint_grouping(tags: Set[str]) -> Tuple[bool, str]:
#     """V12.7-ALPHA: Comprehensive groping blocking"""
#     has_restraint = has_any_tag(tags, RESTRAINT_TAGS)
#     if not has_restraint:
#         return False, ""
    
#     has_1girl = "1girl" in tags
#     if not has_1girl:
#         return False, ""
    
#     # Block if self-exposure
#     if is_self_exposure(tags):
#         return False, ""
    
#     # ✅ 8 BLOCKING CONDITIONS
#     has_oral = has_any_tag(tags, ORAL_TAGS)
#     has_clothing_manipulation = has_any_tag(tags, CLOTHING_MANIPULATION_TAGS)
#     has_existing_grabs = has_any_tag(tags, EXISTING_GRAB_TAGS)
#     has_1boy = "1boy" in tags
#     has_cum_oral = has_any_tag(tags, CUM_ORAL_TAGS) and has_oral
#     has_spread_exposure = has_any_tag(tags, SPREAD_EXPOSURE_TAGS)
#     has_generic_grabbing = any("grabbing" in tag for tag in tags)
    
#     # Remove and group
#     tags.discard("1girl")
#     for tag in list(RESTRAINT_TAGS):
#         if tag in tags:
#             tags.discard(tag)
    
#     tags.add("((1girl, restrained, bound wrists))")
    
#     # Build blocking reasons
#     block_reasons = []
#     if has_oral:
#         block_reasons.append("has oral")
#     if has_clothing_manipulation:
#         block_reasons.append("has clothing manipulation")
#     if has_existing_grabs:
#         block_reasons.append("has existing grabs")
#     if not has_1boy:
#         block_reasons.append("no 1boy")
#     if has_cum_oral:
#         block_reasons.append("cum in mouth/nose")
#     if has_spread_exposure:
#         block_reasons.append("spread anus/ass")
#     if has_generic_grabbing:
#         block_reasons.append("has generic grabbing")
    
#     # Skip groping if ANY blocking condition
#     if block_reasons:
#         reason_str = ", ".join(block_reasons)
#         return True, f"restraint_grouping: grouped (no groping - {reason_str})"
    
#     # Add random groping ONLY if NO blocking
#     chosen_option = random.choice(GROPING_OPTIONS)
#     for tag in chosen_option:
#         if tag not in tags:
#             tags.add(tag)
    
#     return True, f"restraint_grouping: grouped + groping"

def tier_new_restraint_grouping(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-ALPHA: Comprehensive groping blocking"""
    has_restraint = has_any_tag(tags, RESTRAINT_TAGS)
    if not has_restraint:
        return False, ""
    
    has_1girl = "1girl" in tags
    if not has_1girl:
        return False, ""
    
    if is_self_exposure(tags):
        return False, ""
    
    # ✅ 8 BLOCKING CONDITIONS
    has_oral = has_any_tag(tags, ORAL_TAGS)
    has_clothing_manipulation = has_any_tag(tags, CLOTHING_MANIPULATION_TAGS)
    has_existing_grabs = has_any_tag(tags, EXISTING_GRAB_TAGS)
    has_1boy = "1boy" in tags
    has_cum_oral = has_any_tag(tags, CUM_ORAL_TAGS) and has_oral
    has_spread_exposure = has_any_tag(tags, SPREAD_EXPOSURE_TAGS)
    has_generic_grabbing = any("grabbing" in tag for tag in tags)
    has_suspended_position = has_any_tag(tags, {
        "reverse suspended congress", "suspended congress",
        "carrying", "carried", "lifted by another", "princess carry",
        "standing split", "leg hold", "lifted"
    })
    # Remove and group
    tags.discard("1girl")
    for tag in list(RESTRAINT_TAGS):
        if tag in tags:
            tags.discard(tag)
    
    tags.add("((1girl, restrained, bound wrists))")
    
     # Build blocking reasons
    block_reasons = []
    if has_oral:
        block_reasons.append("has oral")
    if has_clothing_manipulation:
        block_reasons.append("has clothing manipulation")
    if has_existing_grabs:
        block_reasons.append("has existing grabs")
    if not has_1boy:
        block_reasons.append("no 1boy")
    if has_cum_oral:
        block_reasons.append("cum in mouth/nose")
    if has_spread_exposure:
        block_reasons.append("spread anus/ass")
    if has_generic_grabbing:
        block_reasons.append("has generic grabbing")
    if has_suspended_position:
        block_reasons.append("has suspended/carrying position")  # ← NEW
    
    # Skip groping if ANY blocking condition
    if block_reasons:
        reason_str = ", ".join(block_reasons)
        return True, f"restraint_grouping: grouped (no groping - {reason_str})"
    
    # Add groping only if NO blocking
    chosen_option = random.choice(GROPING_OPTIONS)
    for tag in chosen_option:
        if tag not in tags:
            tags.add(tag)
    
    return True, f"restraint_grouping: grouped + groping"

def tier_2a_doggystyle_fat_man(tags: Set[str]) -> Tuple[bool, str]:
    # NEW V12.6: Bypass pov+solo block if has sex position
    if is_self_exposure(tags) and not has_explicit_sex_position(tags):
        return False, ""
    if is_fingering_self_exposure(tags):
        return False, ""
     # ✅ NEW V12.7: Block POV aftermath scenes
    has_aftermath = any(tag in tags for tag in {"after sex", "after vaginal"})
    has_pov_hands = "pov hands" in tags
    has_solo = "solo focus" in tags
    
    if has_aftermath and has_pov_hands and has_solo:
        return False, ""  # Block: POV aftermath scene
    has_doggy = has_any_tag(tags, DOGGYSTYLE_TAGS)
    has_penetration = has_any_tag(tags, PENETRATION_TAGS)
    
    if has_doggy and has_penetration:
        if "fat man" not in tags and "((fat man))" not in tags:
            tags.add("((fat man))")
            return True, "doggystyle: added ((fat man))"
    
    return False, ""

def tier_2b_rape_fat_man(tags: Set[str]) -> Tuple[bool, str]:
    # NEW V12.6: Bypass pov+solo block if has sex position
    if is_self_exposure(tags) and not has_explicit_sex_position(tags):
        return False, ""
    if is_fingering_self_exposure(tags):
        return False, ""
    
    has_rape = has_any_tag(tags, RAPE_TAGS)
    has_sex_pos = has_any_tag(tags, SEX_POSITIONS)
    has_contact = has_any_tag(tags, CONTACT_ACTIONS)
    has_pov_hands = "pov hands" in tags
    has_penetration = has_any_tag(tags, PENETRATION_TAGS)
    
    if has_rape and (has_sex_pos or has_contact or has_pov_hands) and has_penetration:
        if "fat man" not in tags and "((fat man))" not in tags:
            tags.add("((fat man))")
            return True, "rape: added ((fat man))"
    
    return False, ""
def tier_2j_standing_holding_leg_faceless_add_fat_man(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-NEW: Đã có faceless+bald + standing sex + holding leg → thêm fat man"""
    if is_self_exposure(tags):
        return False, ""
    
    has_standing_sex = "standing sex" in tags
    has_holding_leg = has_any_tag(tags, {
        "leg lift", "leg up", "lifted leg", "leg hold",
        "holding another's leg", "holding leg", "standing on one leg",
        "legs up", "leg grab"
    })
    
    # ✅ Kiểm tra ĐÃ CÓ faceless + bald
    has_faceless = check_tag_exists(tags, "faceless male")
    has_bald = "bald" in tags or "((bald))" in tags
    
    # ✅ Nếu đã có faceless + bald + standing sex + holding leg
    # KHÔNG cần from behind, KHÔNG cần penetration tag
    if has_faceless and has_bald and has_standing_sex and has_holding_leg:
        if not check_tag_exists(tags, "fat man"):
            tags.add("((fat man))")
            return True, "standing_holding_leg+faceless_exists: added fat_man"
    
    return False, ""

def tier_2k_oral_pov_sitting_fat_man(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-ALPHA: Oral/imminent + pov/sitting + solo → fat man"""
    has_oral = has_any_tag(tags, ORAL_TAGS)
    has_imminent = has_any_tag(tags, IMMINENT_ORAL_TAGS)  # ← NEW
    has_pov = has_any_tag(tags, POV_TAGS)
    has_sitting = "sitting" in tags or "kneeling" in tags
    has_solo = "solo focus" in tags
    
    # ✅ Check oral OR imminent
    if (has_oral or has_imminent) and (has_pov or has_sitting) and has_solo:
        if "((fat man))" not in tags and "fat man" not in tags:
            tags.add("((fat man))")
            return True, "oral_pov_sitting: added fat man"
    
    return False, ""

def tier_2c_all_fours_handjob_fat_man(tags: Set[str]) -> Tuple[bool, str]:
    if is_self_exposure(tags):
        return False, ""
    
    has_all_fours = has_any_tag(tags, {"all fours", "all_fours", "on hands and knees"})
    has_handjob = has_any_tag(tags, {"handjob", "hand job", "jerking off", "hand stimulation"})
    has_penetration = has_any_tag(tags, PENETRATION_TAGS)
    
    if has_all_fours and has_handjob and has_penetration:
        if "fat man" not in tags and "((fat man))" not in tags:
            tags.add("((fat man))")
            return True, "all_fours+handjob: added ((fat man))"
    
    return False, ""
# ==================== TIER 2D: CUNNILINGUS - FACELESS + BALD ====================
def tier_2d_cunnilingus_faceless_bald(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-ALPHA: Cunnilingus → add faceless male + bald"""
    has_cunnilingus = "cunnilingus" in tags
    
    if not has_cunnilingus:
        return False, ""
    
    # Block if self-exposure (rare but possible)
    if is_self_exposure(tags):
        return False, ""
    
    added = []
    
    # Add faceless male (with emphasis)
    if not check_tag_exists(tags, "faceless male"):
        tags.add("((faceless male))")
        added.append("faceless_male")
    
    # Add bald
    if "bald" not in tags:
        tags.add("bald")
        added.append("bald")
    
    return (True, f"cunnilingus: added {', '.join(added)}") if added else (False, "")
# ==================== TIER 2E: PRINCESS CARRY - FAT MAN ====================
def tier_2e_princess_carry_fat_man(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-ALPHA: Princess carry/carrying → add fat man"""
    has_princess_carry = "princess carry" in tags
    has_carrying = "carrying" in tags
    
    # Require princess carry OR carrying
    if not (has_princess_carry or has_carrying):
        return False, ""
    
    # Block if self-exposure (rare but possible)
    if is_self_exposure(tags):
        return False, ""
    
    # Check if fat man already exists
    if check_tag_exists(tags, "fat man"):
        return False, ""
    
    # Add fat man
    tags.add("((fat man))")
    return True, "princess_carry: added ((fat man))"

def tier_2d1_cunnilingus_faceless_bald(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-ALPHA: Cunnilingus → add faceless male + bald"""
    has_cunnilingus = "cunnilingus" in tags
    
    if not has_cunnilingus:
        return False, ""
    
    if is_self_exposure(tags):
        return False, ""
    
    added = []
    
    if not check_tag_exists(tags, "faceless male"):
        tags.add("((faceless male))")
        added.append("faceless_male")
    
    if "bald" not in tags:
        tags.add("bald")
        added.append("bald")
    
    return (True, f"cunnilingus: added {', '.join(added)}") if added else (False, "")

def tier_2e_hetero_irrumatio_contact_fat_man(tags: Set[str]) -> Tuple[bool, str]:
    if is_self_exposure(tags):
        return False, ""
    
    has_hetero = "hetero" in tags
    has_irrumatio = "irrumatio" in tags
    has_contact = has_any_tag(tags, CONTACT_ACTIONS)
    has_pov_hands = "pov hands" in tags
    
    if has_hetero and has_irrumatio and (has_contact or has_pov_hands):
        if "fat man" not in tags and "((fat man))" not in tags:
            tags.add("((fat man))")
            return True, "hetero+irrumatio+contact: added ((fat man))"
    
    return False, ""

def tier_2f_holding_leg_standing_sex_behind_faceless(tags: Set[str]) -> Tuple[bool, str]:
    if is_self_exposure(tags):
        return False, ""
    
    # ✅ COMPLETE FIX:
    has_holding_leg = any(t in tags for t in {
        "holding another's leg", "holding leg", "leg hold", 
        "lifted leg", "legs up", "legs in air",
        "leg grab", "leg lift", "leg up"  # ← ADD THESE 3
    })

    has_standing = "standing" in tags
    has_sex_behind = has_any_tag(tags, {"sex from behind", "from behind"})
    has_standing_split = "standing split" in tags  # ← ADD THIS

    has_penetration = has_any_tag(tags, PENETRATION_TAGS)
    
    added = []
    
    if has_holding_leg and has_standing and (has_sex_behind or has_standing_split) and has_penetration:
        if "faceless male" not in tags and "((faceless male))" not in tags:
            tags.add("((faceless male))")
            added.append("faceless_male")
        if "bald" not in tags and "((bald))" not in tags:
            tags.add("((bald))")
            added.append("bald")
        if "fat man" not in tags and "((fat man))" not in tags:
            tags.add("((fat man))")
            added.append("fat_man")
        
        if added:
            return True, f"holding_leg+standing+sex_behind: added {', '.join(added)}"
    
    return False, ""

def tier_2g_reverse_cowgirl_faceless_fat_man_bald(tags: Set[str]) -> Tuple[bool, str]:
    if is_self_exposure(tags):
        return False, ""
    
    has_reverse_cowgirl = any(t in tags for t in {
        "reverse cowgirl", "reverse cowgirl position", "reverse upright straddle", "reverse riding"
    })
    has_straddling = any(t in tags for t in {
        "straddling", "woman straddling", "astride", "straddling position"
    })
    has_penetration = has_any_tag(tags, PENETRATION_TAGS)
    has_1girl = "1girl" in tags
    
    added = []
    
    if (has_reverse_cowgirl or has_straddling) and has_penetration and has_1girl:
        if "faceless male" not in tags and "((faceless male))" not in tags:
            tags.add("((faceless male))")
            added.append("faceless_male")
        if "fat man" not in tags and "((fat man))" not in tags:
            tags.add("((fat man))")
            added.append("fat_man")
        if "bald" not in tags and "((bald))" not in tags:
            tags.add("((bald))")
            added.append("bald")
        
        if added:
            return True, f"reverse_cowgirl+straddling: added {', '.join(added)}"
    
    return False, ""

def tier_2h_spooning_faceless_fat_man_bald(tags: Set[str]) -> Tuple[bool, str]:
    if is_self_exposure(tags):
        return False, ""
    
    has_spooning = "spooning" in tags
    has_sex_behind = has_any_tag(tags, {"sex from behind", "from behind"})
    has_penetration = has_any_tag(tags, PENETRATION_TAGS)
    
    added = []
    
    if has_spooning and has_sex_behind and has_penetration:
        if "((faceless male))" not in tags and "faceless male" not in tags:
            tags.add("((faceless male))")
            added.append("faceless_male")
        if "((bald))" not in tags and "bald" not in tags:
            tags.add("((bald))")
            added.append("bald")
        if "((fat man))" not in tags and "fat man" not in tags:
            tags.add("((fat man))")
            added.append("fat_man")
        
        if added:
            return True, f"spooning+sex_behind: added {', '.join(added)}"
    
    return False, ""
def tier_2h_v2_spooning_penetration_faceless(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-NEW: Spooning + penetration (without explicit 'from behind') → faceless trio"""
    
    if is_self_exposure(tags):
        return False, ""
    
    has_spooning = "spooning" in tags
    has_sex_behind = has_any_tag(tags, {"sex from behind", "from behind"})
    has_penetration = has_any_tag(tags, PENETRATION_TAGS)
    
    # Only trigger if spooning WITHOUT explicit "sex from behind"
    if not (has_spooning and has_penetration and not has_sex_behind):
        return False, ""
    
    added = []
    
    if not check_tag_exists(tags, "faceless male"):
        tags.add("((faceless male))")
        added.append("faceless_male")
    
    if "bald" not in tags and "((bald))" not in tags:
        tags.add("((bald))")
        added.append("bald")
    
    if "fat man" not in tags and "((fat man))" not in tags:
        tags.add("((fat man))")
        added.append("fat_man")
    
    if added:
        return True, f"spooning_v2: added {', '.join(added)}"
    
    return False, ""

def tier_2i_v2_standing_sex_faceless_add_fat_man(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-NEW: Nếu ĐÃ CÓ faceless+bald + standing sex → chỉ thêm fat man"""
    if is_self_exposure(tags):
        return False, ""
    
    has_standing_sex = "standing sex" in tags
    has_sex_behind = has_any_tag(tags, {"sex from behind", "from behind"})
    
    # ✅ Kiểm tra ĐÃ CÓ faceless + bald
    has_faceless = check_tag_exists(tags, "faceless male")
    has_bald = "bald" in tags or "((bald))" in tags
    
    # ✅ Nếu đã có faceless + bald + standing sex + sex behind
    if has_faceless and has_bald and has_standing_sex and has_sex_behind:
        # Chỉ thêm fat man (KHÔNG cần penetration tag)
        if not check_tag_exists(tags, "fat man"):
            tags.add("((fat man))")
            return True, "standing_sex+faceless_exists: added fat_man"
    
    return False, ""

def tier_2i_standing_sex_behind_faceless_fat_man_bald(tags: Set[str]) -> Tuple[bool, str]:
    if is_self_exposure(tags):
        return False, ""
    
    has_standing_sex = "standing sex" in tags
    has_sex_behind = has_any_tag(tags, {"sex from behind", "from behind"})
    has_penetration = has_any_tag(tags, PENETRATION_TAGS)
    
    added = []
    
    if has_standing_sex and has_sex_behind and has_penetration:
        if "((faceless male))" not in tags and "faceless male" not in tags:
            tags.add("((faceless male))")
            added.append("faceless_male")
        if "((bald))" not in tags and "bald" not in tags:
            tags.add("((bald))")
            added.append("bald")
        if "((fat man))" not in tags and "fat man" not in tags:
            tags.add("((fat man))")
            added.append("fat_man")
        
        if added:
            return True, f"standing_sex+sex_behind: added {', '.join(added)}"
    
    return False, ""

def tier_2_lying_faceless_contact_fat_man(tags: Set[str]) -> Tuple[bool, str]:
    if is_self_exposure(tags):
        return False, ""
    
    has_lying = has_any_tag(tags, LYING_INDICATORS)
    has_faceless = "((faceless male))" in tags
    has_contact = has_any_tag(tags, CONTACT_ACTIONS)
    has_solo = "solo focus" in tags
    has_sex_pos = has_any_tag(tags, SEX_POSITIONS)
    
    if has_lying and has_faceless and has_contact:
        if has_solo and not has_sex_pos:
            return False, ""
        
        if "fat man" not in tags and "((fat man))" not in tags:
            tags.add("((fat man))")
            return True, "lying+faceless+contact: added ((fat man))"
    
    return False, ""

def tier_3_sleep_faceless_penetration(tags: Set[str]) -> Tuple[bool, str]:
    if is_self_exposure(tags):
        return False, ""
    
    has_sleep = "sleep molestation" in tags
    has_faceless = "((faceless male))" in tags
    has_penetration = has_any_tag(tags, PENETRATION_TAGS)
    has_oral = has_any_tag(tags, ORAL_TAGS)
    
    added = []
    
    if has_sleep and has_faceless and (has_penetration or has_oral):
        if "fat man" not in tags and "((fat man))" not in tags:
            tags.add("((fat man))")
            added.append("fat_man")
        if "bald" not in tags and "((bald))" not in tags:
            tags.add("((bald))")
            added.append("bald")
        if "clothed female nude male" not in tags:
            tags.add("clothed female nude male")
            added.append("clothed_female_nude_male")
        
        if added:
            return True, f"sleep+faceless+penetration: added {', '.join(added)}"
    
    return False, ""

def tier_4_missionary_fat_man(tags: Set[str]) -> Tuple[bool, str]:
    # NEW V12.6: Bypass pov+solo block if has sex position
    if is_self_exposure(tags) and not has_explicit_sex_position(tags):
        return False, ""
    if is_fingering_self_exposure(tags):
        return False, ""
    
    if "missionary" in tags:
        if "fat man" not in tags and "((fat man))" not in tags:
            tags.add("((fat man))")
            return True, "missionary: added ((fat man))"
    
    return False, ""
def is_fingering_self_exposure(tags_set: Set[str]) -> bool:
    """V12.7-ALPHA: Detect fingering + solo focus (self-action)"""
    has_fingering = "fingering" in tags_set
    has_solo_focus = "solo focus" in tags_set
    return has_fingering and has_solo_focus

def tier_5_bound_penetration(tags: Set[str]) -> Tuple[bool, str]:
    return False, ""

def tier_6_doggystyle_prone(tags: Set[str]) -> Tuple[bool, str]:
    if "prone bone" in tags and "on stomach" not in tags:
        tags.add("on stomach")
        return True, "prone_bone: added on_stomach"
    return False, ""

def tier_7_emotional_context(tags: Set[str]) -> Tuple[bool, str]:
    return False, ""

def tier_8_multi_partner(tags: Set[str]) -> Tuple[bool, str]:
    return False, ""

def move_wrapped_to_front(tags_list: List[str]) -> List[str]:
    wrapped = [t for t in tags_list if t.startswith("((") and t.endswith("))")]
    unwrapped = [t for t in tags_list if not (t.startswith("((") and t.endswith("))"))]
    
    order = ["((fat man))", "((bald))", "((faceless male))"]
    ordered = [t for t in order if t in wrapped]
    ordered += [t for t in wrapped if t not in order]
    
    return ordered + unwrapped

def apply_grouping(tags_list: List[str], added_arms_up: bool) -> List[str]:
    if not added_arms_up or "arms up" not in tags_list:
        return tags_list
    
    new_list = [t for t in tags_list if t not in ["1girl", "arms up"]]
    
    if "1girl" in tags_list:
        wrapped_count = sum(1 for t in new_list if t.startswith("((") and t.endswith("))"))
        new_list.insert(wrapped_count, "(1girl, arms up)")
    
    return new_list
def tier_new_male_character_grouping(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-ALPHA: Group male character tags, remove male focus"""
    
    actions = []
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 1: Remove male focus (unwanted tag)
    # ═══════════════════════════════════════════════════════════════════════════
    if "male focus" in tags:
        tags.discard("male focus")
        actions.append("removed male_focus")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 2: Collect all male character tags
    # ═══════════════════════════════════════════════════════════════════════════
    male_tags = []
    
    # Collect 1boy
    if "1boy" in tags:
        male_tags.append("1boy")
        tags.discard("1boy")
    
    # Collect faceless male (both wrapped and unwrapped)
    if "faceless male" in tags:
        male_tags.append("faceless male")
        tags.discard("faceless male")
    elif "((faceless male))" in tags:
        male_tags.append("faceless male")
        tags.discard("((faceless male))")
    
    # Collect bald
    if "bald" in tags:
        male_tags.append("bald")
        tags.discard("bald")
    elif "((bald))" in tags:
        male_tags.append("bald")
        tags.discard("((bald))")
    
    # Collect fat man
    if "fat man" in tags:
        male_tags.append("fat man")
        tags.discard("fat man")
    elif "((fat man))" in tags:
        male_tags.append("fat man")
        tags.discard("((fat man))")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 3: Group male tags if any found
    # ═══════════════════════════════════════════════════════════════════════════
    if male_tags:
        # Sort for consistent order
        order = ["1boy", "faceless male", "bald", "fat man"]
        sorted_tags = [t for t in order if t in male_tags]
        
        grouped = f"(({', '.join(sorted_tags)}))"
        tags.add(grouped)
        actions.append(f"grouped {len(male_tags)} tags")
    
    # ═════════════════════════════════════════════════════════════════════════==
    # STEP 4: Return with combined message
    # ═══════════════════════════════════════════════════════════════════════════
    if actions:
        return True, f"male_grouping: {', '.join(actions)}"
    
    return False, ""
def tier_2m_straddling_fat_man(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-NEW: Straddling (non-reverse) + penetration → fat man only"""
    
    # Block self-exposure
    if is_self_exposure(tags):
        return False, ""
    
    # Check straddling variants
    has_straddling = any(t in tags for t in {
        "straddling", "woman straddling", "astride", "straddling position",
        "upright straddle"  # non-reverse upright
    })
    
    if not has_straddling:
        return False, ""
    
    # Block if reverse positions (already handled by TIER 2g)
    has_reverse = any(t in tags for t in {
        "reverse cowgirl", "reverse cowgirl position", 
        "reverse upright straddle", "reverse riding"
    })
    
    if has_reverse:
        return False, ""  # Let TIER 2g handle reverse cases
    
    # Block conflicting positions
    conflicting_positions = {
        "doggystyle", "all fours", "all_fours", "prone bone",
        "missionary", "boy on top", "on stomach", "on back",
        "spooning", "on side", "standing sex"
    }
    
    has_conflict = has_any_tag(tags, conflicting_positions)
    if has_conflict:
        return False, ""
    
    # Require penetration + 1girl
    has_penetration = has_any_tag(tags, PENETRATION_TAGS)
    has_1girl = check_tag_exists(tags, "1girl")
    
    if not (has_penetration and has_1girl):
        return False, ""
    
    # Add fat man only (not faceless/bald - girl on top can see face)
    if not check_tag_exists(tags, "fat man"):
        tags.add("((fat man))")
        return True, "straddling: added fat_man"
    
    return False, ""
def tier_4_5_missionary_breast_sucking_cleanup(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-NEW: Missionary + breast sucking → remove breast sucking (before faceless check)"""
    
    has_missionary = "missionary" in tags
    has_breast_sucking = "breast sucking" in tags
    
    if not (has_missionary and has_breast_sucking):
        return False, ""
    
    # Block self-exposure
    if is_self_exposure(tags):
        return False, ""
    
    # Require hetero context
    has_boy = any(check_tag_exists(tags, boy_tag) for boy_tag in [
        "1boy", "2boys", "multiple boys"
    ])
    has_1girl = check_tag_exists(tags, "1girl")
    
    if not (has_boy and has_1girl):
        return False, ""
    
    # Remove breast sucking FIRST (before TIER 2N can add faceless)
    tags.discard("breast sucking")
    
    return True, "missionary_cleanup: removed breast_sucking"
def tier_2n_breast_sucking_faceless_bald(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-NEW: Breast sucking → faceless male + bald"""
    
    has_breast_sucking = "breast sucking" in tags
    
    if not has_breast_sucking:
        return False, ""  # Nếu đã bị xóa ở TIER 4.5 → không chạy
    
    # Block self-exposure
    if is_self_exposure(tags):
        return False, ""
    
    # Require hetero context
    has_boy = any(check_tag_exists(tags, boy_tag) for boy_tag in [
        "1boy", "2boys", "multiple boys"
    ])
    has_1girl = check_tag_exists(tags, "1girl")
    
    if not (has_boy and has_1girl):
        return False, ""
    
    added = []
    
    # Add faceless male
    if not check_tag_exists(tags, "faceless male"):
        tags.add("((faceless male))")
        added.append("faceless_male")
    
    # Add bald
    if "bald" not in tags and "((bald))" not in tags:
        tags.add("((bald))")
        added.append("bald")
    
    if added:
        return True, f"breast_sucking: added {', '.join(added)}"
    
    return False, ""
def tier_2p_imminent_fellatio_solo_faceless_trio(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-NEW: Imminent fellatio + solo focus → faceless + bald + fat man"""
    
    # Check imminent fellatio
    has_imminent_fellatio = "imminent fellatio" in tags
    
    # Check imminent oral indicators
    has_imminent_oral = has_any_tag(tags, IMMINENT_ORAL_TAGS)  # penis on face, looking at penis
    
    # Check oral tags (handjob counts as oral prep)
    has_oral = has_any_tag(tags, ORAL_TAGS)
    
    if not (has_imminent_fellatio or (has_imminent_oral and has_oral)):
        return False, ""
    
    # Require solo focus (POV-like scene)
    has_solo = "solo focus" in tags
    if not has_solo:
        return False, ""
    
    # Block actual self-exposure (solo + pov without boy)
    if is_self_exposure(tags):
        return False, ""
    
    # Require hetero context
    has_boy = any(check_tag_exists(tags, boy_tag) for boy_tag in [
        "1boy", "2boys", "multiple boys"
    ])
    has_1girl = check_tag_exists(tags, "1girl")
    
    if not (has_boy and has_1girl):
        return False, ""
    
    added = []
    
    # Add faceless male
    if not check_tag_exists(tags, "faceless male"):
        tags.add("((faceless male))")
        added.append("faceless_male")
    
    # Add bald
    if "bald" not in tags and "((bald))" not in tags:
        tags.add("((bald))")
        added.append("bald")
    
    # Add fat man
    if "fat man" not in tags and "((fat man))" not in tags:
        tags.add("((fat man))")
        added.append("fat_man")
    
    if added:
        return True, f"imminent_fellatio_solo: added {', '.join(added)}"
    
    return False, ""
def tier_2q_fingering_faceless_contact_fat_man(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-NEW: Fingering + faceless + contact → fat man"""
    
    has_fingering = "fingering" in tags
    has_faceless = check_tag_exists(tags, "faceless male")
    has_contact = has_any_tag(tags, CONTACT_ACTIONS)  # kiss, grabbing, etc
    
    if not (has_fingering and has_faceless and has_contact):
        return False, ""
    
    # Block self-exposure (fingering + pov + solo)
    if is_fingering_self_exposure(tags):
        return False, ""
    
    # Require hetero
    has_boy = any(check_tag_exists(tags, boy_tag) for boy_tag in ["1boy", "2boys", "multiple boys"])
    has_1girl = check_tag_exists(tags, "1girl")
    
    if not (has_boy and has_1girl):
        return False, ""
    
    # Add fat man
    if not check_tag_exists(tags, "fat man"):
        tags.add("((fat man))")
        return True, "fingering_faceless_contact: added fat_man"
    
    return False, ""
def tier_2r_lying_on_side_penetration_spooning_faceless(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-NEW: Lying + on side + penetration → auto-add spooning + faceless + bald"""
    
    # Check lying + on side (spooning indicators)
    has_lying = has_any_tag(tags, LYING_INDICATORS)
    has_on_side = "on side" in tags
    
    # Check penetration
    has_penetration = has_any_tag(tags, PENETRATION_TAGS)
    
    if not (has_lying and has_on_side and has_penetration):
        return False, ""
    
    # Skip if already has spooning tag (let TIER 2h handle it)
    if "spooning" in tags:
        return False, ""
    
    # Block self-exposure
    if is_self_exposure(tags):
        return False, ""
    
    # Require hetero context
    has_boy = any(check_tag_exists(tags, boy_tag) for boy_tag in [
        "1boy", "2boys", "multiple boys"
    ])
    has_1girl = check_tag_exists(tags, "1girl")
    
    if not (has_boy and has_1girl):
        return False, ""
    
    added = []
    
    # Add spooning tag (for consistency)
    if "spooning" not in tags:
        tags.add("spooning")
        added.append("spooning")
    
    # Add faceless male
    if not check_tag_exists(tags, "faceless male"):
        tags.add("((faceless male))")
        added.append("faceless_male")
    
    # Add bald
    if "bald" not in tags and "((bald))" not in tags:
        tags.add("((bald))")
        added.append("bald")
    
    # Note: fat man already handled by other tiers (rape, etc)
    
    if added:
        return True, f"lying_on_side_implied_spooning: added {', '.join(added)}"
    
    return False, ""
def tier_2s_aftermath_sitting_solo_fat_man(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-NEW: Aftermath + sitting + solo + 1boy + 1girl → fat man only"""
    
    # ✅ BẮT BUỘC: Chỉ 1boy + 1girl (strict hetero)
    has_1boy = check_tag_exists(tags, "1boy")
    has_1girl = check_tag_exists(tags, "1girl")
    
    if not (has_1boy and has_1girl):
        return False, ""
    
    # ✅ Block multiple boys (2boys, multiple boys)
    if any(tag in tags for tag in ["2boys", "multiple boys"]):
        return False, ""
    
    # ✅ Block multiple girls
    if any(tag in tags for tag in ["2girls", "multiple girls"]):
        return False, ""
    
    # Check aftermath indicators
    has_aftermath = "used condom" in tags or has_any_tag(tags, {
        "after sex", "after vaginal", "after oral"
    })
    
    if not has_aftermath:
        return False, ""
    
    # Check sitting + solo
    has_sitting = "sitting" in tags or "kneeling" in tags
    has_solo = "solo focus" in tags
    
    if not (has_sitting and has_solo):
        return False, ""
    
    # Block self-exposure (pov + solo)
    if is_self_exposure(tags):
        return False, ""
    
    # Block active sex (let other tiers handle)
    if has_any_tag(tags, {"vaginal", "fellatio", "oral", "handjob", "sex", 
                          "penetration", "irrumatio", "cunnilingus"}):
        return False, ""
    
    # Add ONLY fat man
    if not check_tag_exists(tags, "fat man"):
        tags.add("((fat man))")
        return True, "aftermath_sitting_solo: added fat_man"
    
    return False, ""
def tier_2o_doggystyle_sex_behind_faceless_bald(tags: Set[str]) -> Tuple[bool, str]:
    """V12.7-NEW: Doggystyle + sex from behind + penetration → faceless + bald"""
    
    # Block self-exposure
    if is_self_exposure(tags):
        return False, ""
    
    # Check doggystyle tags
    has_doggystyle = has_any_tag(tags, {
        "doggystyle", "all fours", "all_fours", "top-down bottom-up"
    })
    
    # Check sex from behind
    has_sex_behind = has_any_tag(tags, {"sex from behind", "from behind"})
    
    # Check penetration
    has_penetration = has_any_tag(tags, PENETRATION_TAGS)
    
    if not (has_doggystyle and has_sex_behind and has_penetration):
        return False, ""
    
    added = []
    
    # Add faceless male
    if not check_tag_exists(tags, "faceless male"):
        tags.add("((faceless male))")
        added.append("faceless_male")
    
    # Add bald
    if "bald" not in tags and "((bald))" not in tags:
        tags.add("((bald))")
        added.append("bald")
    
    # Note: fat man already added by TIER 2a
    
    if added:
        return True, f"doggystyle_sex_behind: added {', '.join(added)}"
    
    return False, ""

def process_tags(tags_set: Set[str]) -> Tuple[Set[str], List[str], bool]:
    tiers = [
            ("Tier 0.5", tier_0_5_colored_pubic_hair_consolidation),
            ("TIER 0", tier_0_arms_up),
            ("TIER NEW-TORN", tier_new_torn_clothes_consolidation),  # ← ADD HERE (sớm)
            ("TIER NEW-NIPPLES", tier_new_nipples_breasts_out),  # ← THÊM ĐÂY

            ("TIER 1", tier_1_faceless_wrapping),
            ("TIER 1.5", tier_1_5_clothed_female_nude_male),
            ("TIER 1.6", tier_1_6_pov_fingering_arms_behind_back),  # V12.7-ALPHA NEW
            ("TIER NEW-CLEANUP", tier_new_pov_solo_cleanup),
            ("TIER NEW-RESTRAINT", tier_new_restraint_grouping),
            ("TIER 2a", tier_2a_doggystyle_fat_man),
            ("TIER 2o", tier_2o_doggystyle_sex_behind_faceless_bald),
            ("TIER 2b", tier_2b_rape_fat_man),
            ("TIER 2c", tier_2c_all_fours_handjob_fat_man),
            ("TIER 2e", tier_2e_hetero_irrumatio_contact_fat_man),
            ("TIER 2c", tier_2c_all_fours_handjob_fat_man),
            ("TIER 2k", tier_2k_oral_pov_sitting_fat_man),           # V12.7 fix #5
            ("TIER 2s", tier_2s_aftermath_sitting_solo_fat_man),     # V12.7 NEW
            ("TIER 2P", tier_2p_imminent_fellatio_solo_faceless_trio), # ← THÊM ĐÂY
            ("TIER 2d", tier_2d_cunnilingus_faceless_bald),          # V12.7 NEW ← ADD
            ("TIER 2L", tier_2l_kissing_faceless_bald),  # ← THÊM VÀO ĐÂY
            ("TIER 2j", tier_2j_standing_holding_leg_faceless_add_fat_man),  # ← MỚI (đơn giản)
            ("TIER NEW-CLEANUP", tier_new_pov_solo_cleanup),
            ("TIER NEW-SOLO-ASSIST", tier_new_solo_assisted_exposure_cleanup),  # ← ADD
            ("TIER 2e", tier_2e_hetero_irrumatio_contact_fat_man),
            ("TIER 2f", tier_2f_holding_leg_standing_sex_behind_faceless),
            ("TIER 2g", tier_2g_reverse_cowgirl_faceless_fat_man_bald),
            ("TIER 2R", tier_2r_lying_on_side_penetration_spooning_faceless), # ← THÊM ĐÂY
            ("TIER 2M", tier_2m_straddling_fat_man),  # ← THÊM ĐÂY
            ("TIER 2h", tier_2h_spooning_faceless_fat_man_bald),
            ("TIER 2h-v2", tier_2h_v2_spooning_penetration_faceless), # ← THÊM ĐÂY

            ("TIER 2i", tier_2i_v2_standing_sex_faceless_add_fat_man),
            ("TIER 2i", tier_2i_standing_sex_behind_faceless_fat_man_bald),
            ("TIER 2", tier_2_lying_faceless_contact_fat_man),
            ("TIER 2Q", tier_2q_fingering_faceless_contact_fat_man), # ← THÊM ĐÂY
            ("TIER 3", tier_3_sleep_faceless_penetration),
            ("TIER 4", tier_4_missionary_fat_man),
            ("TIER 4.5", tier_4_5_missionary_breast_sucking_cleanup), # ← XÓA TRƯỚC
            ("TIER 5", tier_5_bound_penetration),
            ("TIER 6", tier_6_doggystyle_prone),
            ("TIER 7", tier_7_emotional_context),
            ("TIER 8", tier_8_multi_partner),
            ("TIER 2N", tier_2n_breast_sucking_faceless_bald),       # ← KIỂM TRA SAU (cuối pipeline)
            ("TIER NEW-MALE-GROUP", tier_new_male_character_grouping),  # ← ADD HERE (cuối)
    ]
    
    log = []
    added_arms_up = False
    
    for tier_name, tier_func in tiers:
        result, msg = tier_func(tags_set)
        if result:
            log.append(f"[{tier_name}] {msg}")
            if "arms_up" in msg:
                added_arms_up = True
    
    return tags_set, log, added_arms_up

def is_nsfw_tags(tags_set: Set[str]) -> bool:
    return any(any(k in t.lower() for k in NSFW_KEYWORDS) for t in tags_set)

def build_all_tags(folder: Path, remove_tags: Set[str], outpath: Path) -> None:
    lines_out = []
    
    for txt_file in sorted(folder.glob("*.txt")):
        try:
            raw_tags = split_tags(txt_file.read_text(encoding="utf-8"))
            tag_set = set(raw_tags)
            
            temp_remove = remove_tags.copy()
            
            if "fake animal ears" in tag_set:
                temp_remove -= ANIMAL_EAR_TAGS
            
            if ("1girl" in tag_set or "1boy" in tag_set) and has_any_tag(tag_set, {"oral", "fellatio"}):
                temp_remove.add("x-ray")
            
            if any("tail" in t.lower() for t in tag_set):
                if not any("cosplay" in t.lower() or "fake tail" in t.lower() for t in tag_set):
                    temp_remove |= {t for t in tag_set if "tail" in t.lower()}
            
            kept_tags = [t for t in raw_tags if t not in temp_remove]
            tag_string = ", ".join(kept_tags)
            
            if is_nsfw_tags(tag_set) and "uncensored" not in tag_string:
                tag_string += ", uncensored"
            
            lines_out.append(tag_string)
        except Exception as e:
            print(f"⚠️ Error processing {txt_file.name}: {e}")
    
    write_file(outpath, lines_out)
    print(f"✅ Built all_tags.txt: {len(lines_out)} entries")

def extract_parentheses_tags(inpath: Path, outpath: Path) -> None:
    tags = set()
    try:
        for line in inpath.read_text(encoding="utf-8").splitlines():
            for t in split_tags(line):
                if "(" in t and ")" in t:
                    tags.add(t)
    except Exception as e:
        print(f"⚠️ Error extracting parentheses: {e}")
    
    write_file(outpath, [", ".join(sorted(tags))])
    print(f"✅ Extracted parentheses: {len(tags)} unique")

def extract_unique_tags(inpath: Path, outpath: Path) -> None:
    unique = set()
    try:
        for line in inpath.read_text(encoding="utf-8").splitlines():
            for t in split_tags(line):
                unique.add(t)
    except Exception as e:
        print(f"⚠️ Error extracting unique: {e}")
    
    write_file(outpath, [", ".join(sorted(unique))])
    print(f"✅ Extracted unique: {len(unique)} total")

def enhance_tags(inpath: Path, outpath: Path) -> Dict:
    stats = defaultdict(int)
    lines_out = []
    
    print("\n" + "="*80)
    print(" TAG_ENHANCER V12.6-ENHANCED - PRODUCTION")
    print("="*80)
    
    try:
        for linenum, line in enumerate(inpath.read_text(encoding="utf-8").splitlines(), 1):
            raw_list = split_tags(line)
            tags_set = set(raw_list)
            
            final_tags, log, added_arms_up = process_tags(tags_set)
            
            added_tags = final_tags - tags_set
            if added_tags:
                stats["total_enhanced"] += 1
                if "((fat man))" in added_tags:
                    stats["added_fat_man"] += 1
                if "((faceless male))" in added_tags:
                    stats["added_faceless"] += 1
                if "((bald))" in added_tags:
                    stats["added_bald"] += 1
            
            output_tags = sorted(final_tags)
            output_tags = move_wrapped_to_front(output_tags)
            output_tags = apply_grouping(output_tags, added_arms_up)
            
            lines_out.append(", ".join(output_tags))
            stats["total_lines"] += 1
            
            if log and linenum <= 5:
                print(f"L{linenum} ✅ {' | '.join(log)}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    write_file(outpath, lines_out)
    if stats["total_lines"] > 0:
        stats["coverage_pct"] = (stats["total_enhanced"] / stats["total_lines"] * 100)
    else:
        stats["coverage_pct"] = 0
    
    print(f"\n✅ Enhancement complete")
    print(f" Lines: {stats['total_lines']}")
    print(f" Enhanced: {stats['total_enhanced']}")
    print(f" Fat man: {stats['added_fat_man']}")
    print(f" Faceless: {stats['added_faceless']}")
    print(f" Bald: {stats['added_bald']}")
    
    return dict(stats)

def test_8_patterns() -> bool:
    tests = [
        ("Test 1: Rape + Leg Grab + Vaginal", 
         {"1boy", "1girl", "rape", "lying", "leg grab", "vaginal"},
         {"((fat man))"}),
        
        ("Test 2: Lying + Faceless + Ass Grab",
         {"1boy", "1girl", "lying", "((faceless male))", "ass grab", "hetero", "vaginal"},
         {"((fat man))", "((bald))"}),
        
        ("Test 3: All Fours (NO arms_up)",
         {"1girl", "1boy", "all fours", "doggystyle", "grabbing another's breast", "vaginal"},
         {"((fat man))"}),
        
        ("Test 4: Spooning + Sex Behind",
         {"1boy", "1girl", "spooning", "sex from behind", "lying", "vaginal", "hetero"},
         {"((fat man))", "((bald))", "((faceless male))"}),
        
        ("Test 5: Standing Sex + Sex Behind",
         {"1boy", "1girl", "standing sex", "sex from behind", "hetero", "vaginal"},
         {"((fat man))", "((bald))", "((faceless male))"}),
        
        ("Test 6: Irrumatio + Fellatio (fat_man only)",
         {"1boy", "1girl", "irrumatio", "hetero", "fellatio", "oral"},
         {"((fat man))"}),
        
        ("Test 7: POV Hands + Solo Focus (blocked)",
         {"1boy", "1girl", "pov hands", "solo focus", "lying", "vaginal"},
         set()),
        
        ("Test 8: Holding Leg + Standing (faceless)",
         {"1boy", "1girl", "holding another's leg", "standing", "sex from behind", "vaginal"},
         {"((fat man))", "((bald))", "((faceless male))"}),
    ]
    
    print("\n" + "="*80)
    print(" TEST SUITE: V12.6-ENHANCED (8 PATTERNS)")
    print("="*80)
    
    passed = 0
    for name, input_tags, expected_adds in tests:
        tags = input_tags.copy()
        final_tags, _, _ = process_tags(tags)
        added = final_tags - input_tags
        
        has_all = all(tag in added for tag in expected_adds)
        has_no_extra = not any(tag in added for tag in [
            "(1girl, arms up)", "arms up"
        ] if tag not in expected_adds)
        
        passed_test = has_all and has_no_extra
        
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"\n{status} - {name}")
        
        if passed_test:
            passed += 1
        else:
            print(f"  Expected: {expected_adds}")
            print(f"  Got: {added}")
    
    print(f"\n{'='*80}")
    print(f"RESULTS: {passed}/{len(tests)} PASSED")
    print(f"{'='*80}\n")
    
    return passed == len(tests)

def main():
    print("\n" + "="*80)
    print(" TAG_ENHANCER V12.6-ENHANCED")
    print("="*80)
    print(f"Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print("📌 Step 1: Loading remove tags...")
    remove_tags = load_remove_tags(FOLDER_TO_REMOVE)
    print(f"✅ Loaded {len(remove_tags)} remove tags\n")
    
    print("📌 Step 2: Building all_tags.txt...")
    build_all_tags(FOLDER_TO_PROCESS, remove_tags, ALLTAGS_TXT)
    print()
    
    print("📌 Step 3: Extracting parentheses...")
    extract_parentheses_tags(ALLTAGS_TXT, HOP_TXT)
    print()
    
    print("📌 Step 4: Extracting unique...")
    extract_unique_tags(ALLTAGS_TXT, ALLTAG_UNIQUE_TXT)
    print()
    
    print("📌 Step 5: Enhancement...")
    stats = enhance_tags(ALLTAGS_TXT, ADDFACELESS_TXT)
    
    print(f"\n✅ End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
    test_8_patterns()
    
    print("\n" + "="*80)
    print(" VERSION V12.6-ENHANCED - FULL IMPLEMENTATION")
    print("="*80)
    print("✅ FEATURES:")
    print("  ✅ 19 TIER system (0, 1, 1.5, 2a-i, 3-8)")
    print("  ✅ 20+ CONTACT_ACTIONS tags")
    print("  ✅ All_fours protection (no arms_up)")
    print("  ✅ Penetration requirements enforced")
    print("  ✅ Spooning + standing sex detection")
    print("  ✅ Irrumatio handling (fat_man only)")
    print("  ✅ Tag wrapping & ordering")
    print("  ✅ Statistics & coverage tracking")
    print("  ✅ 8-pattern test suite")
    print("  ✅ Full file I/O pipeline")
    print("="*80 + "\n")
