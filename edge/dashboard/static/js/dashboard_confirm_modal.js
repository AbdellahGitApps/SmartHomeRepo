/* dashboard_confirm_modal.js */
window.DashboardConfirm = {
    show: function(message, options = {}) {
        return new Promise((resolve) => {
            const variant = options.variant || 'primary';
            const confirmText = options.confirmText || 'Confirm';
            const cancelText = options.cancelText || 'Cancel';
            const title = options.title || 'Are you sure?';

            // Create overlay
            const overlay = document.createElement('div');
            overlay.className = 'dashboard-confirm-overlay';

            // Create modal
            const modal = document.createElement('div');
            modal.className = 'dashboard-confirm-modal';

            // Modal content
            modal.innerHTML = `
                <div class="dashboard-confirm-title">${title}</div>
                <div class="dashboard-confirm-message">${message}</div>
                <div class="dashboard-confirm-actions">
                    <button class="dashboard-confirm-btn dashboard-confirm-cancel" id="dc-cancel-btn">${cancelText}</button>
                    <button class="dashboard-confirm-btn dashboard-confirm-confirm ${variant}" id="dc-confirm-btn">${confirmText}</button>
                </div>
            `;

            overlay.appendChild(modal);
            document.body.appendChild(overlay);

            // Force reflow for transition
            overlay.offsetHeight;
            overlay.classList.add('show');

            const cleanup = () => {
                overlay.classList.remove('show');
                setTimeout(() => {
                    if (document.body.contains(overlay)) {
                        document.body.removeChild(overlay);
                    }
                }, 200);
            };

            const handleCancel = () => {
                cleanup();
                resolve(false);
            };

            const handleConfirm = () => {
                cleanup();
                resolve(true);
            };

            const cancelBtn = modal.querySelector('#dc-cancel-btn');
            const confirmBtn = modal.querySelector('#dc-confirm-btn');

            cancelBtn.addEventListener('click', handleCancel);
            confirmBtn.addEventListener('click', handleConfirm);
            
            // Close on backdrop click
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    handleCancel();
                }
            });

            // Close on Escape key
            const handleEsc = (e) => {
                if (e.key === 'Escape') {
                    handleCancel();
                    document.removeEventListener('keydown', handleEsc);
                }
            };
            document.addEventListener('keydown', handleEsc);
            
            // Focus cancel button by default for safety
            cancelBtn.focus();
        });
    }
};
