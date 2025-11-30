const themeToggle = document.getElementById('theme-toggle');
themeToggle.addEventListener('click', () => {
	const isDark = document.documentElement.classList.toggle('dark-theme');
	localStorage.setItem('theme', isDark ? 'dark' : 'light');

	// изменяем логотип и cart
	 // изменяем логотип
	const logo = document.querySelector(".logo");
	if (localStorage.getItem('theme') === 'dark') {
		logo.src = whiteLogoPath;
		themeToggle.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 32 32"><path fill="#ffffff" d="M15 2h2v5h-2zm6.688 6.9l3.506-3.506l1.414 1.414l-3.506 3.506zM25 15h5v2h-5zm-3.312 8.1l1.414-1.413l3.506 3.506l-1.414 1.414zM15 25h2v5h-2zm-9.606.192L8.9 21.686l1.414 1.414l-3.505 3.506zM2 15h5v2H2zm3.395-8.192l1.414-1.414L10.315 8.9L8.9 10.314zM16 12a4 4 0 1 1-4 4a4.005 4.005 0 0 1 4-4m0-2a6 6 0 1 0 6 6a6 6 0 0 0-6-6Z"/></svg>'
	}
	else {
		logo.src = blackLogoPath;
		themeToggle.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 16 16"><path fill="#000000" d="M8.796 9.048c-1.552-2.238-1.199-5.323.61-8.1c-3.47-.12-6.6 2.232-7.269 5.672c-.742 3.82 1.83 7.533 5.749 8.294a7.226 7.226 0 0 0 7.526-3.218c-2.794.177-5.27-.711-6.616-2.648"/></svg>';
	}
});