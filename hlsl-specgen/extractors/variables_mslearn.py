# extractors/variables_mslearn.py
import re
from .base import Extractor, fetch, to_soup, dedup_by_key

FAMILY_RE = re.compile(
    r"^(?P<base>[A-Za-z_][A-Za-z0-9_]*?)\s*\[\s*n\s*\]\s*$", re.I)
IS_SV = re.compile(r"^\s*SV_", re.I)


class VariablesMSLearn(Extractor):
    name = "Variables (MS Learn tables: VS/PS + SV)"
    target_key = "variables"

    def __init__(self,
                 url="https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx-graphics-hlsl-semantics",
                 expand_range=(0, 7)):
        self.url = url
        self.expand_lo, self.expand_hi = expand_range  # inclusive

    def run(self):
        html = fetch(self.url, use_cache=True)
        soup = to_soup(html)

        tables = soup.select("div.content table")
        if len(tables) < 5:
            raise RuntimeError(
                "Expected at least 5 tables (VS in/out, PS in/out, SV)")

        role_labels = ["vs_in", "vs_out", "ps_in", "ps_out"]
        items_by_name = {}

        # First four tables: aggregate modifiers
        for idx in range(4):
            role = role_labels[idx]
            for row in self._rows(tables[idx]):
                name, desc, typ = row["name"], row["desc"], row.get("type", "")
                if not name:
                    continue

                entry = items_by_name.get(name) or {
                    "name": name,
                    "description": "",      # string, not list
                    "type": "",
                    "modifiers": set(),
                }
                entry["description"] = self._merge_desc(
                    entry["description"], desc)
                if typ and not entry["type"]:
                    entry["type"] = typ
                if not IS_SV.match(name):
                    entry["modifiers"].add(role)
                items_by_name[name] = entry

                # Family NAME[n]
                fam = self._family_key(name)
                if fam:
                    fentry = items_by_name.get(fam) or {
                        "name": fam,
                        "description": "",
                        "type": "",
                        "modifiers": set(),
                    }
                    fentry["description"] = self._merge_desc(
                        fentry["description"], desc)
                    if typ and not fentry["type"]:
                        fentry["type"] = typ
                    fentry["modifiers"].add(role)
                    items_by_name[fam] = fentry

        # Fifth table: system value semantics; leave modifiers empty
        for row in self._rows(tables[4]):
            name, desc, typ = row["name"], row["desc"], row.get("type", "")
            if not name:
                continue
            entry = items_by_name.get(name) or {
                "name": name,
                "description": "",
                "type": "",
                "modifiers": set(),
            }
            entry["description"] = self._merge_desc(entry["description"], desc)
            if typ and not entry["type"]:
                entry["type"] = typ
            items_by_name[name] = entry

        # Expand families like COLOR[n] -> COLOR0..COLOR7
        expanded = {}
        for key, entry in list(items_by_name.items()):
            m = FAMILY_RE.match(key)
            if not m:
                continue
            base = m.group("base")
            for i in range(self.expand_lo, self.expand_hi + 1):
                concrete = f"{base}{i}"
                centry = items_by_name.get(concrete) or {
                    "name": concrete,
                    # keep as string
                    "description": entry.get("description", ""),
                    "type": entry.get("type", ""),
                    "modifiers": set(entry.get("modifiers", set())),
                }
                expanded[concrete] = centry

        # Finish: flatten modifier sets to sorted lists; description stays string
        all_items = {**items_by_name, **expanded}
        out = []
        for name, e in all_items.items():
            out.append({
                "name": name,
                "type": e.get("type", ""),
                "modifiers": sorted(e["modifiers"]) if e.get("modifiers") else [],
                "description": e.get("description", ""),
            })

        out.sort(key=lambda x: x["name"].lower())
        return dedup_by_key(out, key="name")

    # ---------- helpers ----------

    def _rows(self, table):
        rows = []
        for tr in table.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            name = cells[0].get_text(" ", strip=True)
            desc = cells[1].get_text(" ", strip=True)
            typ = cells[2].get_text(" ", strip=True) if len(cells) >= 3 else ""
            rows.append({"name": name, "desc": desc, "type": typ})
        return rows

    def _family_key(self, name: str):
        m = FAMILY_RE.match(name)
        return m.group(0) if m else None

    def _merge_desc(self, existing: str, new: str):
        # keep the first non-empty description, never overwrite
        if existing:
            return existing
        return new or ""
