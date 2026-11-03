"""Markdown companions for freshly rendered report HTML; never a scientific input.

The report writes its own escaped HTML in a private staging directory. Converting
that same content keeps Markdown and HTML explanations together without another
model call, another judgment or a second set of prose templates.
"""
from html.parser import HTMLParser
import hashlib
from pathlib import Path
import re
from urllib.parse import urlsplit, urlunsplit


def _plain(text):
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"([\\`*_\[\]#!|~])", r"\\\1", text)


def _escape(text):
    text = re.sub(r"\s+", " ", text)
    # GFM autolinking can keep a backslash inside a bare URL instead of
    # interpreting its escaped underscore. Explicit labels preserve the text.
    parts = re.split(r"(https?://[^\s<>\"']+|www\.[^\s<>\"']+)", text)
    result = []
    for index, part in enumerate(parts):
        if index % 2:
            url = part.rstrip(".,;:!")
            while url.endswith(")") and url.count(")") > url.count("("):
                url = url[:-1]
            if url.startswith("www."):
                fence = "`" * max(1, max((len(x) + 1 for x in re.findall(r"`+", url)), default=0))
                result.append(fence + url + fence + _plain(part[len(url):]))
            else:
                result.append("[" + _plain(url) + "](<" + url.replace("`", "%60") + ">)" + _plain(part[len(url):]))
        else:
            result.append(_plain(part))
    return "".join(result)


def markdown_link(value):
    parts = urlsplit(value)
    if parts.scheme:
        if parts.scheme != "https":
            raise ValueError("Unexpected report link scheme")
        return value
    path = parts.path
    if path == "index.html" or path.endswith("/index.html"):
        path = path[:-len("index.html")] + "README.md"
    elif path.endswith(".html"):
        path = path[:-5] + ".md"
    return urlunsplit(("", "", path, parts.query, parts.fragment))


class _Markdown(HTMLParser):
    void = {"br", "hr", "meta", "link", "input"}
    hidden = {"head", "nav", "script", "style", "label"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip = 0
        self.links = []
        self.lists = 0
        self.pre = None

    def block(self):
        while self.out and not self.out[-1].strip():
            self.out.pop()
        if self.out:
            self.out[-1] = self.out[-1].rstrip("\n")
        self.out.append("\n\n")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.void:
            self.handle_endtag(tag)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.skip:
            if tag not in self.void:
                self.skip += 1
            return
        if tag in self.hidden:
            self.skip = 1
            return
        if self.pre is not None:
            raise ValueError("Unexpected nested markup inside report code")
        if tag == "pre":
            self.block(); self.pre = []
        elif tag in {"h1", "h2", "h3", "h4"}:
            self.block(); self.out.append("#" * int(tag[1]) + " ")
        elif tag in {"p", "article", "section", "footer", "div"}:
            self.block()
            if attrs.get("id"):
                anchor = attrs["id"]
                if not re.fullmatch(r"[A-Za-z0-9_-]+", anchor):
                    raise ValueError("Unsafe report anchor")
                self.out.append('<a name="' + anchor + '"></a>\n\n')
        elif tag in {"ul", "ol"}:
            self.block(); self.lists += 1
        elif tag == "li":
            self.out.append("\n" + "  " * max(0, self.lists - 1) + "- ")
        elif tag == "br":
            self.out.append("\n  " if self.lists else "  \n")
        elif tag in {"strong", "b"}:
            self.out.append("**")
        elif tag in {"em", "i"}:
            self.out.append("*")
        elif tag == "a":
            href = attrs.get("href")
            self.links.append(href)
            if href is not None:
                self.out.append("[")
        elif tag == "details":
            self.block(); self.out.append("<details>\n")
        elif tag == "summary":
            self.out.append("<summary>")

    def handle_endtag(self, tag):
        if self.skip:
            self.skip -= 1
            return
        if tag == "pre":
            content = "".join(self.pre or [])
            fence = "`" * max(3, max((len(x) + 1 for x in re.findall(r"`+", content)), default=0))
            self.out.append(fence + "json\n" + content + "\n" + fence)
            self.pre = None; self.block()
        elif tag in {"h1", "h2", "h3", "h4", "p", "article", "section", "footer", "div"}:
            self.block()
        elif tag in {"ul", "ol"}:
            self.lists -= 1; self.block()
        elif tag == "li":
            self.out.append("\n")
        elif tag in {"strong", "b"}:
            self.out.append("**")
        elif tag in {"em", "i"}:
            self.out.append("*")
        elif tag == "a":
            href = self.links.pop()
            if href is not None:
                self.out.append("](<" + markdown_link(href).replace(">", "%3E").replace("<", "%3C") + ">)")
        elif tag == "summary":
            self.out.append("</summary>\n\n")
        elif tag == "details":
            self.block(); self.out.append("</details>"); self.block()

    def handle_data(self, value):
        if self.skip:
            return
        if self.pre is not None:
            self.pre.append(value)
        else:
            self.out.append(_escape(value))


def to_markdown(source, *, depth=0):
    parser = _Markdown(); parser.feed(source); parser.close()
    if parser.skip or parser.pre is not None or parser.links or parser.lists:
        raise ValueError("Incomplete report markup")
    text = "".join(parser.out)
    # Keep code blocks exact; normalize block spacing outside them at emission.
    text = text.strip() + "\n"
    prefix = "../" if depth else ""
    navigation = " · ".join("[" + label + "](" + prefix + target + ")" for target, label in (
        ("README.md", "Overview"), ("primary.md", "Primary readings"),
        ("support.md", "Support readings"), ("other-papers.md", "Other assessed papers"),
        ("references.md", "Reference studies")))
    split = text.find("\n\n")
    if split < 0:
        return text + "\n" + navigation + "\n"
    return text[:split] + "\n\n" + navigation + text[split:]


def write_markdown(root):
    root = Path(root)
    sources = sorted(root.rglob("*.html"))
    for source in sources:
        target = source.with_name("README.md") if source == root / "index.html" else source.with_suffix(".md")
        if target.exists() or source.is_symlink():
            raise ValueError("Markdown export needs freshly generated report files")
        depth = 1 if source.parent == root / "papers" else 0
        with target.open("w", encoding="utf-8", newline="\n") as out:
            out.write(to_markdown(source.read_text(encoding="utf-8"), depth=depth))
    return {"entry": "README.md", "files": len(sources),
            "renderer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "meaning": "Same generated study prose and evidence, linked for Markdown/GitHub viewing"}
