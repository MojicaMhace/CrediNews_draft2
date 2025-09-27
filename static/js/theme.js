// Theme management for CrediNews

window.ThemeManager = window.ThemeManager || class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.init();
    }

    init() {
        // Apply saved theme on page load
        this.applyTheme(this.currentTheme);
        
        // Listen for theme toggle events
        this.setupThemeToggle();
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        this.currentTheme = theme;
        
        // Update theme toggle button if it exists
        const themeToggle = document.querySelector('.theme-toggle');
        if (themeToggle) {
            themeToggle.textContent = theme === 'light' ? '🌙' : '☀️';
        }
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
    }

    setupThemeToggle() {
        const themeToggle = document.querySelector('.theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }
    }
}

// Initialize theme manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new window.ThemeManager();
});