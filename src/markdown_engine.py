from __future__ import annotations

import html
import re


class MarkdownEngine:
    _TABLE_ALIGN_RE = re.compile(r"^\s*\|?[\s:-]+\|[\s|:-]*\|?\s*$")
    _SUPPORTED_LANGS = {"bash", "python", "c", "r", "html", "css", "cs"}
    _LANG_ALIAS = {
        "sh": "bash",
        "shell": "bash",
        "zsh": "bash",
        "py": "python",
        "rscript": "r",
        "c#": "cs",
        "csharp": "cs",
    }

    def render(self, text: str) -> str:
        lines = text.replace("\r\n", "\n").split("\n")
        out: list[str] = []
        para: list[str] = []
        list_mode: str | None = None
        in_code = False
        code_lang = ""
        code_lines: list[str] = []
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
                    code_lines = []
                else:
                    in_code = False
                    out.append(self._render_code_block(code_lang, code_lines))
                i += 1
                continue

            if in_code:
                code_lines.append(line)
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

            hr = re.match(r"^\s{0,3}([-*_])(\s*\1){2,}\s*$", line)
            if hr:
                flush_para()
                close_list()
                out.append("<hr>")
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
                bq_lines: list[str] = []
                while i < len(lines):
                    cur = re.match(r"^>\s?(.*)$", lines[i])
                    if not cur:
                        break
                    bq_lines.append(cur.group(1).strip())
                    i += 1
                bq_parts: list[str] = []
                para_lines: list[str] = []
                for ql in bq_lines:
                    if ql:
                        para_lines.append(ql)
                        continue
                    if para_lines:
                        bq_parts.append("<p>" + "<br>".join(self._inline(x) for x in para_lines) + "</p>")
                        para_lines = []
                if para_lines:
                    bq_parts.append("<p>" + "<br>".join(self._inline(x) for x in para_lines) + "</p>")
                out.append(f"<blockquote>{''.join(bq_parts) if bq_parts else '<p></p>'}</blockquote>")
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
            out.append(self._render_code_block(code_lang, code_lines))
        result = "\n".join(out)
        result = re.sub(r"<table>", '<div class="table-wrap"><table>', result)
        result = re.sub(r"</table>", "</table></div>", result)
        return result

    def _normalize_lang(self, raw: str) -> str:
        lang = raw.strip().lower()
        return self._LANG_ALIAS.get(lang, lang)

    def _render_code_block(self, raw_lang: str, lines: list[str]) -> str:
        code = "\n".join(lines)
        lang = self._normalize_lang(raw_lang)
        if lang in self._SUPPORTED_LANGS:
            highlighted = self._highlight_source(code, lang)
            return f'<pre><code class="codehilite">{highlighted}</code></pre>'
        return f'<pre><code class="nohighlight">{html.escape(code)}</code></pre>'

    def _highlight_source(self, code: str, lang: str) -> str:
        kw = {
            "bash": {
                "if", "then", "else", "fi", "for", "while", "do", "done", "case", "esac", "function", "in", "echo",
                "export", "sudo", "cd", "cat", "grep", "sed", "awk", "systemctl", "pacman", "curl",
            },
            "python": {
                "def", "class", "if", "elif", "else", "for", "while", "try", "except", "finally", "return", "import",
                "from", "as", "with", "pass", "break", "continue", "lambda", "True", "False", "None",
            },
            "c": {
                "int", "long", "short", "float", "double", "char", "void", "const", "static", "struct", "enum", "if",
                "else", "for", "while", "switch", "case", "break", "continue", "return", "typedef", "sizeof",
            },
            "cs": {
                "using", "namespace", "class", "public", "private", "protected", "static", "void", "int", "string",
                "bool", "if", "else", "for", "while", "switch", "case", "break", "continue", "return", "new", "null",
                "true", "false",
            },
            "r": {
                "function", "if", "else", "for", "while", "repeat", "in", "next", "break", "return", "TRUE", "FALSE",
                "NULL", "library",
            },
            "html": set(),
            "css": {
                "@media", "@keyframes", "@supports", "display", "position", "color", "background", "font-size",
                "padding", "margin", "border", "width", "height", "grid", "flex", "overflow",
            },
        }[lang]
        comment_re = {
            "bash": r"#[^\n]*",
            "python": r"#[^\n]*",
            "r": r"#[^\n]*",
            "c": r"//[^\n]*|/\*[\s\S]*?\*/",
            "cs": r"//[^\n]*|/\*[\s\S]*?\*/",
            "css": r"/\*[\s\S]*?\*/",
            "html": r"<!--[\s\S]*?-->",
        }[lang]
        tag_re = r"</?[a-zA-Z][^>]*?>" if lang == "html" else r"$^"
        atrule_re = r"@[a-zA-Z_-]+" if lang == "css" else r"$^"
        kw_re = r"\b(?:%s)\b" % "|".join(sorted(re.escape(x) for x in kw if not x.startswith("@"))) if kw else r"$^"
        string_re = r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
        number_re = r"\b\d+(?:\.\d+)?\b"
        token_re = re.compile(
            rf"(?P<comment>{comment_re})|(?P<tag>{tag_re})|(?P<atrule>{atrule_re})|(?P<string>{string_re})|"
            rf"(?P<keyword>{kw_re})|(?P<number>{number_re})",
            re.MULTILINE,
        )
        out: list[str] = []
        pos = 0
        for m in token_re.finditer(code):
            if m.start() > pos:
                out.append(html.escape(code[pos:m.start()]))
            text = html.escape(m.group(0))
            if m.lastgroup == "comment":
                out.append(f'<span class="tok-c">{text}</span>')
            elif m.lastgroup in {"tag", "keyword", "atrule"}:
                out.append(f'<span class="tok-k">{text}</span>')
            elif m.lastgroup == "string":
                out.append(f'<span class="tok-s">{text}</span>')
            elif m.lastgroup == "number":
                out.append(f'<span class="tok-n">{text}</span>')
            else:
                out.append(text)
            pos = m.end()
        if pos < len(code):
            out.append(html.escape(code[pos:]))
        return "".join(out)

    def _split_cells(self, line: str) -> list[str]:
        s = line.strip()
        if s.startswith("|"):
            s = s[1:]
        if s.endswith("|"):
            s = s[:-1]
        return [c.strip() for c in s.split("|")]

    def _inline(self, text: str) -> str:
        s = html.escape(text)
        s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img alt="\1" src="\2" loading="lazy" decoding="async">', s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
        return s
