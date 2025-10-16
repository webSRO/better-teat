#!/usr/bin/env python3
# fix_cookies.py
# Walks through all HTML files in current directory tree.
# Ensures each has a cookie gate at top of <head> and a recheck loop at end of <head>.
# Redirects to /sorry.html if cookie is missing or expired.

import shutil
from pathlib import Path
from bs4 import BeautifulSoup

TOP_COOKIE_GATE = """(function () {
  function hasValidCookie() {
    const cookies = document.cookie.split("; ").map(c => c.trim());
    const accessCookie = cookies.find(c => c.startsWith("access="));
    if (!accessCookie) return false;
    const parts = accessCookie.split("=");
    if (parts.length < 2) return false;
    // cookie format: access=1|<ISO expiry>
    const val = parts[1];
    const match = val.match(/\\|(.*)$/);
    if (!match) return true; // if no expiry encoded, assume permanent
    const expiry = new Date(match[1]);
    return expiry > new Date();
  }
  if (!hasValidCookie()) {
    window.location.replace("/sorry.html");
  }
})();"""

END_SCHEDULER_BLOCK = """function recheckCookie() {
  function hasValidCookie() {
    const cookies = document.cookie.split("; ").map(c => c.trim());
    const accessCookie = cookies.find(c => c.startsWith("access="));
    if (!accessCookie) return false;
    const parts = accessCookie.split("=");
    if (parts.length < 2) return false;
    const val = parts[1];
    const match = val.match(/\\|(.*)$/);
    if (!match) return true;
    const expiry = new Date(match[1]);
    return expiry > new Date();
  }
  if (!hasValidCookie()) {
    window.location.replace("/sorry.html");
  }
}
function scheduleRecheck() {
  const next = Math.floor(Math.random() * (25000 - 10000 + 1)) + 10000;
  setTimeout(() => {
    recheckCookie();
    scheduleRecheck();
  }, next);
}
scheduleRecheck();"""

def script_text_equal(a, b):
    if a is None or b is None:
        return False
    na = "\n".join(line.rstrip() for line in a.strip().splitlines())
    nb = "\n".join(line.rstrip() for line in b.strip().splitlines())
    return na == nb

def find_exact_script(soup, code):
    matches = []
    for s in soup.find_all("script"):
        if s.has_attr("src"):
            continue
        txt = s.string if s.string is not None else s.get_text()
        if script_text_equal(txt, code):
            matches.append(s)
    return matches

def ensure_head_exists(soup):
    if soup.head is None:
        head = soup.new_tag("head")
        if soup.html:
            soup.html.insert(0, head)
        else:
            html = soup.new_tag("html")
            soup.insert(0, html)
            html.append(head)
    return soup.head

def insert_top_cookie_gate(soup, head):
    if find_exact_script(soup, TOP_COOKIE_GATE):
        return False
    s = soup.new_tag("script")
    s.string = TOP_COOKIE_GATE
    head.insert(0, s)
    return True

def insert_end_scheduler(soup, head):
    if find_exact_script(soup, END_SCHEDULER_BLOCK):
        return False
    s = soup.new_tag("script")
    s.string = END_SCHEDULER_BLOCK
    head.append(s)
    return True

def process_file(path: Path):
    html = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")
    head = ensure_head_exists(soup)
    insert_top_cookie_gate(soup, head)
    insert_end_scheduler(soup, head)
    backup = path.with_suffix(path.suffix + ".bak")
    shutil.copyfile(path, backup)
    path.write_text(str(soup), encoding="utf-8")
    print(f"Processed {path}")

def main():
    here = Path(".")
    for f in here.rglob("*.html"):
        process_file(f)

if __name__ == "__main__":
    main()
