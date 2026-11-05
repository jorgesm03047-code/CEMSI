(() => {
  const toggle = document.getElementById('navToggle');
  const nav = document.getElementById('nav');
  if (!toggle || !nav) return;

  const isEnglish = document.documentElement.lang.toLowerCase().startsWith('en');
  const setOpen = (open, moveFocus = false) => {
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open
      ? (isEnglish ? 'Close menu' : 'Cerrar menú')
      : (isEnglish ? 'Open menu' : 'Abrir menú'));
    nav.classList.toggle('is-open', open);
    if (open && moveFocus) nav.querySelector('a')?.focus();
  };

  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    setOpen(open, open);
  });

  nav.addEventListener('click', event => {
    if (event.target.closest('a')) setOpen(false);
  });

  document.addEventListener('click', event => {
    if (!nav.contains(event.target) && !toggle.contains(event.target)) setOpen(false);
  });

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
      setOpen(false);
      toggle.focus();
    }
  });

  window.addEventListener('resize', () => {
    if (window.innerWidth > 1024) setOpen(false);
  });
})();
