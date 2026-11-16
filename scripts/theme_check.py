"""Capture the light theme and check for dark leftovers / overflow issues."""
import os

from playwright.sync_api import sync_playwright

OUT = r"G:\实习\ai-panel-studio\docs\screenshots"
os.makedirs(OUT, exist_ok=True)
BASE = "http://127.0.0.1:5174/"


def luminance(rgb):
    r, g, b = [c / 255 for c in rgb]
    parts = []
    for c in (r, g, b):
        parts.append(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2]


def parse_rgb(s):
    nums = s[s.find("(") + 1: s.find(")")].split(",")
    return tuple(float(n.strip()) for n in nums[:3])


with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    page = b.new_page(viewport={"width": 1600, "height": 1000}, locale="zh-CN")
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    page.goto(BASE, wait_until="domcontentloaded")
    page.wait_for_timeout(2200)
    page.screenshot(path=os.path.join(OUT, "light-01-home.png"), full_page=True)

    # Sample computed backgrounds to prove nothing is dark
    bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
    print("body background:", bg, "| luminance:", round(luminance(parse_rgb(bg)), 3))

    # focus-visible check on the topic input
    page.locator("#topic-input").focus()
    page.wait_for_timeout(250)
    outline = page.evaluate(
        "(() => { const e = document.querySelector('#topic-input');"
        "const s = getComputedStyle(e); return s.outlineStyle + ' ' + s.outlineColor; })()"
    )
    print("input outline:", outline)

    # Studio view
    page.locator("button", has_text="演播厅实况").first.click()
    page.wait_for_timeout(4000)
    page.screenshot(path=os.path.join(OUT, "light-02-studio.png"), full_page=True)

    dark_nodes = page.evaluate(
        """(() => {
      const bad = [];
      for (const el of document.querySelectorAll('*')) {
        const s = getComputedStyle(el);
        const bg = s.backgroundColor;
        if (!bg || bg === 'rgba(0, 0, 0, 0)') continue;
        const m = bg.match(/\\d+(\\.\\d+)?/g);
        if (!m || m.length < 3) continue;
        const lum = (0.2126*+m[0] + 0.7152*+m[1] + 0.0722*+m[2]) / 255;
        const alpha = m.length > 3 ? +m[3] : 1;
        if (lum < 0.35 && alpha > 0.5) {
          bad.push(el.tagName + '.' + (el.className || '').toString().slice(0, 60) + ' -> ' + bg);
        }
      }
      return bad.slice(0, 10);
    })()"""
    )
    print("\ndark backgrounds (luminance<0.35, alpha>0.5):", len(dark_nodes))
    for n in dark_nodes:
        print("  ", n)

    # horizontal overflow at desktop
    ov = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    print("desktop horizontal overflow px:", ov)

    # Summary view
    page.goto(BASE, wait_until="domcontentloaded")
    page.wait_for_timeout(1800)
    page.locator("button", has_text="总结报告").first.click()
    page.wait_for_timeout(2500)
    page.screenshot(path=os.path.join(OUT, "light-03-summary.png"), full_page=True)

    # Narrow viewport check
    page.set_viewport_size({"width": 430, "height": 900})
    page.goto(BASE, wait_until="domcontentloaded")
    page.wait_for_timeout(1800)
    page.screenshot(path=os.path.join(OUT, "light-04-narrow.png"), full_page=True)
    ov_n = page.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    print("narrow(430px) horizontal overflow px:", ov_n)

    print("\npage errors:", errors if errors else "none")
    b.close()
