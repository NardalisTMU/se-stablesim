import streamlit as st
import random
from collections import defaultdict

# =========================
# GLOBAL STORAGE
# =========================

if "BANNERS" not in st.session_state:
    st.session_state.BANNERS = {}
if "ARCHIVED_BANNERS" not in st.session_state:
    st.session_state.ARCHIVED_BANNERS = set()
if "ALIASES" not in st.session_state:
    st.session_state.ALIASES = {}

# Pity counters
if "GLOBAL_LEG_PITY" not in st.session_state:
    st.session_state.GLOBAL_LEG_PITY = 0
if "WINGED_PEGASUS_PITY" not in st.session_state:
    st.session_state.WINGED_PEGASUS_PITY = 0
if "TACK_EPIC_PITY" not in st.session_state:
    st.session_state.TACK_EPIC_PITY = 0
if "TACK_LEG_PITY" not in st.session_state:
    st.session_state.TACK_LEG_PITY = 0
if "VALENTINE_LEG_PITY" not in st.session_state:
    st.session_state.VALENTINE_LEG_PITY = 0

# Pity persistence
if "PERSIST_PITY" not in st.session_state:
    st.session_state.PERSIST_PITY = True

# Stats
if "TOTAL_PULLS" not in st.session_state:
    st.session_state.TOTAL_PULLS = 0
if "CUMULATIVE_COUNTS" not in st.session_state:
    st.session_state.CUMULATIVE_COUNTS = defaultdict(int)
if "RARITY_COUNTS" not in st.session_state:
    st.session_state.RARITY_COUNTS = defaultdict(int)

# =========================
# UTILITY FUNCTIONS
# =========================

def normalize(text):
    return text.lower().replace(" ", "").replace("_", "")

def register_banner(name, items, aliases=None, archived=False):
    st.session_state.BANNERS[name] = items
    if archived:
        st.session_state.ARCHIVED_BANNERS.add(name)
    if aliases:
        for a in aliases:
            st.session_state.ALIASES[normalize(a)] = name
    st.session_state.ALIASES[normalize(name)] = name

def resolve_banner(input_name):
    return st.session_state.ALIASES.get(normalize(input_name))

def weighted_choice(items):
    if not items:
        raise ValueError("weighted_choice received empty item list")

    total = sum(w for _, _, w in items)
    r = random.uniform(0, total)
    upto = 0
    for name, rarity, weight in items:
        if upto + weight >= r:
            return name, rarity
        upto += weight

    return items[-1][0], items[-1][1]

# =========================
# PULL LOGIC
# =========================

def pull_once(banner):
    items = st.session_state.BANNERS[banner]
    pity_used = False
    pull_info = {}

    # ---------- TACK BANNER ----------
    if banner == "Tack Banner":
        st.session_state.TACK_EPIC_PITY += 1
        st.session_state.TACK_LEG_PITY += 1

        legendary_items = [i for i in items if i[1] == "Legendary"]
        epic_items = [i for i in items if i[1] == "Epic"]

        if st.session_state.TACK_LEG_PITY >= 90:
            name, rarity = weighted_choice(legendary_items)
            st.session_state.TACK_LEG_PITY = 0
            pity_used = True
            active_pool = legendary_items
        elif st.session_state.TACK_EPIC_PITY >= 10:
            name, rarity = weighted_choice(epic_items)
            st.session_state.TACK_EPIC_PITY = 0
            pity_used = True
            active_pool = epic_items
        else:
            name, rarity = weighted_choice(items)
            if rarity == "Legendary":
                st.session_state.TACK_LEG_PITY = 0
            if rarity == "Epic":
                st.session_state.TACK_EPIC_PITY = 0
            active_pool = items

        total_weight = sum(w for _, _, w in active_pool)
        for n, r, w in active_pool:
            if n == name:
                pull_info[f"{n} Chance"] = round(w / total_weight * 100, 2)

        pull_info["Tack Epic Pity"] = st.session_state.TACK_EPIC_PITY
        pull_info["Tack Legendary Pity"] = st.session_state.TACK_LEG_PITY
        return name, rarity, pity_used, pull_info

    # ---------- VALENTINE BANNER ----------
    if banner == "Valentine Stable":
        FEATURED_NAME = "Lovestruck Unicorn"

        st.session_state.VALENTINE_LEG_PITY += 1

        featured_item = next((i for i in items if i[0] == FEATURED_NAME), None)

        if not featured_item:
            name, rarity = weighted_choice(items)
            return name, rarity, False, {}

        if st.session_state.VALENTINE_LEG_PITY >= 25:
            name, rarity, _ = featured_item
            st.session_state.VALENTINE_LEG_PITY = 0
            pity_used = True
            active_pool = [featured_item]
        else:
            name, rarity = weighted_choice(items)
            if name == FEATURED_NAME:
                st.session_state.VALENTINE_LEG_PITY = 0
            active_pool = [i for i in items if i[1] == rarity]

        total_banner_weight = sum(w for _, _, w in items)
        category_weight = sum(w for _, _, w in active_pool)
        category_prob = category_weight / total_banner_weight

        for n, r, w in active_pool:
            if n == name:
                pull_info[f"{n} Chance"] = round(w / category_weight * category_prob * 100, 2)

        pull_info["Valentine Pity Counter"] = st.session_state.VALENTINE_LEG_PITY
        return name, rarity, pity_used, pull_info

    # ---------- WINGED STABLE ----------
    if banner == "Winged Stable":
        st.session_state.WINGED_PEGASUS_PITY += 1

        legendary_items = [i for i in items if i[1] == "Flying"]

        if st.session_state.WINGED_PEGASUS_PITY >= 10:
            name, rarity = weighted_choice(legendary_items)
            st.session_state.WINGED_PEGASUS_PITY = 0
            pity_used = True
            active_pool = legendary_items
        else:
            name, rarity = weighted_choice(items)
            if rarity == "Flying":
                st.session_state.WINGED_PEGASUS_PITY = 0
            active_pool = [i for i in items if i[1] == rarity]

        total_weight = sum(w for _, _, w in active_pool)
        for n, r, w in active_pool:
            if n == name:
                pull_info[f"{n} Chance"] = round(w / total_weight * 100, 2)

        pull_info["Winged Pity Counter"] = st.session_state.WINGED_PEGASUS_PITY
        return name, rarity, pity_used, pull_info

    # ---------- MAJESTIC & MYSTICAL ----------
    if banner in ("Majestic Stable", "Mystical Stable"):
        st.session_state.GLOBAL_LEG_PITY += 1
        legendary_items = [i for i in items if "Legendary" in i[1] or "Fantasy" in i[1]]

        if st.session_state.GLOBAL_LEG_PITY >= 10:
            name, rarity = weighted_choice(legendary_items)
            st.session_state.GLOBAL_LEG_PITY = 0
            pity_used = True
            active_pool = legendary_items
        else:
            name, rarity = weighted_choice(items)
            if "Legendary" in rarity or "Fantasy" in rarity:
                st.session_state.GLOBAL_LEG_PITY = 0
            active_pool = [i for i in items if i[1] == rarity]

        total_weight = sum(w for _, _, w in active_pool)
        for n, r, w in active_pool:
            if n == name:
                pull_info[f"{n} Chance"] = round(w / total_weight * 100, 2)

        pull_info["Horse Pity Counter"] = st.session_state.GLOBAL_LEG_PITY
        return name, rarity, pity_used, pull_info

    # ---------- OTHER BANNERS ----------
    name, rarity = weighted_choice(items)
    total_weight = sum(w for _, _, w in items)
    for n, r, w in items:
        if n == name:
            pull_info[f"{n} Chance"] = round(w / total_weight * 100, 2)
    return name, rarity, False, pull_info

