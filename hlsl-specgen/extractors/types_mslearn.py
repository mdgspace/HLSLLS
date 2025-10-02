# extractors/types_mslearn.py
import re
from .base import Extractor, fetch, to_soup, dedup_by_key


class TypesMSLearn(Extractor):
    name = "Types (MS Learn Scalars + String + Vectors + Matrices + Buffers)"
    target_key = "types"

    def __init__(self,
                 scalars_url="https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx-graphics-hlsl-scalar"):
        self.scalars_url = scalars_url

    def run(self):
        # 1) scrape scalars
        scalars = self._extract_scalars()
        if not scalars:
            raise RuntimeError(
                "No scalar types found in <div class='content'> lists")

        types_items = list(scalars)  # start ONLY with scalars

        # 2) add 'string' from its own section
        s = self._extract_string_type()
        if s:
            types_items.append(s)

        # 3) expand vectors and matrices strictly from scalar names
        scalar_names = [t["name"] for t in scalars]

        vec_items = self._expand_vectors(scalar_names)
        types_items.extend(vec_items)

        mat_items = self._expand_matrices(scalar_names)
        types_items.extend(mat_items)

        # 4) expand buffers from scalars + vectors + matrices
        buf_items = self._expand_buffers(
            scalar_names,
            [v["name"] for v in vec_items],
            [m["name"] for m in mat_items],
        )
        types_items.extend(buf_items)

        # 5) optional generic placeholders (nice for autocomplete)
        types_items.append(
            {"name": "vector<Type, Components>", "description": ["generic vector"]})
        types_items.append(
            {"name": "matrix<Type, Rows, Cols>", "description": ["generic matrix"]})

        return dedup_by_key(types_items, key="name")

    # ---------- scraping ----------

    def _extract_scalars(self):
        html = fetch(self.scalars_url, use_cache=True)
        soup = to_soup(html)

        out = []
        for ul in soup.select("div.content ul"):
            # skip any UL that lives under an H2 'See also'
            h2 = ul.find_previous("h2")
            if h2 and h2.get_text(strip=True).lower() == "see also":
                continue

            for li in ul.find_all("li", recursive=False):
                text = li.get_text(" ", strip=True)
                if not text:
                    continue
                # name = before first dash/en-dash/em-dash/colon, desc = after
                parts = re.split(r"\s*[-–—:]\s*", text, maxsplit=1)
                name = parts[0].strip()
                if not name:
                    continue
                desc = parts[1].strip() if len(parts) > 1 else ""
                out.append(
                    {"name": name, "description": [desc] if desc else []})
        return out

    def _extract_string_type(self):
        html = fetch(self.scalars_url, use_cache=True)
        soup = to_soup(html)

        h2 = soup.find("h2", string=re.compile(r"^\s*String type\s*$", re.I))
        if not h2:
            return None
        p = h2.find_next("p")
        if not p:
            return None
        return {"name": "string", "description": [p.get_text(" ", strip=True)]}

    # ---------- expansion ----------

    def _expand_vectors(self, scalar_names):
        out = []
        # exclude non-numerics and special qualifiers that aren't typical vector bases
        exclude = {"string", "snorm float", "unorm float"}

        base = [s for s in scalar_names if s not in exclude]

        for s in base:
            for n in range(1, 5):
                out.append({
                    "name": f"{s}{n}",
                    "description": [f"{n}-component vector of {s}"]
                })
                out.append({
                    "name": f"vector<{s}, {n}>",
                    "description": [f"{n}-component vector of {s} (generic form)"]
                })
            out.append({
                "name": f"vector<{s}>",
                "description": [f"defaults to 4-component vector of {s}"]
            })

        # bare shorthand default (float4)
        out.append({
            "name": "vector",
            "description": ["defaults to 4-component vector of float"]
        })
        return out

    def _expand_matrices(self, scalar_names):
        out = []
        exclude = {"string", "snorm float", "unorm float"}

        base = [s for s in scalar_names if s not in exclude]

        for s in base:
            for rows in range(1, 5):
                for cols in range(1, 5):
                    out.append({
                        "name": f"{s}{rows}x{cols}",
                        "description": [f"{rows}x{cols} matrix of {s}"]
                    })
                    out.append({
                        "name": f"matrix<{s}, {rows}, {cols}>",
                        "description": [f"{rows}x{cols} matrix of {s} (generic form)"]
                    })
            # defaults
            out.append({
                "name": f"matrix<{s}, 1>",
                "description": [f"defaults to 1x4 matrix of {s}"]
            })
            out.append({
                "name": f"matrix<{s}>",
                "description": [f"defaults to 4x4 matrix of {s}"]
            })

        # bare matrix = float4x4
        out.append({
            "name": "matrix",
            "description": ["defaults to 4x4 matrix of float"]
        })
        return out

    def _expand_buffers(self, scalar_names, vector_names, matrix_names):
        out = []

        # start with scalars, excluding non-payload bases
        exclude_scalars = {"string", "snorm float", "unorm float"}
        bases = [s for s in scalar_names if s not in exclude_scalars]

        # vectors: include concrete forms only; skip bare/generic placeholders
        for v in vector_names:
            if v in {"vector", "vector<Type, Components>"}:
                continue
            bases.append(v)

        # matrices: include concrete forms only; skip bare/generic placeholders
        for m in matrix_names:
            if m in {"matrix", "matrix<Type, Rows, Cols>"}:
                continue
            bases.append(m)

        # dedupe while preserving order
        seen = set()
        ordered_bases = []
        for b in bases:
            if b not in seen:
                seen.add(b)
                ordered_bases.append(b)

        for t in ordered_bases:
            out.append({
                "name": f"Buffer<{t}>",
                "description": [f"read-only buffer of {t}"]
            })

        return out
