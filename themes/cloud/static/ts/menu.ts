'use strict';

(function iifeMenu(document: Document, window: Window) {
	const menuBtn = document.querySelector('.menu__btn') as HTMLElement | null;
	const menu = document.querySelector('.menu__list') as HTMLElement | null;

	function toggleMenu(this: HTMLElement) {
		if (menu) {
			menu.classList.toggle('menu__list--active');
			menu.classList.toggle('menu__list--transition');
		}
		this.classList.toggle('menu__btn--active');
		this.setAttribute(
			'aria-expanded',
			this.getAttribute('aria-expanded') === 'true' ? 'false' : 'true'
		);
	}

	function removeMenuTransition(this: HTMLElement) {
		this.classList.remove('menu__list--transition');
	}

	if (menuBtn && menu) {
		menuBtn.addEventListener('click', toggleMenu, false);
		menu.addEventListener('transitionend', removeMenuTransition, false);
	}
}(document, window));
