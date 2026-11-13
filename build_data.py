"""Builds miniapp/data.js from the GTADB GTA VI landmarks (CC BY 4.0, https://map.gtadb.org).
Usage: python miniapp/build_data.py   (re-run any time to pull the latest community data)
Landmark row: [name, [x, y], ig_photo_size, real_life_name, [lat, lng], rl_photo_size, tags, hash, edited]."""
import json, urllib.request
from collections import Counter
from pathlib import Path

URL = "https://raw.githubusercontent.com/rolux/gtadb.org/main/map/data/6/landmarks.json"  # source named in LICENSE-DATA
OUT = Path(__file__).parent / "data.js"

# category -> tags that select it (first match wins, order matters)
CATS = [
    ("safehouse", {"#safehouse"}),
    ("gas", {"#gas"}),
    ("food", {"restaurant", "#food", "#bar", "#vendor"}),
    ("night", {"#nightclub", "#stripclub"}),
    ("shop", {"retail", "#supermarket", "supermarket", "#clothes", "#guns", "#hair", "#modshop", "#tattoo"}),
    ("hotel", {"hotel"}),
    ("services", {"#police", "#hospital", "government", "public", "#fire"}),
    ("transport", {"transportation", "#bus", "#train", "#airport", "#metro", "#metromover", "#marina"}),
    ("leisure", {"leisure", "landmark", "events", "#racetrack", "#tennis", "natural"}),
    ("home", {"residential"}),
    ("industry", {"industrial", "utilities", "construction", "agriculture", "office"}),
]


# keyword rules on the in-game name, then on the real-life prototype name (first match wins)
import re
WORDS = [
    ("gas", r"\bgas\b|xero|\bfuel"),
    ("services", r"police|sheriff|fire (station|rescue|chief|dept)|\bfire\b|hospital|city hall|courthouse|post ?office|postal|prison|jail|coast guard|lifeguard"),
    ("parking", r"parking|car park"),
    ("cars", r"car wash|dealership|auto|salvage|repair|body shop|tire|mechanic|\bgarage\b"),
    ("bank", r"\bbank|lombank|\bcash\b|\batm\b|credit union"),
    ("hotel", r"hotel|hostel|resort|\binn\b|motel|beach house|suites"),
    ("food", r"restaurant|cafe|café|diner|grill|\bbar\b|pizza|burger|kitchen|bakery|foods|taco|checkers|oar house|cuban|coffee|bean\b|steak|seafood|bbq"),
    ("night", r"night ?club|strip|lounge|\bclub\b(?!.*(yacht|golf|fishing|outboard|tennis|racquet|country))"),
    ("shop", r"store|\bshop|market|\bmall\b|emporium|pawn|pharmacy|clothing|boutique|burberry|outlet|liquor|tattoo|barber|salon|laundr"),
    ("transport", r"marina|\bpier\b|boat|\bdock|seaplane|airport|runway|hangar|station|train|\bbus\b|terminal|ramp|yacht|ferry|metro"),
    ("roads", r"\bturn\b|bridge|tunnel|interchange|overpass|causeway|cswy|highway|crossing|\bgate\b"),
    ("landmark", r"tower|sign|mural|museum|gallery|church|chapel|temple|oceanarium|stadium|grandstand|arena|theat|cinema|monument|statue|center|centre|welcome|blimp|lighthouse|hall\b|library|school|university|college"),
    ("nature", r"\bpark\b|state park|lake|beach|river|canal|\bhill|golf|\bdam\b|jetty|harbor|harbour|\bkey\b|island|swamp|creek|reef|garden|trail|forest|stiltsville"),
    ("home", r"condo|lofts?\b|apartment|residen|villas?\b|\bhomes?\b|village|townhouse|estates?\b|brickell key (one|two)|plaza"),
    ("industry", r"warehouse|container|crane|construction|substation|electric|distribution|factory|plant|mill|silo|tank|depot|yard"),
]


def cat(tags, name, rl):
    for c, sel in CATS:
        if sel & set(tags):
            return c
    for text in (name, rl.split(",")[0] if rl else ""):
        t = text.lower()
        for c, rx in WORDS:
            if t and t != "?" and re.search(rx, t):
                return c
    return "other"


def main():
    req = urllib.request.Request(URL, headers={"User-Agent": "theftco-miniapp-builder"})
    raw = json.load(urllib.request.urlopen(req, timeout=60))
    rows = []
    for lid, v in raw.items():
        name, xy, igs, rl, _ll, _rls, tags, _h, edited = v
        if len(xy) != 2:
            continue  # not placed on the map yet
        x, y = xy
        parts = [p.strip() for p in name.split(",")]
        title = parts[0] if parts[0] != "?" else "Unidentified building"
        area = ", ".join(parts[1:])
        rows.append({
            "i": lid, "n": title, "a": area,
            # Leaflet CRS.Simple: 1024 px at zoom 0 for the 32768-unit world centred on 16384
            "lat": round(-(16384 - y) / 32, 2), "lng": round((x + 16384) / 32, 2),
            "c": cat(tags, parts[0], rl or ""), "w": igs[0] if igs else 0, "e": int("enterable" in tags), "u": int("unconfirmed" in tags),
            "p": int(bool(igs and igs[0])), "v": edited[1] if len(edited) > 1 else 0,
            "r": rl if rl and rl != "?" else "",
        })
    OUT.write_text("// GTA VI Landmarks Data (CC BY 4.0) — https://map.gtadb.org (converted)\nwindow.LANDMARKS=" +
                   json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(len(rows), "landmarks", Counter(r["c"] for r in rows).most_common(), f"{OUT.stat().st_size // 1024} KB")
    assert len(rows) > 1000 and all(-1100 < r["lat"] < 100 and 0 < r["lng"] < 1100 for r in rows)


if __name__ == "__main__":
    main()