# =========================
# MULTI PULL
# =========================

def multi_pull(banner, amount, highlights=None, advanced=False):
    highlights = highlights or []
    results = []

    # Reset pity if OFF
    if not st.session_state.PERSIST_PITY:
        st.session_state.GLOBAL_LEG_PITY = 0
        st.session_state.WINGED_PEGASUS_PITY = 0
        st.session_state.TACK_EPIC_PITY = 0
        st.session_state.TACK_LEG_PITY = 0
        st.session_state.VALENTINE_LEG_PITY = 0

    for i in range(1, amount + 1):
        name, rarity, pity_used, pull_info = pull_once(banner)
        st.session_state.TOTAL_PULLS += 1

        # --- SAFELY increment counts ---
        if name not in st.session_state.CUMULATIVE_COUNTS:
            st.session_state.CUMULATIVE_COUNTS[name] = 0
        st.session_state.CUMULATIVE_COUNTS[name] += 1

        if rarity not in st.session_state.RARITY_COUNTS:
            st.session_state.RARITY_COUNTS[rarity] = 0
        st.session_state.RARITY_COUNTS[rarity] += 1

        highlight_flag = any(h.lower() in name.lower() for h in highlights)
        highlight_mark = "PITY" if pity_used else ""
        if highlight_flag:
            highlight_mark += "*" if highlight_mark else "*"

        chance = pull_info.get(f"{name} Chance", "N/A")
        cumulative_count = st.session_state.CUMULATIVE_COUNTS[name]

        if advanced:
            results.append([i, name, rarity, chance, cumulative_count, highlight_mark])
        else:
            results.append([i, name, rarity, highlight_mark])

    return results

# =========================
# DISPLAY FUNCTIONS
# =========================

def show_table(results):
    st.table(results)

def show_summary():
    rows = [[r, c] for r, c in sorted(st.session_state.RARITY_COUNTS.items())]
    st.write("### Pull Summary")
    st.table(rows)

def show_cumulative():
    rows = [[item, count] for item, count in sorted(st.session_state.CUMULATIVE_COUNTS.items(), key=lambda x: -x[1])]
    st.write("### Cumulative Items")
    st.table(rows)

def best_banner():
    scores = {}
    for banner, items in st.session_state.BANNERS.items():
        score = 0
        for _, rarity, weight in items:
            if "Legendary" in rarity:
                score += weight * 5
            elif "Epic" in rarity:
                score += weight * 3
            else:
                score += weight
        scores[banner] = round(score, 3)
    rows = [[b, s] for b, s in sorted(scores.items(), key=lambda x: -x[1])]
    st.write("### Banner Strength (rough)")
    st.table(rows)

# =========================
# PART 2 — Creatures of the Night (ARCHIVED)
# =========================

