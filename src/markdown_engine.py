from __future__ import annotations

import html
import re
from urllib.parse import quote


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
        self._fn_ids: dict[str, None] = {}
        self._fn_defs: dict[str, str] = {}
        lines = text.replace("\r\n", "\n").split("\n")
        out: list[str] = []
        para: list[str] = []
        list_stack: list[tuple[int, str]] = []
        in_code = False
        code_lang = ""
        code_lines: list[str] = []
        i = 0

        def flush_para() -> None:
            nonlocal para
            if para:
                out.append("<p>" + "<br>".join(self._inline(line) for line in para) + "</p>")
                para = []

        def close_list() -> None:
            nonlocal list_stack
            if list_stack:
                out.append("</li>")
                while list_stack:
                    _, mode = list_stack.pop()
                    out.append(f"</{mode}>")

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

            fn_def = re.match(r"^\[\^([^\]]+)\]:\s+(.*)", line)
            if fn_def:
                flush_para()
                close_list()
                fid = fn_def.group(1).strip()
                self._fn_defs[fid] = self._inline(fn_def.group(2))
                i += 1
                continue

            head = re.match(r"^(#{1,6})\s+(.*)$", line)
            if head:
                flush_para()
                close_list()
                lvl = len(head.group(1))
                out.append(f"<h{lvl} id=\"{self._slugify(head.group(2).strip())}\">{self._inline(head.group(2).strip())}</h{lvl}>")
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
                indent = len(line) - len(line.lstrip())
                content = (ul.group(1) if ul else ol.group(1)).strip()
                task_checked = None
                if ul:
                    tm = re.match(r"^\[([ xX])\]\s+(.*)", content)
                    if tm:
                        task_checked = tm.group(1).lower() == "x"
                        content = tm.group(2)
                inline_html = self._inline(content)
                if task_checked is not None:
                    checked = " checked" if task_checked else ""
                    inline_html = f'<input type="checkbox"{checked} disabled> {inline_html}'
                if not list_stack:
                    out.append(f"<{mode}>")
                    out.append(f"<li>{inline_html}")
                    list_stack.append((indent, mode))
                else:
                    prev_indent, prev_mode = list_stack[-1]
                    if indent > prev_indent:
                        out.append(f"<{mode}>")
                        out.append(f"<li>{inline_html}")
                        list_stack.append((indent, mode))
                    elif indent == prev_indent:
                        if mode != prev_mode:
                            out.append("</li>")
                            out.append(f"</{prev_mode}>")
                            list_stack.pop()
                            out.append(f"<{mode}>")
                            out.append(f"<li>{inline_html}")
                            list_stack.append((indent, mode))
                        else:
                            out.append("</li>")
                            out.append(f"<li>{inline_html}")
                    else:
                        out.append("</li>")
                        while list_stack and indent < list_stack[-1][0]:
                            _, m = list_stack.pop()
                            out.append(f"</{m}>")
                        if list_stack:
                            out.append("</li>")
                        if not list_stack or indent > list_stack[-1][0]:
                            out.append(f"<{mode}>")
                            out.append(f"<li>{inline_html}")
                            list_stack.append((indent, mode))
                        elif indent == list_stack[-1][0]:
                            if mode != list_stack[-1][1]:
                                _, m = list_stack.pop()
                                out.append(f"</{m}>")
                                out.append(f"<{mode}>")
                                list_stack.append((indent, mode))
                            out.append(f"<li>{inline_html}")
                i += 1
                continue

            para.append(line.strip())
            i += 1

        flush_para()
        close_list()
        if in_code:
            out.append(self._render_code_block(code_lang, code_lines))

        if self._fn_defs:
            fn_items = []
            for fid in self._fn_ids:
                if fid in self._fn_defs:
                    fn_items.append(
                        f'<li id="fn-{fid}"><p>{self._fn_defs[fid]} '
                        f'<a href="#fnref-{fid}">↩</a></p></li>'
                    )
            if fn_items:
                out.append('<hr>')
                out.append('<section class="footnotes"><ol>')
                out.extend(fn_items)
                out.append('</ol></section>')

        result = "\n".join(out)
        result = re.sub(r"<table>", '<div class="table-wrap"><table>', result)
        result = re.sub(r"</table>", "</table></div>", result)
        return result

    def _slugify(self, text: str) -> str:
        plain = re.sub(r"<[^>]+>", "", text).strip().lower()
        plain = re.sub(r"\s+", "-", plain)
        result: list[str] = []
        for ch in plain:
            if ch.isascii() and (ch.isalnum() or ch in "-_."):
                result.append(ch)
            elif not ch.isascii():
                result.append(quote(ch))
        return "".join(result)

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
        s = s.replace("\\|", "\x00")
        return [c.strip().replace("\x00", "|") for c in s.split("|")]

    def _inline(self, text: str) -> str:
        code: list[str] = []

        def _save_code(m: re.Match[str]) -> str:
            code.append(m.group(1))
            return f"\x01{len(code) - 1}\x01"

        s = re.sub(r"`([^`]+)`", _save_code, text)

        imgs: list[tuple[str, str, str]] = []

        def _save_img(m: re.Match[str]) -> str:
            imgs.append((m.group(1), m.group(2).strip(), m.group(3) or ""))
            return f"\x02{len(imgs) - 1}\x02"

        s = re.sub(r'!\[([^\]]*)\]\((\S+)(?:\s+"([^"]*)")?\)', _save_img, s)

        links: list[tuple[str, str]] = []

        def _save_link(m: re.Match[str]) -> str:
            links.append((m.group(1), m.group(2)))
            return f"\x03{len(links) - 1}\x03"

        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _save_link, s)

        s = html.escape(s)

        def _restore_link(m: re.Match[str]) -> str:
            txt, url = links[int(m.group(1))]
            return f'<a href="{url}">{html.escape(txt)}</a>'

        s = re.sub(r"\x03(\d+)\x03", _restore_link, s)

        def _restore_img(m: re.Match[str]) -> str:
            alt, src, title = imgs[int(m.group(1))]
            ta = f' title="{html.escape(title)}"' if title else ""
            return f'<img alt="{html.escape(alt)}" src="{src}" loading="lazy" decoding="async"{ta}>'

        s = re.sub(r"\x02(\d+)\x02", _restore_img, s)

        def _restore_code(m: re.Match[str]) -> str:
            return f"<code>{html.escape(code[int(m.group(1))])}</code>"

        s = re.sub(r"\x01(\d+)\x01", _restore_code, s)

        s = re.sub(r"~~([^~]+)~~", r"<del>\1</del>", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)

        def replace_fn(match: re.Match[str]) -> str:
            fid = match.group(1).strip()
            self._fn_ids[fid] = None
            return f'<sup><a href="#fn-{fid}" id="fnref-{fid}">[{fid}]</a></sup>'

        s = re.sub(r"\[\^([^\]]+)\]", replace_fn, s)
        return s
