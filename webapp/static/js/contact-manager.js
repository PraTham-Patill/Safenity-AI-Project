// Contact Management System
class ContactManager {
    constructor() {
        this.contacts = JSON.parse(localStorage.getItem('emergencyContacts')) || [];
        this.initializeEventListeners();
        this.renderContacts();
    }

    initializeEventListeners() {
        // Add New Contact Button
        const addButton = document.querySelector('.personal-contacts-section .btn-add');
        if (addButton) {
            addButton.addEventListener('click', () => this.showContactModal());
        }

        // Contact Actions
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-edit-contact')) {
                const contactCard = e.target.closest('.contact-card');
                const contactId = parseInt(contactCard.dataset.contactId);
                this.editContact(contactId);
            } else if (e.target.classList.contains('btn-delete-contact')) {
                const contactCard = e.target.closest('.contact-card');
                const contactId = parseInt(contactCard.dataset.contactId);
                this.deleteContact(contactId);
            } else if (e.target.classList.contains('btn-call-contact')) {
                const contactCard = e.target.closest('.contact-card');
                const phone = contactCard.dataset.phone;
                if (phone) {
                    window.location.href = `tel:${phone}`;
                }
            }
        });
    }

    showContactModal(contact = null) {
        const modalHtml = `
            <div class="modal fade" id="contactModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${contact ? 'Edit' : 'Add New'} Contact</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="contactForm">
                                <div class="mb-3">
                                    <label class="form-label">Name</label>
                                    <input type="text" class="form-control" id="contactName" required value="${contact ? contact.name : ''}">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Relationship</label>
                                    <input type="text" class="form-control" id="contactRelationship" required value="${contact ? contact.relationship : ''}">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Phone Number</label>
                                    <input type="tel" class="form-control" id="contactPhone" required value="${contact ? contact.phone : ''}">
                                </div>
                                ${contact ? `<input type="hidden" id="contactId" value="${contact.id}">` : ''}
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="saveContact">Save Contact</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if any
        const existingModal = document.querySelector('#contactModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add new modal to DOM
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Initialize Bootstrap modal
        const modal = new bootstrap.Modal(document.getElementById('contactModal'));
        modal.show();

        // Save Contact Event
        document.getElementById('saveContact').addEventListener('click', () => {
            const form = document.getElementById('contactForm');
            if (form.checkValidity()) {
                const name = document.getElementById('contactName').value;
                const relationship = document.getElementById('contactRelationship').value;
                const phone = document.getElementById('contactPhone').value;
                const contactId = document.getElementById('contactId')?.value;

                if (contactId) {
                    this.updateContact(parseInt(contactId), name, relationship, phone);
                } else {
                    this.createContact(name, relationship, phone);
                }

                modal.hide();
            } else {
                form.reportValidity();
            }
        });
    }

    createContact(name, relationship, phone) {
        const newContact = {
            id: Date.now(),
            name,
            relationship,
            phone
        };

        this.contacts.push(newContact);
        this.saveContacts();
        this.renderContacts();
        this.showToast('Contact added successfully!');
    }

    editContact(contactId) {
        const contact = this.contacts.find(c => c.id === contactId);
        if (contact) {
            this.showContactModal(contact);
        }
    }

    updateContact(contactId, name, relationship, phone) {
        const index = this.contacts.findIndex(c => c.id === contactId);
        if (index !== -1) {
            this.contacts[index] = { ...this.contacts[index], name, relationship, phone };
            this.saveContacts();
            this.renderContacts();
            this.showToast('Contact updated successfully!');
        }
    }

    deleteContact(contactId) {
        if (confirm('Are you sure you want to delete this contact?')) {
            this.contacts = this.contacts.filter(c => c.id !== contactId);
            this.saveContacts();
            this.renderContacts();
            this.showToast('Contact deleted successfully!');
        }
    }

    saveContacts() {
        localStorage.setItem('emergencyContacts', JSON.stringify(this.contacts));
    }

    renderContacts() {
        const container = document.querySelector('.contacts-grid');
        if (!container) return;

        container.innerHTML = this.contacts.map(contact => `
            <div class="contact-card" data-contact-id="${contact.id}" data-phone="${contact.phone}">
                <div class="contact-header">
                    <h3>${contact.name}</h3>
                    <div class="contact-actions">
                        <button class="btn-edit-contact"><i class="fas fa-edit"></i></button>
                        <button class="btn-delete-contact"><i class="fas fa-trash"></i></button>
                    </div>
                </div>
                <div class="contact-info">
                    <p><strong>Relationship:</strong> ${contact.relationship}</p>
                    <p><strong>Phone:</strong> ${contact.phone}</p>
                </div>
                <div class="contact-footer">
                    <button class="btn-call-contact">Call Now</button>
                </div>
            </div>
        `).join('') || '<p class="no-contacts">No emergency contacts added yet.</p>';
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

// Initialize Contact Manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ContactManager();
});