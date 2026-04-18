from __future__ import annotations

import html
import re


class MarkdownEngine:
    _TABLE_ALIGN_RE = re.compile(r"^\s*\|?[\s:-]+\|[\s|:-]*\|?\s*$")

    def render(self, text: str) -> str:
        lines = text.replace("\r\n", "\n").split("\n")
        out: list[str] = []
        para: list[str] = []
        list_mode: str | None = None
        in_code = False
        code_lang = ""
        i = 0

        def flush_para() -> None:
            nonlocal para
            if para:
                out.append(f"<p>{self._inline(' '.join(para).strip())}</p>")
                para = []

        def close_list() -> None:
            nonlocal list_mode
            if list_mode:
                out.append(f"</{list_mode}>")
                list_mode = None

        while i < len(lines):
            line = lines[i]

            if line.startswith("```"):
                flush_para()
                close_list()
                if not in_code:
                    in_code = True
                    code_lang = line[3:].strip()
                    cls = f' class="language-{html.escape(code_lang)}"' if code_lang else ""
                    lang_attr = f' data-lang="{html.escape(code_lang)}"' if code_lang else ""
                    out.append(f"<pre{lang_attr}><code{cls}>")
                else:
                    in_code = False
                    out.append("</code></pre>")
                i += 1
                continue

            if in_code:
                out.append(html.escape(line))
                i += 1
                continue

            if not line.strip():
                flush_para()
                close_list()
                i += 1
                continue

            if line.lstrip().startswith("<"):
                flush_para()
                close_list()
                out.append(line)
                i += 1
                continue

            head = re.match(r"^(#{1,6})\s+(.*)$", line)
            if head:
                flush_para()
                close_list()
                lvl = len(head.group(1))
                out.append(f"<h{lvl}>{self._inline(head.group(2).strip())}</h{lvl}>")
                i += 1
                continue

            if i + 1 < len(lines) and "|" in line and self._TABLE_ALIGN_RE.match(lines[i + 1] or ""):
                flush_para()
                close_list()
                header = self._split_cells(line)
                i += 2
                rows: list[list[str]] = []
                while i < len(lines):
                    row = lines[i]
                    if not row.strip() or "|" not in row:
                        break
                    rows.append(self._split_cells(row))
                    i += 1
                out.append("<table><thead><tr>")
                for c in header:
                    out.append(f"<th>{self._inline(c)}</th>")
                out.append("</tr></thead><tbody>")
                for r in rows:
                    out.append("<tr>")
                    for c in r:
                        out.append(f"<td>{self._inline(c)}</td>")
                    out.append("</tr>")
                out.append("</tbody></table>")
                continue

            bq = re.match(r"^>\s?(.*)$", line)
            if bq:
                flush_para()
                close_list()
                out.append(f"<blockquote><p>{self._inline(bq.group(1).strip())}</p></blockquote>")
                i += 1
                continue

            ul = re.match(r"^\s*[-*]\s+(.*)$", line)
            ol = re.match(r"^\s*\d+\.\s+(.*)$", line)
            if ul or ol:
                flush_para()
                mode = "ul" if ul else "ol"
                if list_mode != mode:
                    close_list()
                    out.append(f"<{mode}>")
                    list_mode = mode
                content = ul.group(1) if ul else ol.group(1)
                out.append(f"<li>{self._inline(content.strip())}</li>")
                i += 1
                continue

            para.append(line.strip())
            i += 1

        flush_para()
        close_list()
        if in_code:
            out.append("</code></pre>")
        result = "\n".join(out)
        result = re.sub(r"(<pre[^>]*><code[^>]*>)\n", r"\1", result)
        result = re.sub(r"<table>", '<div class="table-wrap"><table>', result)
        result = re.sub(r"</table>", "</table></div>", result)
        return result

    def _split_cells(self, line: str) -> list[str]:
        s = line.strip()
        if s.startswith("|"):
            s = s[1:]
        if s.endswith("|"):
            s = s[:-1]
        return [c.strip() for c in s.split("|")]

    def _inline(self, text: str) -> str:
        s = html.escape(text)
        s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img alt="\1" src="\2">', s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
        return s
