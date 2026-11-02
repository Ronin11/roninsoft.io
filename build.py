#!/usr/bin/env python3
"""Assemble the pages from src_*.html and the shared _head/_header/_footer snippets. Run after editing."""
import os
here = os.path.dirname(os.path.abspath(__file__))
rd = lambda n: open(os.path.join(here, n)).read()
parts = {"HEAD": rd("_head.html"), "HEADER": rd("_header.html"), "FOOTER": rd("_footer.html")}
pages = {"src_index.html": "index.html", "src_hexbound.html": "hexbound/index.html",
         "src_privacy.html": "hexbound/privacy/index.html", "src_support.html": "support/index.html"}
for src, out in pages.items():
    html = rd(src)
    for k, v in parts.items():
        html = html.replace("{{%s}}" % k, v.strip())
    os.makedirs(os.path.dirname(os.path.join(here, out)) or here, exist_ok=True)
    open(os.path.join(here, out), "w").write(html)
    print("built", out)
