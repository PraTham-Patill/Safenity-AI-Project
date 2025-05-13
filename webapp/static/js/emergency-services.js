// Emergency Services Call Handler
class EmergencyServicesManager {
    constructor() {
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Add click event listeners to all emergency service call buttons
        document.querySelectorAll('.emergency-services-section .btn-call').forEach(button => {
            button.addEventListener('click', (e) => {
                const serviceCard = e.target.closest('.service-card');
                const phoneLink = serviceCard.querySelector('.service-phone');
                const phoneNumber = phoneLink.textContent.trim().split(' ').pop(); // Get the phone number
                this.initiateCall(phoneNumber);
            });
        });
    }

    initiateCall(phoneNumber) {
        if (phoneNumber) {
            window.location.href = `tel:${phoneNumber}`;
            this.showToast(`Initiating call to ${phoneNumber}...`);
        } else {
            this.showToast('Unable to initiate call. Invalid phone number.', 'danger');
        }
    }

    showToast(message, type = 'success') {
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;

        const toastContainer = document.querySelector('.toast-container') || (() => {
            const container = document.createElement('div');
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(container);
            return container;
        })();

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toast = toastContainer.lastElementChild;
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        toast.addEventListener('hidden.bs.toast', () => toast.remove());
    }
}

// Initialize Emergency Services Manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new EmergencyServicesManager();
});