param(
    [string]$SourceDir = "D:\no\wantremove",
    [string]$OutputDir = "D:\no\wantremove\_organized_tags"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $SourceDir -PathType Container)) {
    throw "Source directory not found: $SourceDir"
}

if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$categoryOrder = @(
    "01_character_names",
    "02_character_count_and_groups",
    "03_hair_styles_and_hair_accessories",
    "04_eyes_and_face",
    "05_headwear",
    "06_jewelry",
    "07_eyewear",
    "08_clothing_and_outfits",
    "09_legwear_and_footwear",
    "10_body_traits_and_anatomy",
    "11_animal_features",
    "12_horns_halo_wings_tails",
    "13_censor_text_watermark",
    "14_objects_and_props",
    "15_background_and_places",
    "16_colors_patterns_materials",
    "17_pose_action_state",
    "99_uncategorized",
    "_needs_review"
)

$groups = @{}
foreach ($category in $categoryOrder) {
    $groups[$category] = New-Object "System.Collections.Generic.HashSet[string]"
}

$sourceByTag = @{}
$originalByNormalized = @{}
$skippedEmpty = 0

function Normalize-Tag {
    param([string]$Tag)

    $value = $Tag.Normalize([Text.NormalizationForm]::FormKC)
    $value = $value -replace "[\u200B-\u200D\uFEFF]", ""
    $value = $value -replace "[\\]+\(", "("
    $value = $value -replace "[\\]+\)", ")"
    $value = $value.Trim([char]34)
    $value = $value -replace "[\u2018\u2019\u201B]", "'"
    $value = $value -replace "\s+", " "
    $value = $value.Trim()
    $value = $value.ToLowerInvariant()
    return $value
}

function Split-Tags {
    param([string]$Content)

    $clean = $Content -replace "`r?`n", " "
    return $clean -split "," | ForEach-Object { $_.Trim() }
}

function Get-SourceHint {
    param([string]$FileName)

    $name = [IO.Path]::GetFileNameWithoutExtension($FileName).ToLowerInvariant()

    if ($name -match "^(name|name2|name_|tags_kushina)") { return "characters" }
    if ($name -match "headwear|halo|horns|tails|wings|tai|mask") { return "head_features" }
    if ($name -match "trangsuc") { return "jewelry" }
    if ($name -match "eyeswear") { return "eyewear" }
    if ($name -match "hair|toc|dotrentoc|trang_tri_toc") { return "hair" }
    if ($name -match "mau_mat|eyes") { return "eyes_face" }
    if ($name -match "quanao|trangphuc|kimono|clothes") { return "clothing" }
    if ($name -match "abs|chest|navel|ron_navel|skin") { return "body" }
    if ($name -match "cencord|censor|kiemduyet|watermark|text|othoai") { return "censor_text" }
    if ($name -match "multigirls|multi|mono") { return "count" }
    if ($name -match "color") { return "colors" }

    return ""
}

function Has-AnySourceHint {
    param([string]$Tag, [string]$Hint)

    if (-not $sourceByTag.ContainsKey($Tag)) { return $false }
    foreach ($source in $sourceByTag[$Tag]) {
        if ($source.EndsWith("|$Hint")) { return $true }
    }
    return $false
}

function Is-CharacterTag {
    param([string]$Tag)

    $franchisePattern = "\(.*(fate|genshin impact|azur lane|kancolle|pokemon|blue archive|arknights|touhou|umamusume|hololive|nijisanji|fire emblem|granblue fantasy|honkai|girls' frontline|girls und panzer|league of legends|overwatch|re:zero|vocaloid|idolmaster|project moon|kemono friends|neptunia|splatoon|street fighter|chainsaw man|naruto|one piece|dragon ball|sao|xenoblade|persona|danganronpa|madoka|princess connect|konosuba|maidragon|touken ranbu|hetalia|animal crossing|cyberpunk|ff[0-9]+|dq[0-9]+|jojo|undertale|omori|frozen|housamo|reverse:1999|oshi no ko).*\)"
    $nonCharacterWords = "\b(uniform|outfit|clothes|clothing|dress|shirt|skirt|pants|shorts|boots|gloves|hat|helmet|hair|eyes|wings|horns|tail|object|place|background|text|censor|watermark|print|symbol|mask|swimsuit|bikini|bra|panties|socks|thighhighs|footwear|weapon|sword|bag|collar|bow|ribbon|halo|earrings|necklace|bracelet)\b"

    if ($Tag -match $franchisePattern -and $Tag -notmatch $nonCharacterWords) { return $true }
    if (Has-AnySourceHint $Tag "characters" -and $Tag -notmatch "^(dark aura|character name|artist name|mother and|ninja|mecha musume|monster hunter \(character\)|digimon \(creature\)|pikmin \(creature\))$") { return $true }
    return $false
}

