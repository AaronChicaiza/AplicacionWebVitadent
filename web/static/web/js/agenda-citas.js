document.querySelectorAll('.agenda-appointment').forEach((item) => {
  const top = Number(item.dataset.top);
  const duration = Number(item.dataset.duration);
  if (Number.isFinite(top) && Number.isFinite(duration)) {
    item.style.top = `${Math.max(0, top)}px`;
    item.style.height = `${Math.max(15, duration)}px`;
  }
});
