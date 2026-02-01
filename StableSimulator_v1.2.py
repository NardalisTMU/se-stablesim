import random
from collections import defaultdict

# =========================
# GLOBAL STORAGE
# =========================

BANNERS = {}
ARCHIVED_BANNERS = set()
ALIASES = {}

# pity counters
GLOBAL_LEG_PITY = 0         # shared between Majestic and Mystical Stable
WINGED_PEGASUS_PITY = 0     # Winged Stable
TACK_EPIC_PITY = 0
TACK_LEG_PITY = 0
VALENTINE_LEG_PITY = 0

# pity persistence toggle
PERSIST_PITY = True

# cumulative stats
TOTAL_PULLS = 0
CUMULATIVE_COUNTS = defaultdict(int)
RARITY_COUNTS = defaultdict(int)

# =========================
# UTILITY FUNCTIONS
# =========================

def normalize(text):
    return text.lower().replace(" ", "").replace("_", "")

def register_banner(name, items, aliases=None, archived=False):
    BANNERS[name] = items
    if archived:
        ARCHIVED_BANNERS.add(name)
    if aliases:
        for a in aliases:
            ALIASES[normalize(a)] = name
    ALIASES[normalize(name)] = name

def list_banners():
    print("\nAvailable banners:")
    for b in BANNERS:
        tag = " (ARCHIVED)" if b in ARCHIVED_BANNERS else ""
        print(f"  - {b}{tag}")

def resolve_banner(input_name):
    key = normalize(input_name)
    return ALIASES.get(key)

# =========================
# TABLE DISPLAY
# =========================

