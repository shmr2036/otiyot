"""Build a single self-contained HTML file of the landing page for sharing.

The output opens straight from a WhatsApp attachment on iPhone and Android:
images and fonts are embedded as data URIs, so nothing else needs to travel
with the file. The Vimeo embeds become poster links, because a local file
cannot embed them. The page already renders fully without JavaScript, which
matters for iPhone's file preview. Fonts, scripts and images are inlined.

Usage: python3 tools/build_share.py [output.html]
"""
from __future__ import annotations

import base64
import io
import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / 'tools' / 'vendor'
SOURCE = ROOT / 'index.html'
DEFAULT_OUT = ROOT / 'share' / 'maaseh-otiyot.html'
SITE_URL = 'https://otiyot.emilim.net/'

MAX_IMAGE_WIDTH = 1200
JPEG_QUALITY = 80

PLAY_ICON = ('<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 5.5v13a1 1 0 0 0 1.5.86l11-6.5'
             'a1 1 0 0 0 0-1.72l-11-6.5A1 1 0 0 0 7 5.5z"/></svg>')

EXTRA_CSS = '''
    /* Shared-file build: videos open on Vimeo; fixed controls clear the phone's notch and home bar */
    .reel-link { position: relative; display: block; }
    .reel-link img { width: 100%; height: 100%; object-fit: cover; }
    .reel-link .play {
      position: absolute; inset: 0; margin: auto; width: 64px; height: 64px; border-radius: 50%;
      display: grid; place-items: center; background: rgba(27,20,16,.62);
      box-shadow: 0 0 0 1px rgba(217,154,61,.5);
      transition: transform .25s var(--ease), background .25s var(--ease);
    }
    .reel-link .play svg { width: 26px; height: 26px; color: var(--cream); transform: translateX(2px); }
    .reel-link:hover .play { transform: scale(1.08); background: rgba(168,67,26,.85); }
    .reel-link:focus-visible { outline-offset: 4px; border-radius: var(--radius); }
    header.site {
      padding-top: max(14px, env(safe-area-inset-top, 0px));
      padding-left: max(clamp(20px, 5vw, 48px), env(safe-area-inset-left, 0px));
      padding-right: max(clamp(20px, 5vw, 48px), env(safe-area-inset-right, 0px));
    }
    .wa-float { bottom: calc(22px + env(safe-area-inset-bottom, 0px)); }
    footer.site { padding-bottom: calc(40px + env(safe-area-inset-bottom, 0px)); }
'''


def data_uri(raw: bytes, mime: str) -> str:
    return f'data:{mime};base64,{base64.b64encode(raw).decode("ascii")}'


def jpeg_data_uri(path: Path) -> str:
    """Downscale to MAX_IMAGE_WIDTH and recompress; keep the original if that is smaller."""
    original = path.read_bytes()
    img = Image.open(io.BytesIO(original)).convert('RGB')
    if img.width > MAX_IMAGE_WIDTH:
        img = img.resize((MAX_IMAGE_WIDTH, round(img.height * MAX_IMAGE_WIDTH / img.width)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, 'JPEG', quality=JPEG_QUALITY, optimize=True, progressive=True)
    return data_uri(min(original, buf.getvalue(), key=len), 'image/jpeg')


def inline_fonts_css() -> str:
    """assets/css/fonts.css with each woff2 url() replaced by a data URI."""
    css = (ROOT / 'assets' / 'css' / 'fonts.css').read_text(encoding='utf-8')
    css = re.sub(r"url\('\.\./fonts/([^']+)'\)",
                 lambda m: f"url({data_uri((ROOT / 'assets' / 'fonts' / m.group(1)).read_bytes(), 'font/woff2')})",
                 css)
    return '<style>\n' + css + '  </style>'


def inline_script(m: re.Match) -> str:
    return '<script>\n' + (ROOT / m.group(1)).read_text(encoding='utf-8') + '</script>'


def build(out_path: Path) -> None:
    html = SOURCE.read_text(encoding='utf-8')

    html = html.replace('content="width=device-width, initial-scale=1.0"',
                        'content="width=device-width, initial-scale=1.0, viewport-fit=cover"', 1)
    html = re.sub(r'\s*<!-- Meta Pixel:.*?-->', '', html)
    html = re.sub(r'\s*<meta property="og:image"[^>]*>', '', html)

    # The site's CSP only allows same-origin files; a standalone file carries everything as
    # data: URIs and inline code, so it drops the policy (it has no user input to protect).
    html = re.sub(r'\s*<meta http-equiv="Content-Security-Policy"[^>]*>', '', html)

    # Self-hosted fonts and external scripts -> embedded.
    html = re.sub(r'\s*<link rel="preload"[^>]*as="font"[^>]*>', '', html)
    html, n_css = re.subn(r'<link rel="stylesheet" href="assets/css/fonts\.css" />', lambda _: inline_fonts_css(), html)
    html, n_js = re.subn(r'<script src="(assets/js/[^"]+\.js)"></script>', inline_script, html)
    if n_css != 1 or n_js != 2:
        sys.exit(f'expected 1 font stylesheet and 2 scripts, found {n_css} and {n_js}')

    # Vimeo embeds -> poster links.
    videos: list[str] = []

    def to_poster(m: re.Match) -> str:
        vid, title = m.group(1), m.group(2)
        videos.append(vid)
        thumb = data_uri((VENDOR / f'reel-{vid}.jpg').read_bytes(), 'image/jpeg')
        return (f'<a class="frame reel-link" href="https://vimeo.com/{vid}" target="_blank" rel="noopener" '
                f'aria-label="צפייה בסרטון: {title}">\n'
                f'            <img src="{thumb}" width="640" height="1137" decoding="async" alt="" />\n'
                f'            <span class="play" aria-hidden="true">{PLAY_ICON}</span>\n'
                f'          </a>')

    html = re.sub(r'<div class="frame">\s*<iframe src="https://player\.vimeo\.com/video/(\d+)[^"]*"'
                  r'(?:[^>]*?\s)?title="([^"]+)".*?</iframe>\s*</div>', to_poster, html, flags=re.S)
    if len(videos) != 2:
        sys.exit(f'expected 2 Vimeo embeds, found {videos}')

    # Local images -> data URIs.
    images: set[str] = set()

    def to_inline(m: re.Match) -> str:
        images.add(m.group(1))
        return f'src="{jpeg_data_uri(ROOT / m.group(1))}"'

    html = re.sub(r'src="(assets/images/[^"]+\.jpe?g)"', to_inline, html)

    # Pages that only exist on the site are linked by full URL.
    html = html.replace('href="accessibility.html"', f'href="{SITE_URL}accessibility.html" target="_blank" rel="noopener"')

    html = html.replace('  </style>\n</head>', EXTRA_CSS + '  </style>\n</head>', 1)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding='utf-8')
    leftovers = re.findall(r'(?:src|href)="(assets/[^"]+)"', html)
    print(f'{out_path}: {len(html.encode()) / 1024:.0f} KB | images {sorted(images)} | '
          f'videos {videos} | leftover refs {leftovers}')


if __name__ == '__main__':
    build(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT)