cotn_items = [

    # ---- FEATURED FANTASY ----
    ("Lycan Diremane", "Fantasy", 2.50),
    ("Transylvanian Nightstalker", "Fantasy", 2.50),
    ("Haunted Arabian", "Fantasy", 0.83),
    ("Skeleton Puppy", "Fantasy", 0.83),

    # ---- FANTASY ----
    ("Aesir Friesian", "Fantasy", 0.83),
    ("Legendary Clydesdale", "Fantasy", 0.83),
    ("Aratiri Clydesdale", "Fantasy", 0.83),
    ("Sahar Arabian", "Fantasy", 0.83),
    ("Maelstrom Clydesdale", "Fantasy", 0.83),
    ("Night Glow", "Fantasy", 0.83),
    ("Glacier Storm", "Fantasy", 0.83),
    ("Atlantean Arabian", "Fantasy", 0.83),
    ("Cosmic Mustang", "Fantasy", 0.83),
    ("Wildfin Triton", "Fantasy", 0.83),

    # ---- LEGENDARY ----
    ("Black Shire", "Legendary", 0.62),
    ("Rose Grey Clydesdale", "Legendary", 0.62),
    ("Red Roan Clydesdale", "Legendary", 0.62),
    ("Black Overo Shire", "Legendary", 0.62),
    ("Strawberry Roan Clydesdale", "Legendary", 0.62),
    ("Blue Roan Shire", "Legendary", 0.62),
    ("Gray Tobiano Shire", "Legendary", 0.62),
    ("White Shire", "Legendary", 0.62),
    ("Sorrel Rabicano Clydesdale", "Legendary", 0.62),

    ("Blood Bay Friesian Sport", "Legendary", 0.62),
    ("Grey Friesian Sport", "Legendary", 0.62),
    ("Palomino Friesian Sport", "Legendary", 0.62),
    ("Leopard Cross Friesian Sport", "Legendary", 0.62),
    ("Brown Pintaloosa Friesian Sport", "Legendary", 0.62),
    ("Grey Pintaloosa Friesian Sport", "Legendary", 0.62),
    ("Red Roan Friesian Sport", "Legendary", 0.62),
    ("Brown Tobiano Friesian Sport", "Legendary", 0.62),
    ("Sorrel Tobiano Friesian Sport", "Legendary", 0.62),
    ("Grey Tobiano Friesian Sport", "Legendary", 0.62),
    ("Piebald Friesian Sport", "Legendary", 0.62),

    ("White Hair Friesian", "Legendary", 0.62),
    ("Braided Friesian", "Legendary", 0.62),
    ("Blue Roan Friesian Sport", "Legendary", 0.62),
    ("Appaloosa Friesian", "Legendary", 0.62),
    ("Dapple Overo Brown Friesian", "Legendary", 0.62),
    ("Speckled Overo Friesian", "Legendary", 0.62),
    ("Peacock Snowcap Friesian", "Legendary", 0.62),
    ("Tobiano Friesian", "Legendary", 0.62),

    ("Appaloosa Clydesdale", "Legendary", 0.62),
    ("Appaloosa Shire", "Legendary", 0.62),
    ("Dapple Grey Clydesdale", "Legendary", 0.62),
    ("Seal Bay Clydesdale", "Legendary", 0.62),

    # ---- EPIC ----
    ("Black Snowflake Arabian", "Epic", 0.62),
    ("Light Bay Arabian", "Epic", 0.88),
    ("Buckskin Arabian", "Epic", 0.88),
    ("Silver Dapple Arabian", "Epic", 0.88),
    ("Rose Grey Arabian", "Epic", 0.88),
    ("Silver Splashed Pintabian", "Epic", 0.88),
    ("Black Arabian", "Epic", 0.88),
    ("Light Brown Pintabian", "Epic", 0.88),
    ("Grey Tovero Pintabian", "Epic", 0.88),
    ("Red Dun Arabian", "Epic", 0.88),
    ("Liver Chestnut Pintabian", "Epic", 0.88),

    ("Bay Dun Kiger", "Epic", 0.88),
    ("Black Mustang", "Epic", 0.88),
    ("Grey Rabicano Mustang", "Epic", 0.88),
    ("Smokey Cream Mustang", "Epic", 0.88),
    ("Dapple Grey Mustang", "Epic", 0.88),
    ("Dark Bay Roan Mustang", "Epic", 0.88),
    ("White Mustang", "Epic", 0.88),
    ("Grulla Dapple Mustang", "Epic", 0.88),
    ("Grulla Dun Kiger", "Epic", 0.88),
    ("Blood Bay Kiger", "Epic", 0.88),
    ("Bay Mustang", "Epic", 0.88),
    ("Chestnut Skewbald Mustang", "Epic", 0.88),
    ("Silver Dapple Kiger", "Epic", 0.88),
    ("Grey Tobiano Kiger", "Epic", 0.88),

    ("Black Splashed Paint", "Epic", 0.88),
    ("Black Snowflake Quarter", "Epic", 0.88),
    ("Gray Overo Paint", "Epic", 0.88),
    ("Seal Bay Aussie", "Epic", 0.88),
    ("Buckskin Quarter", "Epic", 0.88),
    ("Dapple Bay Aussie", "Epic", 0.88),
    ("Cremello Aussie", "Epic", 0.88),
    ("Dapple Gray Quarter", "Epic", 0.88),
    ("Spotted Grey Quarter", "Epic", 0.88),
    ("Dark Seal Quarter", "Epic", 0.88),
    ("Dark Bay Aussie", "Epic", 0.88),
    ("Dark Brown Heart Quarter", "Epic", 0.88),
    ("Grey Splashed Quarter", "Epic", 0.88),
    ("Silver Ripple Aussie", "Epic", 0.88),
    ("Silver Dapple Quarter", "Epic", 0.88),
    ("White Quarter", "Epic", 0.88),
    ("Black Sabino Paint", "Epic", 0.88),
    ("Smokey Black Quarter", "Epic", 0.88),
    ("Chestnut Tobiano Paint", "Epic", 0.88),
    ("Grey Chimera Aussie", "Epic", 0.88),
    ("Champagne Spattered Quarter", "Epic", 0.88),
    ("Tobiano Grey Aussie", "Epic", 0.88),
    ("Palomino Quarter", "Epic", 0.88),
    ("Red Dun Aussie", "Epic", 0.88),
    ("Perlino Aussie", "Epic", 0.88),
    ("Rose Grey Quarter", "Epic", 0.88),
    ("Smokey Seal Quarter", "Epic", 0.88),

    ("Liver Splatter Paint", "Epic", 0.88),
    ("Liver Tobiano Paint", "Epic", 0.88),

    ("Grease Spot Pintabian", "Epic", 0.88),
    ("Grey Tobiano Pintabian", "Epic", 0.88),
    ("Appaloosa Pintabian", "Epic", 0.88),

    ("Dapple Seal Arabian", "Epic", 0.88),
    ("Dapple Overo Brown Arabian", "Epic", 0.88),
    ("Steel Grey Arabian", "Epic", 0.88),
    ("Dapple Brown Arabian", "Epic", 0.88),
    ("Overo Palomino Arabian", "Epic", 0.88),
    ("Overo Brown Arabian", "Epic", 0.88),
    ("Dapple Overo Grey Arabian", "Epic", 0.88),

    ("Appaloosa American Quarter", "Epic", 0.88),
    ("Drenched Appaloosa Quarter", "Epic", 0.88),
    ("Champagne Dapple Aussie", "Epic", 0.88),
    ("Tobiano Buckskin Paint", "Epic", 0.88),
    ("Perlino Dun Paint", "Epic", 0.88),
    ("Chestnut Faded Paint", "Epic", 0.88),
    ("Splashed Black Paint", "Epic", 0.88),
    ("Cream Tricolor Quarter", "Epic", 0.88),
    ("Grey Tricolor Paint", "Epic", 0.88),
]

register_banner(
    "Creatures of the Night",
    cotn_items,
    aliases=["cotn", "night", "creatures"],
    archived=True
)

# =========================
# PART 3 — Mystical Stable
# =========================

