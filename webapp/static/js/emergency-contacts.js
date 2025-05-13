// Template Management System
class TemplateManager {
    constructor() {
        this.templates = JSON.parse(localStorage.getItem('emergencyTemplates')) || [
            {
                id: 1,
                title: 'Emergency Help',
                content: 'I need immediate help. This is an emergency. I\'m at [Current Location]. Please contact emergency services.'
            },
            {
                id: 2,
                title: 'Medical Emergency',
                content: 'I\'m having a medical emergency. Please call an ambulance. I\'m at [Current Location]. My medical information is available in my health profile.'
            }
        ];
        this.initializeEventListeners();
        this.renderTemplates();
    }

    initializeEventListeners() {
        // Create New Template Button
        document.querySelector('.btn-add').addEventListener('click', () => this.showTemplateModal());

        // Template Modal Events
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-edit')) {
                const templateCard = e.target.closest('.template-card');
                const templateId = parseInt(templateCard.dataset.templateId);
                this.editTemplate(templateId);
            } else if (e.target.classList.contains('btn-delete')) {
                const templateCard = e.target.closest('.template-card');
                const templateId = parseInt(templateCard.dataset.templateId);
                this.deleteTemplate(templateId);
            } else if (e.target.classList.contains('btn-send')) {
                const templateCard = e.target.closest('.template-card');
                const templateId = parseInt(templateCard.dataset.templateId);
                this.sendTemplate(templateId);
            }
        });
    }

    showTemplateModal(template = null) {
        const modalHtml = `
            <div class="modal fade" id="templateModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${template ? 'Edit' : 'Create New'} Template</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="templateForm">
                                <div class="mb-3">
                                    <label class="form-label">Title</label>
                                    <input type="text" class="form-control" id="templateTitle" required value="${template ? template.title : ''}">
                                </div>
                                <div class="mb-3">
                                    <label class="form-label">Message Content</label>
                                    <textarea class="form-control" id="templateContent" rows="4" required>${template ? template.content : ''}</textarea>
                                </div>
                                ${template ? `<input type="hidden" id="templateId" value="${template.id}">` : ''}
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" id="saveTemplate">Save Template</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Remove existing modal if any
        const existingModal = document.querySelector('#templateModal');
        if (existingModal) {
            existingModal.remove();
        }

        // Add new modal to DOM
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Initialize Bootstrap modal
        const modal = new bootstrap.Modal(document.getElementById('templateModal'));
        modal.show();

        // Save Template Event
        document.getElementById('saveTemplate').addEventListener('click', () => {
            const form = document.getElementById('templateForm');
            if (form.checkValidity()) {
                const title = document.getElementById('templateTitle').value;
                const content = document.getElementById('templateContent').value;
                const templateId = document.getElementById('templateId')?.value;

                if (templateId) {
                    this.updateTemplate(parseInt(templateId), title, content);
                } else {
                    this.createTemplate(title, content);
                }

                modal.hide();
            } else {
                form.reportValidity();
            }
        });
    }

    createTemplate(title, content) {
        const newTemplate = {
            id: Date.now(),
            title,
            content
        };

        this.templates.push(newTemplate);
        this.saveTemplates();
        this.renderTemplates();
        this.showToast('Template created successfully!');
    }

    editTemplate(templateId) {
        const template = this.templates.find(t => t.id === templateId);
        if (template) {
            this.showTemplateModal(template);
        }
    }

    updateTemplate(templateId, title, content) {
        const index = this.templates.findIndex(t => t.id === templateId);
        if (index !== -1) {
            this.templates[index] = { ...this.templates[index], title, content };
            this.saveTemplates();
            this.renderTemplates();
            this.showToast('Template updated successfully!');
        }
    }

    deleteTemplate(templateId) {
        if (confirm('Are you sure you want to delete this template?')) {
            this.templates = this.templates.filter(t => t.id !== templateId);
            this.saveTemplates();
            this.renderTemplates();
            this.showToast('Template deleted successfully!');
        }
    }

    async sendTemplate(templateId) {
        const template = this.templates.find(t => t.id === templateId);
        if (!template) return;

        try {
            const response = await fetch('/send-emergency-message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: this.processTemplateContent(template.content)
                })
            });

            const result = await response.json();
            if (result.success) {
                this.showToast('Emergency message sent to all contacts!');
            } else {
                throw new Error(result.message || 'Failed to send message');
            }
        } catch (error) {
            this.showToast('Error sending message: ' + error.message, 'error');
        }
    }

    processTemplateContent(content) {
        // Replace [Current Location] with actual location
        return content.replace('[Current Location]', 'Current Location (Pending)');
    }

    saveTemplates() {
        localStorage.setItem('emergencyTemplates', JSON.stringify(this.templates));
    }

    renderTemplates() {
        const container = document.querySelector('.templates-container');
        container.innerHTML = this.templates.map(template => `
            <div class="template-card" data-template-id="${template.id}">
                <div class="template-header">
                    <h3>${template.title}</h3>
                    <div class="template-actions">
                        <button class="btn-edit"><i class="fas fa-edit"></i></button>
                        <button class="btn-delete"><i class="fas fa-trash"></i></button>
                    </div>
                </div>
                <div class="template-content">
                    <p>${template.content}</p>
                </div>
                <div class="template-footer">
                    <button class="btn-send">Send to All Contacts</button>
                </div>
            </div>
        `).join('');
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

// Initialize Template Manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TemplateManager();
});
