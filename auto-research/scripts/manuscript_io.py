"""Đọc bản thảo (Markdown hoặc LaTeX) và references.bib — dùng chung cho các cổng kiểm tra."""
from __future__ import annotations

import re
from pathlib import Path


def find_manuscript(rd: Path) -> tuple[Path | None, str]:
    m = rd / "manuscript"
    for name, kind in (("manuscript.md", "md"), ("main.tex", "tex"), ("manuscript.tex", "tex")):
        if (m / name).is_file():
            return m / name, kind
    return None, ""


def read_text(p: Path) -> str:
    text = p.read_text(encoding="utf-8")
    if p.suffix == ".tex":  # gộp \input{...}
        def inc(mo):
            q = p.parent / (mo.group(1) if mo.group(1).endswith(".tex") else mo.group(1) + ".tex")
            return read_text(q) if q.is_file() else mo.group(0)
        text = re.sub(r"\\(?:input|include)\{([^}]+)\}", inc, text)
    return text


def strip_comments(text: str, kind: str) -> str:
    if kind == "tex":
        return re.sub(r"(?<!\\)%.*", "", text)
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def body_without_references(text: str, kind: str) -> str:
    if kind == "md":
        return re.split(r"^#+\s*(References|Tài liệu tham khảo|Bibliography)\s*$", text, flags=re.M | re.I)[0]
    return re.split(r"\\begin\{thebibliography\}|\\bibliography\{|\\printbibliography", text)[0]


def parse_bib(path: Path) -> dict[str, dict]:
    """Parser BibTeX tối giản: @type{key, field = {..} | ".." | số, ...}."""
    if not path.is_file():
        return {}
    s = path.read_text(encoding="utf-8")
    out: dict[str, dict] = {}
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", s):
        start = m.end(); depth = 1; i = start
        while i < len(s) and depth:
            depth += {"{": 1, "}": -1}.get(s[i], 0); i += 1
        body = s[start:i - 1]
        fields = {"_type": m.group(1).lower(), "_span": (m.start(), i)}
        j = 0
        while j < len(body):
            fm = re.compile(r"\s*([\w-]+)\s*=\s*").match(body, j)
            if not fm:
                break
            j = fm.end(); name = fm.group(1).lower()
            if j < len(body) and body[j] == "{":
                d = 0; k = j
                while k < len(body):
                    d += {"{": 1, "}": -1}.get(body[k], 0); k += 1
                    if d == 0:
                        break
                val = body[j + 1:k - 1]; j = k
            elif j < len(body) and body[j] == '"':
                k = body.index('"', j + 1); val = body[j + 1:k]; j = k + 1
            else:
                k = re.compile(r"[,\n]").search(body, j); k = k.start() if k else len(body)
                val = body[j:k].strip(); j = k
            fields[name] = " ".join(val.replace("{", "").replace("}", "").split())
            cm = re.compile(r"\s*,").match(body, j)
            j = cm.end() if cm else j + 1
        out[m.group(2)] = fields
    return out


def cited_keys(text: str, kind: str) -> list[str]:
    keys: list[str] = []
    if kind == "md":
        for m in re.finditer(r"\[([^\]]*@[^\]]+)\]", text):
            keys += re.findall(r"@([\w:.-]+)", m.group(1))
        keys += re.findall(r"(?<![\w\[@])@([A-Za-z][\w:.-]*)(?=[\s,.;)])", text)
        keys = [k.rstrip(".:") for k in keys if not re.match(r"(fig|tbl|eq|sec):", k)]
    else:
        for m in re.finditer(r"\\(?:cite|citep|citet|parencite|textcite|autocite)\w*\*?(?:\[[^\]]*\])*\{([^}]+)\}", text):
            keys += [k.strip() for k in m.group(1).split(",")]
    seen = []
    for k in keys:
        if k not in seen:
            seen.append(k)
    return seen
