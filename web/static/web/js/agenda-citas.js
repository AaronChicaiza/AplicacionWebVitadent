const grid = document.querySelector('.agenda-grid');
if (grid) {
  const hours = Math.max(1, Number(grid.dataset.hours));
  const hourSize = Math.min(52, Math.max(22, 440 / hours));
  grid.style.setProperty('--agenda-hour-size', `${hourSize}px`);
  grid.style.setProperty('--agenda-hours', String(hours));
  document.querySelectorAll('.agenda-appointment').forEach((item) => {
    const top = Number(item.dataset.top);
    const duration = Number(item.dataset.duration);
    if (Number.isFinite(top) && Number.isFinite(duration)) {
      item.style.top = `${Math.max(0, top) * hourSize / 60}px`;
      item.style.height = `${Math.max(14, duration * hourSize / 60)}px`;
    }
  });
}