def print_table(rows, headers):
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    def line():
        print("+" + "+".join("-" * (w + 2) for w in col_widths) + "+")

    line()
    print("| " + " | ".join(headers[i].ljust(col_widths[i]) for i in range(len(headers))) + " |")
    line()

    for row in rows:
        print("| " + " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(row))) + " |")
    line()

def print_table_chunked(rows, headers, chunk_size=50):
    for start in range(0, len(rows), chunk_size):
        chunk = rows[start:start + chunk_size]
        print_table(chunk, headers)
        if start + chunk_size < len(rows):
            input("\n--- Press Enter to continue ---\n")

# =========================
# WEIGHTED CHOICE
# =========================

def weighted_choice(items):
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
    global GLOBAL_LEG_PITY, WINGED_PEGASUS_PITY, TACK_EPIC_PITY, TACK_LEG_PITY, VALENTINE_LEG_PITY

    items = BANNERS[banner]
    pity_used = False
    pull_info = {}

    # ---------- TACK BANNER ----------
    if banner == "Tack Banner":
        TACK_EPIC_PITY += 1
        TACK_LEG_PITY += 1

        legendary_items = [i for i in items if i[1] == "Legendary"]
        epic_items = [i for i in items if i[1] == "Epic"]

        if TACK_LEG_PITY >= 90:
            name, rarity = weighted_choice(legendary_items)
            TACK_LEG_PITY = 0
            pity_used = True
            active_pool = legendary_items
        elif TACK_EPIC_PITY >= 10:
            name, rarity = weighted_choice(epic_items)
            TACK_EPIC_PITY = 0
            pity_used = True
            active_pool = epic_items
        else:
            name, rarity = weighted_choice(items)
            if rarity == "Legendary":
                TACK_LEG_PITY = 0
            if rarity == "Epic":
                TACK_EPIC_PITY = 0
            active_pool = items

        total_weight = sum(w for _, _, w in active_pool)
        for n, r, w in active_pool:
            if n == name:
                pull_info[f"{n} Chance"] = round(w / total_weight * 100, 2)

        pull_info["Tack Epic Pity"] = TACK_EPIC_PITY
        pull_info["Tack Legendary Pity"] = TACK_LEG_PITY
        return name, rarity, pity_used, pull_info

    # ---------- VALENTINE BANNER ----------
    if banner == "Valentine Stable":
        FEATURED_NAME = "Lovestruck Unicorn"

        # increment pity only if featured not obtained
        if all(n[0] != FEATURED_NAME for n in items):
            print("ERROR: Featured Valentine item not found!")
            return weighted_choice(items)[0], weighted_choice(items)[1], False, {}

        VALENTINE_LEG_PITY += 1
        featured_item = next(i for i in items if i[0] == FEATURED_NAME)

        if VALENTINE_LEG_PITY >= 25:
            name, rarity, _ = featured_item
            VALENTINE_LEG_PITY = 0
            pity_used = True
            active_pool = [featured_item]
        else:
            name, rarity = weighted_choice(items)
            if name == FEATURED_NAME:
                VALENTINE_LEG_PITY = 0
            active_pool = [i for i in items if i[1] == rarity]

        total_banner_weight = sum(w for _, _, w in items)
        category_weight = sum(w for _, _, w in active_pool)
        category_prob = category_weight / total_banner_weight

        for n, r, w in active_pool:
            if n == name:
                pull_info[f"{n} Chance"] = round(w / category_weight * category_prob * 100, 2)

        pull_info["Valentine Pity Counter"] = VALENTINE_LEG_PITY
        return name, rarity, pity_used, pull_info

    # ---------- WINGED STABLE ----------
    if banner == "Winged Stable":
        WINGED_PEGASUS_PITY += 1
        legendary_items = [i for i in items if i[0] == "Pegasus"]

        if WINGED_PEGASUS_PITY >= 10:
            name, rarity = weighted_choice(legendary_items)
            WINGED_PEGASUS_PITY = 0
            pity_used = True
            active_pool = legendary_items
        else:
            name, rarity = weighted_choice(items)
            if name == "Pegasus":
                WINGED_PEGASUS_PITY = 0
            active_pool = [i for i in items if i[1] == rarity]

        total_weight = sum(w for _, _, w in active_pool)
        for n, r, w in active_pool:
            if n == name:
                pull_info[f"{n} Chance"] = round(w / total_weight * 100, 2)

        pull_info["Winged Pity Counter"] = WINGED_PEGASUS_PITY
        return name, rarity, pity_used, pull_info

    # ---------- MAJESTIC & MYSTICAL STABLES ----------
    if banner in ("Majestic Stable", "Mystical Stable"):
        GLOBAL_LEG_PITY += 1
        legendary_items = [i for i in items if "Legendary" in i[1] or "Fantasy" in i[1]]

        if GLOBAL_LEG_PITY >= 10:
            name, rarity = weighted_choice(legendary_items)
            GLOBAL_LEG_PITY = 0
            pity_used = True
            active_pool = legendary_items
        else:
            name, rarity = weighted_choice(items)
            if "Legendary" in rarity or "Fantasy" in rarity:
                GLOBAL_LEG_PITY = 0
            active_pool = [i for i in items if i[1] == rarity]

        total_weight = sum(w for _, _, w in active_pool)
        for n, r, w in active_pool:
            if n == name:
                pull_info[f"{n} Chance"] = round(w / total_weight * 100, 2)

        pull_info["Horse Pity Counter"] = GLOBAL_LEG_PITY
        return name, rarity, pity_used, pull_info

    # ---------- OTHER BANNERS (COTN etc.) ----------
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
    global TOTAL_PULLS
    global GLOBAL_LEG_PITY, WINGED_PEGASUS_PITY, TACK_EPIC_PITY, TACK_LEG_PITY, VALENTINE_LEG_PITY

    # reset pity if persistence is OFF
    if not PERSIST_PITY:
        GLOBAL_LEG_PITY = 0
        WINGED_PEGASUS_PITY = 0
        TACK_EPIC_PITY = 0
        TACK_LEG_PITY = 0
        VALENTINE_LEG_PITY = 0

    highlights = highlights or []
    rows = []

    for i in range(1, amount + 1):
        name, rarity, pity_used, pull_info = pull_once(banner)

        TOTAL_PULLS += 1
        CUMULATIVE_COUNTS[name] += 1
        RARITY_COUNTS[rarity] += 1

        highlight_flag = any(h.lower() in name.lower() for h in highlights)
        highlight_mark = "PITY" if pity_used else ""
        if highlight_flag:
            highlight_mark += "*" if highlight_mark else "*"

        chance = pull_info.get(f"{name} Chance", "N/A")
        cumulative_count = CUMULATIVE_COUNTS[name]

        if advanced:
            rows.append([i, name, rarity, chance, cumulative_count, highlight_mark])
        else:
            rows.append([i, name, rarity, highlight_mark])

    if advanced:
        print_table_chunked(rows, ["#", "Item", "Rarity", "Chance (%)", "Cumulative", "Highlight"], 40)
    else:
        print_table_chunked(rows, ["#", "Item", "Rarity", "Highlight"], 40)

# =========================
# STATS
# =========================

def show_summary():
    rows = [[r, c] for r, c in sorted(RARITY_COUNTS.items())]
    print("\nPull Summary:")
    print_table(rows, ["Rarity", "Count"])

def show_cumulative():
    rows = [[item, count] for item, count in sorted(CUMULATIVE_COUNTS.items(), key=lambda x: -x[1])]
    print("\nCumulative Items:")
    print_table(rows, ["Item", "Times Pulled"])

# =========================
# BEST BANNER
# =========================

def best_banner():
    scores = {}

    for banner, items in BANNERS.items():
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
    print("\nBanner Strength (rough):")
    print_table(rows, ["Banner", "Score"])

# =========================
# INTERACTIVE
# =========================

def interactive():
    print("\n--- Horse Stable Simulator ---\n")
    print("Welcome to the simulator! Here's how it works:")
    print(" - Pull from various banners to get items of different rarities.")
    print(" - 'Pity' counters ensure you eventually get higher-rarity items:")
    print("     * Tack Banner: Epic pity at 10, Legendary pity at 90")
    print("     * Valentine Banner: Featured item pity at 25")
    print("     * Winged Stable: Pegasus pity at 10")
    print("     * Majestic/Mystical Stable: Legendary/Fantasy pity at 10 (shared)")
    print(" - Creatures of the Night (COTN) has no pity at all")
    print(" - You can toggle 'advanced' mode to see detailed stats for each pull.")
    print(" - 'pity on/off' will toggle whether pity counters persist between sessions.\n")
    print("Commands available: summary | cumulative | best | advanced on/off | pity on/off | exit\n")

    advanced_mode = False

    while True:
        list_banners()
        choice = input("\nChoose banner or command: ").strip()

        if choice.lower() == "exit":
            break
        elif choice.lower() == "summary":
            show_summary()
        elif choice.lower() == "cumulative":
            show_cumulative()
        elif choice.lower() == "best":
            best_banner()
        elif choice.lower() == "advanced on":
            advanced_mode = True
            print("Advanced mode ENABLED.")
        elif choice.lower() == "advanced off":
            advanced_mode = False
            print("Advanced mode DISABLED.")
        elif choice.lower() == "pity on":
            global PERSIST_PITY
            PERSIST_PITY = True
            print("Pity persistence ENABLED.")
        elif choice.lower() == "pity off":
            PERSIST_PITY = False
            print("Pity persistence DISABLED.")
        else:
            banner = resolve_banner(choice)
            if not banner:
                print("Invalid banner name.")
                continue

            try:
                pulls = int(input(f"How many pulls on {banner}? "))
            except ValueError:
                print("Enter a number.")
                continue

            highlight_input = input("Highlight keywords (comma separated, optional): ")
            highlights = [h.strip() for h in highlight_input.split(",")] if highlight_input else []

            multi_pull(banner, pulls, highlights, advanced=advanced_mode)

# =========================
# INTERACTIVE
# =========================

def interactive():
    print("\n--- Horse Stable Simulator ---\n")
    print("Welcome to the simulator! Here's how it works:")
    print(" - Pull from various banners to get items of different rarities.")
    print(" - 'Pity' counters ensure you eventually get higher-rarity items:")
    print("     * Tack Banner: Epic and Legendary pity")
    print("     * Valentine Banner: Featured item pity at 25 pulls")
    print("     * Global Horse Banners: Legendary pity at 10 pulls")
    print(" - You can toggle 'advanced' mode to see detailed stats for each pull.")
    print(" - 'pity on/off' will toggle whether pity counters persist between sessions.\n")
    print("Commands available: summary | cumulative | best | advanced on/off | pity on/off | exit\n")

    advanced_mode = False

    while True:
        list_banners()
        choice = input("\nChoose banner or command: ").strip()

        if choice.lower() == "exit":
            break

        elif choice.lower() == "summary":
            show_summary()

        elif choice.lower() == "cumulative":
            show_cumulative()

        elif choice.lower() == "best":
            best_banner()

        elif choice.lower() == "advanced on":
            advanced_mode = True
            print("Advanced mode ENABLED.")

        elif choice.lower() == "advanced off":
            advanced_mode = False
            print("Advanced mode DISABLED.")

        elif choice.lower() == "pity on":
            global PERSIST_PITY
            PERSIST_PITY = True
            print("Pity persistence ENABLED.")

        elif choice.lower() == "pity off":
            PERSIST_PITY = False
            print("Pity persistence DISABLED.")

        else:
            banner = resolve_banner(choice)
            if not banner:
                print("Invalid banner name.")
                continue

            try:
                pulls = int(input(f"How many pulls on {banner}? "))
            except ValueError:
                print("Enter a number.")
                continue

            highlight_input = input("Highlight keywords (comma separated, optional): ")
            highlights = [h.strip() for h in highlight_input.split(",")] if highlight_input else []

            multi_pull(banner, pulls, highlights, advanced=advanced_mode)


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


if __name__ == "__main__":
    interactive()