function Get-Category {
    param([string]$Tag)

    if ($Tag.Length -eq 0) { return "" }
    if ($Tag.Length -gt 120 -or $Tag -match "note:|^\d+$|^\d{4,}$|^từ file|angsty\*\*|corrected to") { return "_needs_review" }

    if ($Tag -match "^\d+(girls|boys)$|^multi(girls|boys)$|^multiple (girls|boys)|^solo$|^1girl$|^1boy$|^mother and (daughter|son)$") { return "02_character_count_and_groups" }
    if (Is-CharacterTag $Tag) { return "01_character_names" }

    if ($Tag -match "censor|watermark|patreon logo|logo censor|artist name|character name|english text|chinese text|engrish text|dialogue box|speech bubble|spoken object|can't show this") { return "13_censor_text_watermark" }
    if ($Tag -match "wrestling ring|basketball|volleyball|knife|handbag|lamp|lamppost|command spell|cross$|button|buttons|drawstring|zipper pull tab") { return "14_objects_and_props" }
    if ($Tag -match "o-ring bikini|o ring bikini|o-ring thigh strap|two-sided fabric|microdress|miniskirt|bodystocking|bodice|bridal gauntlets|ankle cuffs|chaps|dirndl|fishnets|harness|hood$|hood down|maid$|obi(age|jime)?$|off shoulder|open fly|pantylines|pasties|sash$|sleeveless turtleneck|square neckline|suspenders|traditional bowtie|underwear|v-neck") { return "08_clothing_and_outfits" }
    if ($Tag -match "single hair ring") { return "03_hair_styles_and_hair_accessories" }
    if ($Tag -match "\b(eyewear|glasses|sunglasses|goggles|eyepatch|eye mask|scouter|mask|blindfold|shutter shades)\b") { return "07_eyewear" }
    if ($Tag -match "\b(earrings?|necklace|bracelet|bangle|anklet|armlet|ring|wedding ring|toe ring|brooch|choker|jewel|gem|gemstone|piercing|pendant|watch|wristwatch|wristband)\b") { return "06_jewelry" }
    if ($Tag -match "\b(hat|cap|helmet|headwear|headdress|crown|tiara|diadem|circlet|veil|hijab|headscarf|headband|hairband|forehead protector|balaclava|bandana|beanie|beret|bonnet|fedora|ushanka|sombrero|turban|hachimaki|mongkhon|wimple|coif|fascinator|object on head|on head|no headwear|chin strap|headlamp|mortarboard|mitre|songkok|tenugui|tokin|tsunokakushi)\b") { return "05_headwear" }
    if ($Tag -match "\b(hair|bangs|braid|twintails|ponytail|sidelocks|ahoge|bun|drills|bob cut|hime cut|mullet|pixie cut|bowl cut|chignon|dreadlocks|cornrows|antenna hair|scrunchie|hairclip|hair ornament|hair ribbon|hair bow|hair tie)\b") { return "03_hair_styles_and_hair_accessories" }
    if ($Tag -match "\b(eyes?|pupils?|sclera|eyelashes|eyebrows|face|fangs?|teeth|freckles|beard|mustache|facial hair|forehead|lips|eyeshadow|aegyo sal|bags under eyes|skin fang|slit pupils|third eye)\b") { return "04_eyes_and_face" }
    if ($Tag -match "\b(cat|dog|fox|wolf|bear|rabbit|bunny|deer|cow|sheep|tiger|bat|bird|frog|horse|kemomimi|animal ear fluff|animal print|fake animal ears|animal ears?|extra ears|fake ears)\b") { return "11_animal_features" }
    if ($Tag -match "\b(ears?|tail|wings?|halo|horns?|antlers|cat girl|dog girl|fox girl|demon girl|elf|draph|erune|viera|au ra)\b") { return "12_horns_halo_wings_tails" }
    if ($Tag -match "\b(boots?|shoes?|socks?|thighhighs?|kneehighs?|pantyhose|stockings?|legwear|footwear|heels?|sneakers|slippers|uwabaki|tabi|toeless|stirrup|garter|zettai ryouiki|bare legs|barefoot)\b") { return "09_legwear_and_footwear" }
    if ($Tag -match "\b(apron|armor|bikini|bodysuit|bra|buruma|cape|capelet|cardigan|cheerleader|china dress|cloak|clothes|clothing|coat|collar|corset|costume|dress|fashion|gloves?|goth|hakama|hoodie|jacket|kimono|kogal|latex|leotard|maid|neck(erchief|tie)|obi|obiage|obijime|office lady|outfit|panties|pants|pasties|robe|sailor collar|sarashi|scarf|serafuku|shirt|shorts|skirt|sleeves?|suit|sweater|swimsuit|t-shirt|tank top|thong|top|uniform|vest|yukata)\b") { return "08_clothing_and_outfits" }
    if ($Tag -match "\b(abs|anatomy|back muscles|bare shoulders?|biceps|bodybuilder|breasts?|chest|cleavage|dark skin|defloration|fingernails|flat chest|gyaru|lipstick|makeup|mascara|mole|muscles?|nail polish|navel|petite|skin|stomach|tan|tanlines|thighs?|toenails|toned|underbust|v-taper|waist|wet clothes|small breasts|underboob)\b") { return "10_body_traits_and_anatomy" }
    if ($Tag -match "\b(background|alley|architecture|bathroom|bathtub|bed(room)?|building|campfire|chalkboard|city|cityscape|classroom|couch|curtains|desk|door|doorway|floor|forest|full moon|grass|indoors|kitchen|moon|nature|office|outdoors|park|place|prison|road|room|scenery|school|shop|shower|sky|skyline|skyscraper|snow|snowing|street|sun(set|rise|light)?|table|tatami|tile|tiles|toilet|town|tree|village|wall|water|window|wooden floor)\b") { return "15_background_and_places" }
    if ($Tag -match "\b(bag|backpack|badge|ball|bandage|bandaid|basketball|bed sheet|beer mug|bell|belt|blanket|book|buckle|button|cage|candle|card|cellphone|chain|chopsticks|coin|collar|comb|condom|cup|dice|dildo|egg vibrator|feather|flower|food|gag|mug|phone|sword|weapon|toy|umbrella|vibrator)\b") { return "14_objects_and_props" }
    if ($Tag -match "\b(aqua|black|blonde|blue|brown|colored|dark|green|grey|gray|orange|pink|purple|red|silver|white|yellow|striped|checkered|pinstripe pattern|print|frilled|floral|transparent|translucent|see-through|metal|leather|denim|lace|ribbon|bow|rose|flower|spot color)\b") { return "16_colors_patterns_materials" }
    if ($Tag -match "\b(adjusting|aside|biting|broken|carrying|clothed|covered|crossed|dirty|downblouse|dutch angle|flapping|folded|hand on|hands on|holding|in mouth|loss|on chest|over eyes|peek|pinned back|profile|putting on|removing|ripped|slip|split|torn|tucked in|unbuttoned|undone|unworn|unzipped|upskirt|wet)\b") { return "17_pose_action_state" }

    $hintCategory = ""
    if (Has-AnySourceHint $Tag "jewelry") { $hintCategory = "06_jewelry" }
    elseif (Has-AnySourceHint $Tag "eyewear") { $hintCategory = "07_eyewear" }
    elseif (Has-AnySourceHint $Tag "hair") { $hintCategory = "03_hair_styles_and_hair_accessories" }
    elseif (Has-AnySourceHint $Tag "eyes_face") { $hintCategory = "04_eyes_and_face" }
    elseif (Has-AnySourceHint $Tag "head_features") { $hintCategory = "12_horns_halo_wings_tails" }
    elseif (Has-AnySourceHint $Tag "clothing") { $hintCategory = "08_clothing_and_outfits" }
    elseif (Has-AnySourceHint $Tag "body") { $hintCategory = "10_body_traits_and_anatomy" }
    elseif (Has-AnySourceHint $Tag "censor_text") { $hintCategory = "13_censor_text_watermark" }
    elseif (Has-AnySourceHint $Tag "count") { $hintCategory = "02_character_count_and_groups" }
    elseif (Has-AnySourceHint $Tag "colors") { $hintCategory = "16_colors_patterns_materials" }

    if ($hintCategory.Length -gt 0) { return $hintCategory }
    return "99_uncategorized"
}

