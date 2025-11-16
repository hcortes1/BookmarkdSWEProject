// countdown timer for recommended books refresh
function updateCountdown() {
    const countdownEl = document.getElementById('refresh-countdown');
    if (!countdownEl) return;

    const now = new Date();
    const et = new Date(now.toLocaleString('en-US', {timeZone: 'America/New_York'}));
    
    let nextRefresh = new Date(et);
    nextRefresh.setHours(19, 0, 0, 0);
    
    if (et >= nextRefresh) {
        nextRefresh.setDate(nextRefresh.getDate() + 1);
    }
    
    const diff = nextRefresh - et;
    const hours = Math.floor(diff / 3600000);
    const minutes = Math.floor((diff % 3600000) / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);
    
    countdownEl.textContent = `Refreshes in ${hours}h ${minutes}m ${seconds}s`;
}

// start countdown when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        updateCountdown();
        setInterval(updateCountdown, 1000);
    });
} else {
    updateCountdown();
    setInterval(updateCountdown, 1000);
}

// re-initialize countdown when dash re-renders the page
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        restart_countdown: function() {
            setTimeout(function() {
                updateCountdown();
            }, 100);
            return window.dash_clientside.no_update;
        }
    }
});