mystical_items = [

    # ---- FANTASY (10%) ----
    ("Aesir Friesian", "Fantasy", 1.00),
    ("Legendary Clydesdale", "Fantasy", 1.00),
    ("Aratiri Clydesdale", "Fantasy", 1.00),
    ("Sahar Arabian", "Fantasy", 1.00),
    ("Maelstrom Clydesdale", "Fantasy", 1.00),
    ("Night Glow", "Fantasy", 1.00),
    ("Glacier Storm", "Fantasy", 1.00),
    ("Atlantean Arabian", "Fantasy", 1.00),
    ("Cosmic Mustang", "Fantasy", 1.00),
    ("Wildfin Triton", "Fantasy", 1.00),

    # ---- LEGENDARY (20%) ----
    ("Black Shire", "Legendary", 0.62),
    ("Rose Grey Clydesdale", "Legendary", 0.62),
    ("Red Roan Clydesdale", "Legendary", 0.62),
    ("Black Overo Shire", "Legendary", 0.62),
    ("Strawberry Roan Clydesdale", "Legendary", 0.62),
    ("Blue Roan Shire", "Legendary", 0.62),
    ("Gray Tobiano Shire", "Legendary", 0.62),
    ("White Shire", "Legendary", 0.62),
    ("Sorrel Rabicano Clydesdale", "Legendary", 0.62),

    ("Blood Bay Friesian Sport", "Legendary", 0.62),
    ("Grey Friesian Sport", "Legendary", 0.62),
    ("Palomino Friesian Sport", "Legendary", 0.62),
    ("Leopard Cross Friesian Sport", "Legendary", 0.62),
    ("Brown Pintaloosa Friesian Sport", "Legendary", 0.62),
    ("Grey Pintaloosa Friesian Sport", "Legendary", 0.62),
    ("Red Roan Friesian Sport", "Legendary", 0.62),
    ("Brown Tobiano Friesian Sport", "Legendary", 0.62),
    ("Sorrel Tobiano Friesian Sport", "Legendary", 0.62),
    ("Grey Tobiano Friesian Sport", "Legendary", 0.62),
    ("Piebald Friesian Sport", "Legendary", 0.62),

    ("White Hair Friesian", "Legendary", 0.62),
    ("Braided Friesian", "Legendary", 0.62),
    ("Blue Roan Friesian Sport", "Legendary", 0.62),
    ("Appaloosa Friesian", "Legendary", 0.62),
    ("Dapple Overo Brown Friesian", "Legendary", 0.62),
    ("Speckled Overo Friesian", "Legendary", 0.62),
    ("Peacock Snowcap Friesian", "Legendary", 0.62),
    ("Tobiano Friesian", "Legendary", 0.62),

    ("Appaloosa Clydesdale", "Legendary", 0.62),
    ("Appaloosa Shire", "Legendary", 0.62),
    ("Dapple Grey Clydesdale", "Legendary", 0.62),
    ("Seal Bay Clydesdale", "Legendary", 0.62),

    # ---- EPIC (70%) ----
    ("Black Snowflake Arabian", "Epic", 0.95),
    ("Light Bay Arabian", "Epic", 0.95),
    ("Buckskin Arabian", "Epic", 0.95),
    ("Silver Dapple Arabian", "Epic", 0.95),
    ("Rose Grey Arabian", "Epic", 0.95),
    ("Silver Splashed Pintabian", "Epic", 0.95),
    ("Black Arabian", "Epic", 0.95),
    ("Light Brown Pintabian", "Epic", 0.95),
    ("Grey Tovero Pintabian", "Epic", 0.95),
    ("Red Dun Arabian", "Epic", 0.95),
    ("Liver Chestnut Pintabian", "Epic", 0.95),

    ("Bay Dun Kiger", "Epic", 0.95),
    ("Black Mustang", "Epic", 0.95),
    ("Grey Rabicano Mustang", "Epic", 0.95),
    ("Smokey Cream Mustang", "Epic", 0.95),
    ("Dapple Grey Mustang", "Epic", 0.95),
    ("Dark Bay Roan Mustang", "Epic", 0.95),
    ("White Mustang", "Epic", 0.95),
    ("Grulla Dapple Mustang", "Epic", 0.95),
    ("Grulla Dun Kiger", "Epic", 0.95),
    ("Blood Bay Kiger", "Epic", 0.95),
    ("Bay Mustang", "Epic", 0.95),
    ("Chestnut Skewbald Mustang", "Epic", 0.95),
    ("Silver Dapple Kiger", "Epic", 0.95),
    ("Grey Tobiano Kiger", "Epic", 0.95),

    ("Black Splashed Paint", "Epic", 0.95),
    ("Black Snowflake Quarter", "Epic", 0.95),
    ("Gray Overo Paint", "Epic", 0.95),
    ("Seal Bay Aussie", "Epic", 0.95),
    ("Buckskin Quarter", "Epic", 0.95),
    ("Dapple Bay Aussie", "Epic", 0.95),
    ("Cremello Aussie", "Epic", 0.95),
    ("Dapple Gray Quarter", "Epic", 0.95),
    ("Spotted Grey Quarter", "Epic", 0.95),
    ("Dark Seal Quarter", "Epic", 0.95),
    ("Dark Bay Aussie", "Epic", 0.95),
    ("Dark Brown Heart Quarter", "Epic", 0.95),
    ("Grey Splashed Quarter", "Epic", 0.95),
    ("Silver Ripple Aussie", "Epic", 0.95),
    ("Silver Dapple Quarter", "Epic", 0.95),
    ("White Quarter", "Epic", 0.95),
    ("Black Sabino Paint", "Epic", 0.95),
    ("Smokey Black Quarter", "Epic", 0.95),
    ("Chestnut Tobiano Paint", "Epic", 0.95),
    ("Grey Chimera Aussie", "Epic", 0.95),
    ("Champagne Spattered Quarter", "Epic", 0.95),
    ("Tobiano Grey Aussie", "Epic", 0.95),
    ("Palomino Quarter", "Epic", 0.95),
    ("Red Dun Aussie", "Epic", 0.95),
    ("Perlino Aussie", "Epic", 0.95),
    ("Rose Grey Quarter", "Epic", 0.95),
    ("Smokey Seal Quarter", "Epic", 0.95),

    ("Liver Splatter Paint", "Epic", 0.95),
    ("Liver Tobiano Paint", "Epic", 0.95),

    ("Grease Spot Pintabian", "Epic", 0.95),
    ("Grey Tobiano Pintabian", "Epic", 0.95),
    ("Appaloosa Pintabian", "Epic", 0.95),

    ("Dapple Seal Arabian", "Epic", 0.95),
    ("Dapple Overo Brown Arabian", "Epic", 0.95),
    ("Steel Grey Arabian", "Epic", 0.95),
    ("Dapple Brown Arabian", "Epic", 0.95),
    ("Overo Palomino Arabian", "Epic", 0.95),
    ("Overo Brown Arabian", "Epic", 0.95),
    ("Dapple Overo Grey Arabian", "Epic", 0.95),

    ("Appaloosa American Quarter", "Epic", 0.95),
    ("Drenched Appaloosa Quarter", "Epic", 0.95),
    ("Champagne Dapple Aussie", "Epic", 0.95),
    ("Tobiano Buckskin Paint", "Epic", 0.95),
    ("Perlino Dun Paint", "Epic", 0.95),
    ("Chestnut Faded Paint", "Epic", 0.95),
    ("Splashed Black Paint", "Epic", 0.95),
    ("Cream Tricolor Quarter", "Epic", 0.95),
    ("Grey Tricolor Paint", "Epic", 0.95),
]

register_banner(
    "Mystical Stable",
    mystical_items,
    aliases=["mystical", "ms"]
)

# =========================
# PART 4 — Majestic Stable
# =========================