$files = Get-ChildItem -LiteralPath $SourceDir -File -Filter "*.txt" |
    Where-Object { $_.FullName -notlike "$OutputDir*" }

foreach ($file in $files) {
    $hint = Get-SourceHint $file.Name
    $content = [IO.File]::ReadAllText($file.FullName)
    foreach ($rawTag in (Split-Tags $content)) {
        $tag = Normalize-Tag $rawTag
        if ($tag.Length -eq 0) {
            $skippedEmpty++
            continue
        }

        if (-not $originalByNormalized.ContainsKey($tag)) {
            $originalByNormalized[$tag] = $rawTag.Trim()
        }
        if (-not $sourceByTag.ContainsKey($tag)) {
            $sourceByTag[$tag] = New-Object "System.Collections.Generic.HashSet[string]"
        }
        [void]$sourceByTag[$tag].Add("$($file.Name)|$hint")
    }
}

foreach ($tag in $sourceByTag.Keys) {
    $category = Get-Category $tag
    if ($category.Length -gt 0) {
        [void]$groups[$category].Add($tag)
    }
}

$allTags = New-Object "System.Collections.Generic.HashSet[string]"
foreach ($category in $categoryOrder) {
    foreach ($tag in $groups[$category]) {
        [void]$allTags.Add($tag)
    }
}

