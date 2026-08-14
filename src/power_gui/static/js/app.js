/**
 * POWER-GUI Core Client Application Utilities
 */

function updateClock() {
    const now = new Date();
    const utcString = now.toISOString().substring(11, 19) + ' UTC';
    const clockEl = document.getElementById('liveClock');
    if (clockEl) {
        clockEl.textContent = utcString;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    updateClock();
    setInterval(updateClock, 1000);
});