majestic_items = [

    # ---- FEATURED LEGENDARY ----
    ("White Hair Friesian", "Legendary", 0.53),
    ("Braided Friesian", "Legendary", 0.53),
    ("Blue Roan Friesian Sport", "Legendary", 0.53),
    ("Blood Bay Friesian Sport", "Legendary", 0.53),
    ("Grey Friesian Sport", "Legendary", 0.53),
    ("Palomino Friesian Sport", "Legendary", 0.53),
    ("Leopard Cross Friesian Sport", "Legendary", 0.53),
    ("Brown Pintaloosa Friesian Sport", "Legendary", 0.53),
    ("Grey Pintaloosa Friesian Sport",  "Legendary", 0.53),
    ("Red Roan Friesian Sport", "Legendary", 0.53),
    ("Brown Tobiano Friesian Sport", "Legendary", 0.53),
    ("Sorrel Tobiano Friesian Sport", "Legendary", 0.53),
    ("Grey Tobiano Friesian Sport", "Legendary", 0.53),
    ("Piebald Friesian Sport", "Legendary", 0.53),
    ("Appaloosa Friesian", "Legendary", 0.53),
    ("Dapple Overo Brown Friesian", "Legendary", 0.53),
    ("Speckled Overo Friesian", "Legendary", 0.53),
    ("Peacock Snowcap Friesian", "Legendary", 0.53),
    ("Tobiano Friesian", "Legendary", 0.53),

    # ---- REGULAR LEGENDARY ----
    ("Black Shire", "Legendary", 0.62),
    ("Rose Grey Clydesdale", "Legendary", 0.62),
    ("Red Roan Clydesdale", "Legendary", 0.62),
    ("Black Overo Shire", "Legendary", 0.62),
    ("Strawberry Roan Clydesdale", "Legendary", 0.62),
    ("Blue Roan Shire", "Legendary", 0.62),
    ("Gray Tobiano Shire", "Legendary", 0.62),
    ("White Shire", "Legendary", 0.62),
    ("Sorrel Rabicano Clydesdale", "Legendary", 0.62),

    ("Blood Bay Friesian Sport", "Legendary", 0.62),
    ("Grey Friesian Sport", "Legendary", 0.62),
    ("Palomino Friesian Sport", "Legendary", 0.62),
    ("Leopard Cross Friesian Sport", "Legendary", 0.62),
    ("Brown Pintaloosa Friesian Sport", "Legendary", 0.62),
    ("Grey Pintaloosa Friesian Sport", "Legendary", 0.62),
    ("Red Roan Friesian Sport", "Legendary", 0.62),
    ("Brown Tobiano Friesian Sport", "Legendary", 0.62),
    ("Sorrel Tobiano Friesian Sport", "Legendary", 0.62),
    ("Grey Tobiano Friesian Sport", "Legendary", 0.62),
    ("Piebald Friesian Sport", "Legendary", 0.62),

    ("White Hair Friesian", "Legendary", 0.62),
    ("Braided Friesian", "Legendary", 0.62),
    ("Blue Roan Friesian Sport", "Legendary", 0.62),
    ("Appaloosa Friesian", "Legendary", 0.62),
    ("Dapple Overo Brown Friesian", "Legendary", 0.62),
    ("Speckled Overo Friesian", "Legendary", 0.62),
    ("Peacock Snowcap Friesian", "Legendary", 0.62),
    ("Tobiano Friesian", "Legendary", 0.62),

    ("Appaloosa Clydesdale", "Legendary", 0.62),
    ("Appaloosa Shire", "Legendary", 0.62),
    ("Dapple Grey Clydesdale", "Legendary", 0.62),
    ("Seal Bay Clydesdale", "Legendary", 0.62),

    # ---- EPIC ----
    ("Black Snowflake Arabian", "Epic", 0.95),
    ("Light Bay Arabian", "Epic", 0.95),
    ("Buckskin Arabian", "Epic", 0.95),
    ("Silver Dapple Arabian", "Epic", 0.95),
    ("Rose Grey Arabian", "Epic", 0.95),
    ("Silver Splashed Pintabian", "Epic", 0.95),
    ("Black Arabian", "Epic", 0.95),
    ("Light Brown Pintabian", "Epic", 0.95),
    ("Grey Tovero Pintabian", "Epic", 0.95),
    ("Red Dun Arabian", "Epic", 0.95),
    ("Liver Chestnut Pintabian", "Epic", 0.95),

    ("Bay Dun Kiger", "Epic", 0.95),
    ("Black Mustang", "Epic", 0.95),
    ("Grey Rabicano Mustang", "Epic", 0.95),
    ("Smokey Cream Mustang", "Epic", 0.95),
    ("Dapple Grey Mustang", "Epic", 0.95),
    ("Dark Bay Roan Mustang", "Epic", 0.95),
    ("White Mustang", "Epic", 0.95),
    ("Grulla Dapple Mustang", "Epic", 0.95),
    ("Grulla Dun Kiger", "Epic", 0.95),
    ("Blood Bay Kiger", "Epic", 0.95),
    ("Bay Mustang", "Epic", 0.95),
    ("Chestnut Skewbald Mustang", "Epic", 0.95),
    ("Silver Dapple Kiger", "Epic", 0.95),
    ("Grey Tobiano Kiger", "Epic", 0.95),

    ("Black Splashed Paint", "Epic", 0.95),
    ("Black Snowflake Quarter", "Epic", 0.95),
    ("Gray Overo Paint", "Epic", 0.95),
    ("Seal Bay Aussie", "Epic", 0.95),
    ("Buckskin Quarter", "Epic", 0.95),
    ("Dapple Bay Aussie", "Epic", 0.95),
    ("Cremello Aussie", "Epic", 0.95),
    ("Dapple Gray Quarter", "Epic", 0.95),
    ("Spotted Grey Quarter", "Epic", 0.95),
    ("Dark Seal Quarter", "Epic", 0.95),
    ("Dark Bay Aussie", "Epic", 0.95),
    ("Dark Brown Heart Quarter", "Epic", 0.95),
    ("Grey Splashed Quarter", "Epic", 0.95),
    ("Silver Ripple Aussie", "Epic", 0.95),
    ("Silver Dapple Quarter", "Epic", 0.95),
    ("White Quarter", "Epic", 0.95),
    ("Black Sabino Paint", "Epic", 0.95),
    ("Smokey Black Quarter", "Epic", 0.95),
    ("Chestnut Tobiano Paint", "Epic", 0.95),
    ("Grey Chimera Aussie", "Epic", 0.95),
    ("Champagne Spattered Quarter", "Epic", 0.95),
    ("Tobiano Grey Aussie", "Epic", 0.95),
    ("Palomino Quarter", "Epic", 0.95),
    ("Red Dun Aussie", "Epic", 0.95),
    ("Perlino Aussie", "Epic", 0.95),
    ("Rose Grey Quarter", "Epic", 0.95),
    ("Smokey Seal Quarter", "Epic", 0.95),

    ("Liver Splatter Paint", "Epic", 0.95),
    ("Liver Tobiano Paint", "Epic", 0.95),

    ("Grease Spot Pintabian", "Epic", 0.95),
    ("Grey Tobiano Pintabian", "Epic", 0.95),
    ("Appaloosa Pintabian", "Epic", 0.95),

    ("Dapple Seal Arabian", "Epic", 0.95),
    ("Dapple Overo Brown Arabian", "Epic", 0.95),
    ("Steel Grey Arabian", "Epic", 0.95),
    ("Dapple Brown Arabian", "Epic", 0.95),
    ("Overo Palomino Arabian", "Epic", 0.95),
    ("Overo Brown Arabian", "Epic", 0.95),
    ("Dapple Overo Grey Arabian", "Epic", 0.95),

    ("Appaloosa American Quarter", "Epic", 0.95),
    ("Drenched Appaloosa Quarter", "Epic", 0.95),
    ("Champagne Dapple Aussie", "Epic", 0.95),
    ("Tobiano Buckskin Paint", "Epic", 0.95),
    ("Perlino Dun Paint", "Epic", 0.95),
    ("Chestnut Faded Paint", "Epic", 0.95),
    ("Splashed Black Paint", "Epic", 0.95),
    ("Cream Tricolor Quarter", "Epic", 0.95),
    ("Grey Tricolor Paint", "Epic", 0.95),
]

