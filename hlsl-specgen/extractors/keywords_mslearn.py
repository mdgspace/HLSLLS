# extractors/keywords_mslearn.py
import re
from .base import Extractor, fetch, to_soup, dedup_by_key

IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

class KeywordsMSLearn(Extractor):
    name = "Keywords + Reserved (MS Learn)"
    target_key = "keywords"

    def __init__(self,
                 keywords_url="https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx-graphics-hlsl-appendix-keywords",
                 reserved_url="https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx-graphics-hlsl-appendix-reserved-words"):
        self.keywords_url = keywords_url
        self.reserved_url = reserved_url

    def run(self):
        items = []
        items += self._extract_keywords()
        items += self._extract_reserved()
        if not items:
            raise RuntimeError("No keywords or reserved words found")
        return dedup_by_key(items, key="name")

    def _extract_keywords(self):
        html = fetch(self.keywords_url, use_cache=True)
        soup = to_soup(html)

        h2 = soup.find("h2", id="ms--in-this-article")
        if not h2:
            raise RuntimeError("Keywords page: heading not found")

        ul = h2.find_next("ul")
        if not ul:
            raise RuntimeError("Keywords page: no <ul> after heading")

        items = []
        for li in ul.find_all("li", recursive=False):
            text = li.get_text(" ", strip=True)
            for token in text.split(","):
                token = token.strip()
                if token and IDENT.match(token):
                    items.append({"name": token, "kind": "hlsl"})
        return items

    def _extract_reserved(self):
        html = fetch(self.reserved_url, use_cache=True)
        soup = to_soup(html)

        content = soup.find("div", class_="column")
        if not content:
            raise RuntimeError("Reserved words page: div.content not found")

        para = content.find("p")
        if not para:
            raise RuntimeError("Reserved words page: no <p> with reserved list found")

        text = para.get_text(" ", strip=True)
        tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text)

        items = [{"name": t, "kind": "reserved"} for t in tokens if IDENT.match(t)]
        if not items:
            raise RuntimeError("Reserved words page: no identifiers parsed")
        return items
