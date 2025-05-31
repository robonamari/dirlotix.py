function sortTable(e) {
  const tbody = document.querySelector("table tbody");
  const rows = Array.from(tbody.rows);
  const isSameColumn = e === window.lastSortedColumnIndex;
  const defaultAsc = {
    1: true,
    2: false,
    3: false
  };
  let isAsc = isSameColumn ? window.lastSortOrder !== "asc" : defaultAsc[e] ?? true;
  const sortedRows = rows.sort((a, b) => {
    let aText = a.cells[e]?.innerText?.toLowerCase() || "";
    let bText = b.cells[e]?.innerText?.toLowerCase() || "";
    if (e === 2) { // Size
      aText = parseFloat(aText) || 0;
      bText = parseFloat(bText) || 0;
    } else if (e === 3) { // Last Modified
      const aTime = a.cells[e].querySelector('time')?.getAttribute('datetime') || aText;
      const bTime = b.cells[e].querySelector('time')?.getAttribute('datetime') || bText;
      aText = new Date(aTime).getTime() || 0;
      bText = new Date(bTime).getTime() || 0;
    }
    if (aText > bText) return isAsc ? 1 : -1;
    if (aText < bText) return isAsc ? -1 : 1;
    return 0;
  });
  tbody.innerHTML = "";
  sortedRows.forEach(row => tbody.appendChild(row));
  window.lastSortedColumnIndex = e;
  window.lastSortOrder = isAsc ? "asc" : "desc";
  const parentDirRow = sortedRows.find(row => row.cells[1].innerText === "Parent Directory");
  if (parentDirRow) {
    tbody.prepend(parentDirRow);
  }
}