register_banner(
    "Majestic Stable",
    majestic_items,
    aliases=["majestic", "mj"]
)

# =========================
# PART 5 — Winged Stable
# =========================

winged_items = [

    # ---- FLYING ----
    ("Azure Friesian Pegasus", "Flying", 2.00),
    ("Dark Friesian Pegasus", "Flying", 2.00),
    ("White Friesian Pegasus", "Flying", 2.00),
    ("Dapple Brown Friesian Pegasus", "Flying", 2.00),
    ("Dapple Grey Friesian Pegasus", "Flying", 2.00),

    # ---- FANTASY ----
    ("Aesir Friesian", "Fantasy", 3.00),
    ("Legendary Clydesdale", "Fantasy", 3.00),
    ("Aratiri Clydesdale", "Fantasy", 3.00),
    ("Sahar Arabian", "Fantasy", 3.00),
    ("Maelstrom Clydesdale", "Fantasy", 3.00),
    ("Night Glow", "Fantasy", 3.00),
    ("Glacier Storm", "Fantasy", 3.00),
    ("Atlantean Arabian", "Fantasy", 3.00),
    ("Cosmic Mustang", "Fantasy", 3.00),
    ("Wildfin Triton", "Fantasy", 3.00),

    # ---- LEGENDARY ----
    ("Black Shire", "Legendary", 1.87),
    ("Rose Grey Clydesdale", "Legendary", 1.87),
    ("Red Roan Clydesdale", "Legendary", 1.87),
    ("Strawberry Roan Clydesdale", "Legendary", 1.87),
    ("Blue Roan Shire", "Legendary", 1.87),
    ("Gray Tobiano Shire", "Legendary", 1.87),
    ("White Shire", "Legendary", 1.87),
    ("Sorrel Rabicano Clydesdale", "Legendary", 1.87),

    ("Blood Bay Friesian Sport", "Legendary", 1.87),
    ("Grey Friesian Sport", "Legendary", 1.87),
    ("Palomino Friesian Sport", "Legendary", 1.87),
    ("Leopard Cross Friesian Sport", "Legendary", 1.87),
    ("Brown Pintaloosa Friesian Sport", "Legendary", 1.87),
    ("Grey Pintaloosa Friesian Sport", "Legendary", 1.87),
    ("Red Roan Friesian Sport", "Legendary", 1.87),
    ("Brown Tobiano Friesian Sport", "Legendary", 1.87),
    ("Sorrel Tobiano Friesian Sport", "Legendary", 1.87),
    ("Grey Tobiano Friesian Sport", "Legendary", 1.87),
    ("Piebald Friesian Sport", "Legendary", 1.87),

    ("White Hair Friesian", "Legendary", 1.87),
    ("Braided Friesian", "Legendary", 1.87),
    ("Blue Roan Friesian Sport", "Legendary", 1.87),
    ("Appaloosa Friesian", "Legendary", 1.87),
    ("Dapple Overo Brown Friesian", "Legendary", 1.87),
    ("Speckled Overo Friesian", "Legendary", 1.87),
    ("Peacock Snowcap Friesian", "Legendary", 1.87),
    ("Tobiano Friesian", "Legendary", 1.87),

    ("Appaloosa Clydesdale", "Legendary", 1.87),
    ("Appaloosa Shire", "Legendary", 1.87),
    ("Dapple Grey Clydesdale", "Legendary", 1.87),
    ("Seal Bay Clydesdale", "Legendary", 1.87),
]

register_banner(
    "Winged Stable",
    winged_items,
    aliases=["winged", "pegasus", "fly"]
)

# =========================
# PART 7 — Valentine Stable (Limited)
# =========================

