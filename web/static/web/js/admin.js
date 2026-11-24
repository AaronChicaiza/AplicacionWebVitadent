document.addEventListener('DOMContentLoaded', () => {
  const button = document.querySelector('.admin-menu-toggle');
  const sidebar = document.querySelector('.admin-sidebar');
  if (!button || !sidebar) return;
  button.addEventListener('click', () => {
    const open = button.getAttribute('aria-expanded') !== 'true';
    button.setAttribute('aria-expanded', String(open));
    sidebar.classList.toggle('is-open', open);
  });
});
