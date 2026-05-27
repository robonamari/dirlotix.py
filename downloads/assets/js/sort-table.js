function sortTable(e) {
  const tbody = document.querySelector("table tbody");
  const rows = Array.from(tbody.rows);
  const isFolder = r => !r.cells[2]?.innerText.trim();
  const isPrev = r => r.cells[1]?.innerText.trim() === "Previous Folder";
  if (e === 2 || e === 3) {
    const fixed = [], sortable = [];
    rows.forEach((r, i) => {
      const t = r.cells[e]?.innerText.trim();
      t ? sortable.push(r) : fixed.push({ r, i });
    });
    const same = e === window.lastSortedColumnIndex;
    const asc = same ? window.lastSortOrder !== "asc" : ({ 1: 1, 2: 0, 3: 0 }[e] ?? 1);
    sortable.sort((a, b) => {
      let aT = a.cells[e]?.innerText.toLowerCase() || "";
      let bT = b.cells[e]?.innerText.toLowerCase() || "";
      if (e === 2) {
        aT = parseFloat(aT) || 0;
        bT = parseFloat(bT) || 0;
      } else {
        const aD = a.cells[e]?.querySelector("time")?.getAttribute("datetime");
        const bD = b.cells[e]?.querySelector("time")?.getAttribute("datetime");
        aT = aD ? Date.parse(aD) : 0;
        bT = bD ? Date.parse(bD) : 0;
      }
      return aT > bT ? (asc ? 1 : -1) : aT < bT ? (asc ? -1 : 1) : 0;
    });
    const out = [];
    let si = 0;
    for (let i = 0; i < rows.length; i++) {
      const f = fixed.find(x => x.i === i);
      out.push(f ? f.r : sortable[si++]);
    }
    tbody.innerHTML = "";
    out.forEach(r => tbody.appendChild(r));
    window.lastSortedColumnIndex = e;
    window.lastSortOrder = asc ? "asc" : "desc";
    return;
  }
  const same = e === window.lastSortedColumnIndex;
  const asc = same ? window.lastSortOrder !== "asc" : true;
  rows.sort((a, b) => {
    const aT = a.cells[e]?.innerText.toLowerCase() || "";
    const bT = b.cells[e]?.innerText.toLowerCase() || "";
    return aT > bT ? (asc ? 1 : -1) : aT < bT ? (asc ? -1 : 1) : 0;
  });
  const prev = rows.filter(isPrev);
  const folders = rows.filter(r => !isPrev(r) && isFolder(r));
  const files = rows.filter(r => !isPrev(r) && !isFolder(r));
  tbody.innerHTML = "";
  [...prev, ...folders, ...files].forEach(r => tbody.appendChild(r));
  window.lastSortedColumnIndex = e;
  window.lastSortOrder = asc ? "asc" : "desc";
}
