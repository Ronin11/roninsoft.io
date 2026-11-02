# roninsoft.io

Static site for RoninSoft, served by GitHub Pages at https://roninsoft.io.

- Edit `src_*.html` (pages) and `_head.html` / `_header.html` / `_footer.html` (shared), then run `python3 build.py`
  to regenerate `index.html`, `hexbound/`, `hexbound/privacy/` and `support/`. Commit both.
- Styles in `assets/css/site.css`, images in `assets/img/` (screenshots are JPEGs at 1600 px wide).
- `CNAME` holds the custom domain; DNS at Namecheap points the apex at GitHub Pages' A records and `www` at
  `ronin11.github.io`.
