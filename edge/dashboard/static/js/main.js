document.addEventListener('DOMContentLoaded', () => {
    // Sidebar Toggle Logic
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
    }

    // Set active nav item based on current URL path
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        const href = item.getAttribute('href');
        if (currentPath === href || (currentPath === '/' && href === '/')) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
});
