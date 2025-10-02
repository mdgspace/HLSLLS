# extractors/functions_mslearn.py
import re
from .base import Extractor, fetch, to_soup, dedup_by_key

WS = re.compile(r"\s+")

# map Unicode superscripts to normal digits
_SUPER_TO_DIGIT = str.maketrans({
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
    "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9"
})


class FunctionsMSLearn(Extractor):
    name = "Functions (MS Learn Intrinsics)"
    target_key = "functions"

    def __init__(self,
                 url="https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx-graphics-hlsl-intrinsic-functions"):
        self.url = url

    def run(self):
        html = fetch(self.url, use_cache=True)
        soup = to_soup(html)

        tables = soup.select("div.content table")
        if not tables:
            raise RuntimeError(
                "No tables found under .content on intrinsics page")

        table = tables[0]  # first table only
        out = []

        for tr in table.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if len(cells) < 2 or cells[0].name == "th":
                continue

            name = self._clean(cells[0].get_text(" ", strip=True))
            if not name:
                continue

            desc = self._clean(cells[1].get_text(" ", strip=True))
            raw_sm = self._clean(cells[2].get_text(
                " ", strip=True)) if len(cells) >= 3 else ""
            min_sm = self._normalize_sm(raw_sm)

            out.append({
                "name": name,
                "kind": "intrinsic",
                "description": desc,         # single string
                "min_shader_model": min_sm,  # e.g. "2_1", "4_0", "" if unknown
                "return_type": "",           # intentionally empty for now
                "parameters": []             # intentionally empty for now
            })

        if not out:
            raise RuntimeError(
                "Intrinsic functions table parsed but yielded 0 rows")

        return dedup_by_key(out, key="name")

    def _clean(self, s: str) -> str:
        s = WS.sub(" ", s or "").strip()
        # trim surrounding quotes/backticks if the cell used them
        if len(s) >= 2 and s[0] == s[-1] and s[0] in {"`", '"', "“", "”"}:
            s = s[1:-1].strip()
        return s

    def _normalize_sm(self, s: str) -> str:
        """
        Normalize to 'M_m' (e.g. '2_1', '4_0').
        Handles '2¹', '1^1', '2.0', 'ps_4_1 or higher', etc.
        Strategy: strip to digits and pick the first (major in 1..6) and the next digit as minor.
        """
        if not s:
            return ""

        # map unicode superscripts, drop obvious noise
        t = s.translate(_SUPER_TO_DIGIT)
        t = re.sub(r"\bor higher\b|\bplus\b|\+$", "", t, flags=re.I)
        t = t.replace("^", "").lower()

        # keep only digits so we don't care about underscores/periods/superscripts/etc.
        digits = re.findall(r"\d", t)
        if not digits:
            return ""

        # find first valid major (1..6)
        major_idx = next((i for i, d in enumerate(digits) if d in {
                         "1", "2", "3", "4", "5", "6"}), None)
        if major_idx is None:
            return ""

        major = digits[major_idx]
        minor = digits[major_idx + 1] if major_idx + 1 < len(digits) else "0"
        return f"{major}_{minor}"
