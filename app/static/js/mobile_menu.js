const menuBtn = document.querySelector(".menu-btn");
const mobileMenu = document.querySelector(".mobile-menu");
const menuItems = document.querySelectorAll(".mobile-nav__ul li a");

menuBtn.setAttribute('aria-controls', 'mobile-menu');
mobileMenu.setAttribute('id', 'mobile-menu');
mobileMenu.setAttribute('aria-hidden', 'true');

menuBtn.addEventListener('click', () => {
  const isOpen = mobileMenu.classList.toggle('open');
  menuBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  mobileMenu.setAttribute('aria-hidden', !isOpen);
  document.body.classList.toggle('no-scroll');
  if (!isOpen) {
    menuBtn.focus();
  }
});

menuItems.forEach(link => {
  link.addEventListener('click', () => {
    mobileMenu.classList.remove('open');
    menuBtn.setAttribute('aria-expanded', 'false');
    mobileMenu.setAttribute('aria-hidden', 'true');
    document.body.classList.remove('no-scroll');
    menuBtn.focus();
  });
});

menuBtn.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault();
    menuBtn.click();
  }
});
