async () => {
  const pill = document.querySelector('[data-testid="floating-tab-bar"]')?.firstElementChild;
  const pillTop = pill ? Math.round(pill.getBoundingClientRect().top) : null;
  let el = document.elementFromPoint(innerWidth / 2, innerHeight * 0.55);
  let sc = null;
  while (el) {
    const s = getComputedStyle(el);
    if ((s.overflowY === 'auto' || s.overflowY === 'scroll') && el.scrollHeight > el.clientHeight + 2) { sc = el; break; }
    el = el.parentElement;
  }
  if (!sc) return { pillTop, note: 'no scroller (content fits)', maxBottom: (() => {
    let mb = 0; document.querySelectorAll('[data-testid]').forEach(e => { if (e.closest('[data-testid="floating-tab-bar"]')) return; const r = e.getBoundingClientRect(); if (r.height > 0 && r.bottom <= innerHeight && r.bottom > mb) mb = r.bottom; }); return Math.round(mb); })() };
  sc.scrollTop = sc.scrollHeight;
  await new Promise(r => setTimeout(r, 1200));
  sc.scrollTop = sc.scrollHeight;
  await new Promise(r => setTimeout(r, 400));
  const cc = sc.firstElementChild;
  let maxB = 0, txt = '';
  cc.querySelectorAll('*').forEach(e => {
    const r = e.getBoundingClientRect();
    if (r.height > 0 && r.width > 0 && (e.innerText || '').trim() && e.children.length === 0 && r.bottom > maxB) { maxB = r.bottom; txt = e.innerText.trim().slice(0, 40); }
  });
  return { pillTop, scrollTop: Math.round(sc.scrollTop), max: sc.scrollHeight - sc.clientHeight, scrollerBottom: Math.round(sc.getBoundingClientRect().bottom), lastTextBottom: Math.round(maxB), lastTxt: txt, padBottom: getComputedStyle(cc).paddingBottom, hidden: pillTop !== null && maxB > pillTop };
}
