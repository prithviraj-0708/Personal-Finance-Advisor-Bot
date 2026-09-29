// Personal Finance Advisor Bot - Main Application Script

document.addEventListener('DOMContentLoaded', function () {
    // Mobile sidebar toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.app-sidebar');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('show');
        });
    }

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (e) {}
        }, 5000);
    });

    // Mark notification as read
    document.querySelectorAll('.mark-notif-read').forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const notifId = this.dataset.id;
            const notifItem = document.getElementById('notif-item-' + notifId);

            fetch('/notifications/read/' + notifId, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'success' && notifItem) {
                    notifItem.style.opacity = '0.5';
                    this.remove();
                }
            })
            .catch(err => console.error('Error marking notification read:', err));
        });
    });
});

function getCsrfToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    return metaTag ? metaTag.getAttribute('content') : '';
}