valentine_items = [

    # ---- FEATURED (5%) ----
    ("Lovestruck Unicorn", "Featured Fantasy", 5.00),

    # ---- FANTASY (20%) ----
    ("Aesir Friesian", "Fantasy", 2.00),
    ("Legendary Clydesdale", "Fantasy", 2.00),
    ("Aratiri Clydesdale", "Fantasy", 2.00),
    ("Sahar Arabian", "Fantasy", 2.00),
    ("Maelstrom Clydesdale", "Fantasy", 2.00),
    ("Night Glow", "Fantasy", 2.00),
    ("Glacier Storm", "Fantasy", 2.00),
    ("Atlantean Arabian", "Fantasy", 2.00),
    ("Cosmic Mustang", "Fantasy", 2.00),
    ("Wildfin Triton", "Fantasy", 2.00),

    # ---- LEGENDARY (25%) ----
    ("Black Shire", "Legendary", 0.78),
    ("Rose Grey Clydesdale", "Legendary", 0.78),
    ("Red Roan Clydesdale", "Legendary", 0.78),
    ("Black Overo Shire", "Legendary", 0.78),
    ("Strawberry Roan Clydesdale", "Legendary", 0.78),
    ("Blue Roan Shire", "Legendary", 0.78),
    ("Gray Tobiano Shire", "Legendary", 0.78),
    ("White Shire", "Legendary", 0.78),
    ("Sorrel Rabicano Clydesdale", "Legendary", 0.78),

    ("Blood Bay Friesian Sport", "Legendary", 0.78),
    ("Grey Friesian Sport", "Legendary", 0.78),
    ("Palomino Friesian Sport", "Legendary", 0.78),
    ("Leopard Cross Friesian Sport", "Legendary", 0.78),
    ("Brown Pintaloosa Friesian Sport", "Legendary", 0.78),
    ("Grey Pintaloosa Friesian Sport", "Legendary", 0.78),
    ("Red Roan Friesian Sport", "Legendary", 0.78),
    ("Brown Tobiano Friesian Sport", "Legendary", 0.78),
    ("Sorrel Tobiano Friesian Sport", "Legendary", 0.78),
    ("Grey Tobiano Friesian Sport", "Legendary", 0.78),
    ("Piebald Friesian Sport", "Legendary", 0.78),

    ("White Hair Friesian", "Legendary", 0.78),
    ("Braided Friesian", "Legendary", 0.78),
    ("Blue Roan Friesian Sport", "Legendary", 0.78),
    ("Appaloosa Friesian", "Legendary", 0.78),
    ("Dapple Overo Brown Friesian", "Legendary", 0.78),
    ("Speckled Overo Friesian", "Legendary", 0.78),
    ("Peacock Snowcap Friesian", "Legendary", 0.78),
    ("Tobiano Friesian", "Legendary", 0.78),

    ("Appaloosa Clydesdale", "Legendary", 0.78),
    ("Appaloosa Shire", "Legendary", 0.78),
    ("Dapple Grey Clydesdale", "Legendary", 0.78),
    ("Seal Bay Clydesdale", "Legendary", 0.78),

    # ---- EPIC (50%) ----
    # (all same chance so same weight)

    ("Black Snowflake Arabian", "Epic", 0.68),
    ("Light Bay Arabian", "Epic", 0.68),
    ("Buckskin Arabian", "Epic", 0.68),
    ("Silver Dapple Arabian", "Epic", 0.68),
    ("Rose Grey Arabian", "Epic", 0.68),
    ("Silver Splashed Pintabian", "Epic", 0.68),
    ("Black Arabian", "Epic", 0.68),
    ("Light Brown Pintabian", "Epic", 0.68),
    ("Grey Tovero Pintabian", "Epic", 0.68),
    ("Red Dun Arabian", "Epic", 0.68),
    ("Liver Chestnut Pintabian", "Epic", 0.68),

    ("Bay Dun Kiger", "Epic", 0.68),
    ("Black Mustang", "Epic", 0.68),
    ("Grey Rabicano Mustang", "Epic", 0.68),
    ("Smokey Cream Mustang", "Epic", 0.68),
    ("Dapple Grey Mustang", "Epic", 0.68),
    ("Dark Bay Roan Mustang", "Epic", 0.68),
    ("White Mustang", "Epic", 0.68),
    ("Grulla Dapple Mustang", "Epic", 0.68),
    ("Grulla Dun Kiger", "Epic", 0.68),
    ("Blood Bay Kiger", "Epic", 0.68),
    ("Bay Mustang", "Epic", 0.68),
    ("Chestnut Skewbald Mustang", "Epic", 0.68),
    ("Silver Dapple Kiger", "Epic", 0.68),
    ("Grey Tobiano Kiger", "Epic", 0.68),

    ("Black Splashed Paint", "Epic", 0.68),
    ("Black Snowflake Quarter", "Epic", 0.68),
    ("Gray Overo Paint", "Epic", 0.68),
    ("Seal Bay Aussie", "Epic", 0.68),
    ("Buckskin Quarter", "Epic", 0.68),
    ("Dapple Bay Aussie", "Epic", 0.68),
    ("Cremello Aussie", "Epic", 0.68),
    ("Dapple Gray Quarter", "Epic", 0.68),
    ("Spotted Grey Quarter", "Epic", 0.68),
    ("Dark Seal Quarter", "Epic", 0.68),
    ("Dark Bay Aussie", "Epic", 0.68),
    ("Dark Brown Heart Quarter", "Epic", 0.68),
    ("Grey Splashed Quarter", "Epic", 0.68),
    ("Silver Ripple Aussie", "Epic", 0.68),
    ("Silver Dapple Quarter", "Epic", 0.68),
    ("White Quarter", "Epic", 0.68),
]

register_banner(
    "Valentine Stable",
    valentine_items,
    aliases=["valentine", "love", "vday"]
)

# =========================
# PART 6 — Tack Banner
# =========================

tack_items = [

    # ---- LEGENDARY (1%) ----
    ("Bridle", "Legendary", 0.03),
    ("Saddle Pad", "Legendary", 0.03),
    ("Saddle", "Legendary", 0.03),
    ("Horseshoes", "Legendary", 0.03),

    # ---- EPIC (6%) ----
    ("Bridle", "Epic", 0.15),
    ("Saddle Pad", "Epic", 0.15),
    ("Saddle", "Epic", 0.15),
    ("Horseshoes", "Epic", 0.15),

    # ---- RARE (93%) ----
    ("Bridle", "Rare", 4.65),
    ("Saddle Pad", "Rare", 4.65),
    ("Saddle", "Rare", 4.65),
    ("Horseshoes", "Rare", 4.65),
]

register_banner(
    "Tack Banner",
    tack_items,
    aliases=["tack", "gear", "equipment"]
)

# =========================
# STREAMLIT UI (FULL FIXED)
# =========================

import streamlit as st
import io, csv
from collections import defaultdict

st.set_page_config(layout="wide")
st.title("Horse Stable Simulator 🐴")

# ---------------- THEME ----------------

theme_choice = st.sidebar.selectbox(
    "Theme",
    ["Auto", "Dark", "Light"]
)

def get_theme():
    if theme_choice == "Dark":
        return "dark"
    if theme_choice == "Light":
        return "light"

    # AUTO — safely mirror Streamlit theme
    base = st.get_option("theme.base")
    return base if base in ("dark", "light") else "dark"

THEME = get_theme()

# ---------------- COLORS ----------------

if THEME == "dark":

    BG = "#0e1117"
    TEXT = "#ffffff"
    HEADER_BG = "#555"
    FOOTER = "#666"

    RARITY_COLORS = {
        "Rare": "#4da6ff",
        "Epic": "#9b59b6",
        "Legendary": "#c9a227",
        "Fantasy": "#ffd966",
        "Flying": "#ff9fd6",
        "Featured Fantasy": "#ff6fb1"
    }