foreach ($category in $categoryOrder) {
    $path = Join-Path $OutputDir "$category.txt"
    $sorted = $groups[$category] | Sort-Object
    [IO.File]::WriteAllText($path, ($sorted -join ", "), [Text.Encoding]::UTF8)
}

[IO.File]::WriteAllText(
    (Join-Path $OutputDir "all_tags_normalized.txt"),
    (($allTags | Sort-Object) -join ", "),
    [Text.Encoding]::UTF8
)

$summaryLines = New-Object "System.Collections.Generic.List[string]"
$summaryLines.Add("# Organized tag summary")
$summaryLines.Add("")
$summaryLines.Add("Source: $SourceDir")
$summaryLines.Add("Output: $OutputDir")
$summaryLines.Add("Input files: $($files.Count)")
$summaryLines.Add("Unique normalized tags: $($allTags.Count)")
$summaryLines.Add("Skipped empty fragments: $skippedEmpty")
$summaryLines.Add("")
$summaryLines.Add("| Group | Count |")
$summaryLines.Add("|---|---:|")
foreach ($category in $categoryOrder) {
    $summaryLines.Add("| $category | $($groups[$category].Count) |")
}
$summaryLines.Add("")
$summaryLines.Add("Notes:")
$summaryLines.Add("- Original files were not modified.")
$summaryLines.Add("- Parentheses escaped as \`\(name\`\) were normalized to `(name)`.")
$summaryLines.Add("- `_needs_review.txt` contains numeric fragments, long accidental notes, and tags that looked malformed.")

[IO.File]::WriteAllText(
    (Join-Path $OutputDir "README.md"),
    ($summaryLines -join [Environment]::NewLine),
    [Text.Encoding]::UTF8
)

Write-Host "Organized tags written to: $OutputDir"
Write-Host "Unique normalized tags: $($allTags.Count)"
foreach ($category in $categoryOrder) {
    Write-Host ("{0}: {1}" -f $category, $groups[$category].Count)
}
