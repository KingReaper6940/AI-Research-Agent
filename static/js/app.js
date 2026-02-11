/**
 * DeepResearch — Landing Page JavaScript
 * Handles search form submission and example query chips.
 */

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('searchForm');
    const input = document.getElementById('searchInput');
    const chips = document.querySelectorAll('.example-chip');

    // Handle search form submission
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = input.value.trim();
        if (query) {
            // Navigate to research page with query param
            const encoded = encodeURIComponent(query);
            window.location.href = `/research?q=${encoded}`;
        }
    });

    // Handle example chip clicks
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            const query = chip.getAttribute('data-query');
            input.value = query;
            input.focus();
            // Auto-submit
            const encoded = encodeURIComponent(query);
            window.location.href = `/research?q=${encoded}`;
        });
    });

    // Subtle parallax on hero
    const hero = document.querySelector('.hero');
    if (hero) {
        window.addEventListener('mousemove', (e) => {
            const x = (e.clientX / window.innerWidth - 0.5) * 10;
            const y = (e.clientY / window.innerHeight - 0.5) * 10;
            const glow = document.querySelector('.hero-glow');
            if (glow) {
                glow.style.transform = `translateX(calc(-50% + ${x}px)) translateY(${y}px)`;
            }
        });
    }

    // Auto-focus search on page load
    if (input) {
        setTimeout(() => input.focus(), 600);
    }
});