else:  # LIGHT MODE

    BG = "#ffffff"
    TEXT = "#111111"
    HEADER_BG = "#dddddd"
    FOOTER = "#444"

    RARITY_COLORS = {
        "Rare": "#1f6fd2",
        "Epic": "#6f2c91",
        "Legendary": "#9c7a00",
        "Fantasy": "#d4b200",
        "Flying": "#e066ad",
        "Featured Fantasy": "#cc2f85"
    }

# ---------------- GLOBAL CSS ----------------

st.markdown(
    f"""
    <style>
    body {{
        background-color:{BG};
        color:{TEXT};
    }}

    table {{
        width:100%;
        border-collapse:collapse;
    }}

    th {{
        background:{HEADER_BG};
        color:{TEXT};
        padding:6px;
    }}

    td {{
        padding:4px;
        text-align:center;
        color:{TEXT};
    }}

    mark {{
        background:#fffb91;
        color:black;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------- SESSION ----------------

if "LAST_RESULTS" not in st.session_state:
    st.session_state.LAST_RESULTS = None

if "TOTAL_PULLS" not in st.session_state:
    st.session_state.TOTAL_PULLS = 0

if "CUMULATIVE_COUNTS" not in st.session_state:
    st.session_state.CUMULATIVE_COUNTS = defaultdict(int)

if "RARITY_COUNTS" not in st.session_state:
    st.session_state.RARITY_COUNTS = defaultdict(int)

if "BANNERS" not in st.session_state:
    st.session_state.BANNERS = {}

# ✅ RESTORED PITY PERSISTENCE
if "PERSIST_PITY" not in st.session_state:
    st.session_state.PERSIST_PITY = True

# ---------------- SIDEBAR ----------------

st.sidebar.header("Settings")

advanced_mode = st.sidebar.checkbox("Advanced Mode")

# ✅ PITY TOGGLE BACK
st.session_state.PERSIST_PITY = st.sidebar.checkbox(
    "Persistent Pity",
    value=st.session_state.PERSIST_PITY
)

if st.sidebar.button("RESET ALL"):
    st.session_state.TOTAL_PULLS = 0
    st.session_state.CUMULATIVE_COUNTS.clear()
    st.session_state.RARITY_COUNTS.clear()
    st.session_state.LAST_RESULTS = None
    st.rerun()

# ---------------- MAIN ----------------

col1, col2, col3 = st.columns([2,1,1])

with col1:
    banner_choice = st.selectbox(
        "Choose a banner",
        list(st.session_state.BANNERS.keys())
    )

with col2:
    pulls = st.number_input("Pulls", min_value=1, value=1)

with col3:
    highlight_input = st.text_input("Highlight keywords")

highlights = [h.strip().lower() for h in highlight_input.split(",")] if highlight_input else []

# ---------------- TABLE RENDER ----------------

def render_table(rows, headers):

    html = "<table>"

    html += "<tr>"
    for h in headers:
        html += f"<th>{h}</th>"
    html += "</tr>"

    for row in rows:
        html += "<tr>"
        for idx, cell in enumerate(row):

            display = str(cell)

            if highlights and idx == 1:
                for kw in highlights:
                    if kw in display.lower():
                        display = display.replace(kw, f"<mark>{kw}</mark>")

            if display in RARITY_COLORS:
                html += f"<td style='color:{RARITY_COLORS[display]};font-weight:600'>{display}</td>"
            else:
                html += f"<td>{display}</td>"

        html += "</tr>"

    html += "</table>"

    st.markdown(html, unsafe_allow_html=True)

# ---------------- PULL BUTTON ----------------

if st.button("🎲 PULL", use_container_width=True):

    results = multi_pull(
        banner_choice,
        pulls,
        highlights,
        advanced=advanced_mode
    )

    st.session_state.LAST_RESULTS = results

    st.write("### Results")

    table_data = []

    if advanced_mode:
        headers = ["#", "Item", "Rarity", "Chance", "Owned", "Mark"]
        for r in results:
            table_data.append(r)
    else:
        headers = ["#", "Item", "Rarity", "Mark"]
        for i,n,rar,m in results:
            table_data.append([i,n,rar,m])

    render_table(table_data, headers)

# ---------------- DOWNLOAD ----------------

if st.session_state.LAST_RESULTS:

    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerows(st.session_state.LAST_RESULTS)

    st.download_button(
        "📥 Download Last Pull CSV",
        csv_buffer.getvalue(),
        file_name="last_pull.csv"
    )

# ---------------- STATS ----------------

if st.session_state.RARITY_COUNTS:

    st.write("## 📊 Pull Statistics")

    total = sum(st.session_state.RARITY_COUNTS.values())

    for rarity, count in st.session_state.RARITY_COUNTS.items():

        pct = (count/total)*100
        color = RARITY_COLORS.get(rarity, TEXT)

        st.markdown(
            f"<span style='color:{color};font-weight:600'>{rarity}</span>: {count} ({pct:.1f}%)",
            unsafe_allow_html=True
        )

# ---------------- EXTRA TABLES ----------------

def show_summary():
    rows = [[r,c] for r,c in st.session_state.RARITY_COUNTS.items()]
    render_table(rows, ["Rarity","Count"])

def show_cumulative():
    rows = sorted(
        st.session_state.CUMULATIVE_COUNTS.items(),
        key=lambda x:-x[1]
    )
    render_table(rows, ["Item","Count"])

def best_banner():

    scores = {}

    for banner, items in st.session_state.BANNERS.items():
        score = 0
        for _, rarity, weight in items:
            if "Legendary" in rarity: score+=weight*5
            elif "Epic" in rarity: score+=weight*3
            elif rarity in ("Fantasy","Flying"): score+=weight*2
            else: score+=weight
        scores[banner]=round(score,2)

    rows = sorted(scores.items(), key=lambda x:-x[1])
    render_table(rows, ["Banner","Score"])

st.divider()

c1,c2,c3 = st.columns(3)

with c1:
    if st.button("📜 Summary", use_container_width=True):
        show_summary()

with c2:
    if st.button("📦 Cumulative", use_container_width=True):
        show_cumulative()

with c3:
    if st.button("⭐ Best Banner", use_container_width=True):
        best_banner()

# ---------------- FOOTER ----------------

st.markdown(
f"""
<div style="width:100%;padding:10px;border-top:1px solid #999;margin-top:20px;
text-align:center;color:{FOOTER}">
Based on Star Equestrian | Credits: Nardalis | Support:
<a href="https://ko-fi.com/nardalisvault" target="_blank">Ko-Fi</a>
</div>
""",
unsafe_allow_html=True
)
