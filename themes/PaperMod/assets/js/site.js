const menu = document.getElementById("menu");
if (menu) {
    menu.scrollLeft = localStorage.getItem("menu-scroll-position");
    menu.onscroll = () => localStorage.setItem("menu-scroll-position", menu.scrollLeft);
}

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener("click", function (e) {
        e.preventDefault();
        const id = this.getAttribute("href").substr(1);
        const target = document.querySelector(`[id='${decodeURIComponent(id)}']`);
        if (!target) return;
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
            target.scrollIntoView();
        } else {
            target.scrollIntoView({ behavior: "smooth" });
        }
        if (id === "top") {
            history.replaceState(null, null, " ");
        } else {
            history.pushState(null, null, `#${id}`);
        }
    });
});

const topLink = document.getElementById("top-link");
if (topLink) {
    window.addEventListener("scroll", () => {
        const show = document.body.scrollTop > 800 || document.documentElement.scrollTop > 800;
        topLink.style.visibility = show ? "visible" : "hidden";
        topLink.style.opacity = show ? "1" : "0";
    }, { passive: true });
}

const themeToggle = document.getElementById("theme-toggle");
if (themeToggle) {
    themeToggle.addEventListener("click", () => {
        if (document.body.className.includes("dark")) {
            document.body.classList.remove("dark");
            localStorage.setItem("pref-theme", "light");
        } else {
            document.body.classList.add("dark");
            localStorage.setItem("pref-theme", "dark");
        }
    });
}
