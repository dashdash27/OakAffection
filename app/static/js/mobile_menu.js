const menuBtn = document.querySelector(".menu-btn");
const mobileMenu = document.querySelector(".mobile-menu");
const menuItems = document.querySelector(".mobile-nav__ul").querySelectorAll("li");

menuBtn.addEventListener('click', () => {
  const isOpen = mobileMenu.classList.toggle('open');
  menuBtn.setAttribute('aria-expanded', isOpen);
  document.body.classList.toggle('no-scroll');
});

menuItems.forEach(link => {
  link.addEventListener('click', () => {
    // Закрываем меню
    mobileMenu.classList.remove('open');
    menuBtn.setAttribute('aria-expanded', false);
    document.body.classList.toggle('no-scroll');
  });
});