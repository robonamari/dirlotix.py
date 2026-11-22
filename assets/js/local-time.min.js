document.querySelectorAll("time[datetime]").forEach(t => t.textContent = new Date(t.dateTime).toLocaleString());
