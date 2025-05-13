/**
 * Emergency Manager - Handles both Personal Emergency Contacts and Emergency Message Templates
 * This file combines and enhances functionality for both systems
 */

// Toast Notification System
class ToastManager {
    static show(message, type = 'success') {
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
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

// Contact Management System
class ContactManager {
    constructor() {
        this.contacts = JSON.parse(localStorage.getItem('emergencyContacts')) || [
            {
                id: 1,
                name: 'Sarah Johnson',
                relation: 'Family Member',
                phone: '(555) 123-4567',
                image: 'https://randomuser.me/api/portraits/women/44.jpg',
                priority: false
            },
            {
                id: 2,
                name: 'Michael Chen',
                relation: 'Friend',
                phone: '(555) 987-6543',
                image: 'https://randomuser.me/api/portraits/men/32.jpg',
                priority: false
            },
            {
                id: 3,
                name: 'David Williams',
                relation: 'Neighbor',
                phone: '(555) 456-7890',
                image: 'https://randomuser.me/api/portraits/men/68.jpg',
                priority: false
            }
        ];
        this.contextMenu = null;
        this.initializeEventListeners();
        this.renderContacts();
    }

    initializeEventListeners() {
        // Add Contact Button
        const addButton = document.querySelector('.personal-contacts-section .btn-add');
        if (addButton) {
            addButton.addEventListener('click', () => this.showContactModal());
        }

        // Contact Actions - Using event delegation for all contact interactions
        document.addEventListener('click', (e) => {
            // Close context menu when clicking outside
            if (this.contextMenu && !e.target.closest('.context-menu') && !e.target.closest('.btn-edit')) {
                this.contextMenu.remove();
                this.contextMenu = null;
            }

            // Handle all button clicks with proper target checking
            const target = e.target;
            const buttonElement = target.closest('button');
            
            if (!buttonElement) return;
            
            const contactCard = buttonElement.closest('.contact-card');
            if (!contactCard) return;
            
            const contactId = parseInt(contactCard.dataset.contactId);
            if (isNaN(contactId)) return;

            // Call button
            if (buttonElement.classList.contains('btn-call')) {
                this.callContact(contactId);
            }
            
            // Message button
            else if (buttonElement.classList.contains('btn-message')) {
                this.messageContact(contactId);
            }
            
            // Edit button (three dots)
            else if (buttonElement.classList.contains('btn-edit')) {
                e.preventDefault();
                e.stopPropagation();
                this.showContextMenu(buttonElement, contactId);
            }
        });

        // Context menu item clicks
        document.addEventListener('click', (e) => {
            if (e.target.closest('.edit-contact')) {
                const contactId = parseInt(e.target.closest('.context-menu').dataset.contactId);
                if (!isNaN(contactId)) {
                    this.editContact(contactId);
                    if (this.contextMenu) {
                        this.contextMenu.remove();
                        this.contextMenu = null;
                    }
                }
            } else if (e.target.closest('.delete-contact')) {
                const contactId = parseInt(e.target.closest('.context-menu').dataset.contactId);
                if (!isNaN(contactId)) {
                    this.deleteContact(contactId);
                    if (this.contextMenu) {
                        this.contextMenu.remove();
                        this.contextMenu = null;
                    }
                }
            }
        });

        // Add Contact Form Submission
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('save-contact')) {
                const form = document.getElementById('addContactForm');
                if (form && form.checkValidity()) {
                    const contactId = document.getElementById('contactId')?.value;
                    const name = document.getElementById('contactName').value;
                    const relation = document.getElementById('contactRelation').value;
                    const phone = document.getElementById('contactPhone').value;
                    const priority = document.getElementById('priorityContact').checked;
                    
                    if (contactId) {
                        this.updateContact(parseInt(contactId), name, relation, phone, priority);
                    } else {
                        this.addContact(name, relation, phone, priority);
                    }
                    
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addContactModal'));
                    if (modal) modal.hide();
                } else if (form) {
                    form.reportValidity();
                }
            }
        });
    }

    showContactModal(contact = null) {
        // Remove existing modal if any
        const existingModal = document.getElementById('addContactModal');
        if (existingModal) {
            const bsModal = bootstrap.Modal.getInstance(existingModal);
            if (bsModal) bsModal.dispose();
            existingModal.remove();
        }

        // Create modal
        const modalHtml = `
            <div class="modal fade" id="addContactModal" tabindex="-1" aria-labelledby="addContactModalLabel" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="addContactModalLabel">${contact ? 'Edit' : 'Add'} Emergency Contact</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <form id="addContactForm">
                                <div class="mb-3">
                                    <label for="contactName" class="form-label">Name</label>
                                    <input type="text" class="form-control" id="contactName" required value="${contact ? contact.name : ''}">
                                </div>
                                <div class="mb-3">
                                    <label for="contactRelation" class="form-label">Relationship</label>
                                    <input type="text" class="form-control" id="contactRelation" required value="${contact ? contact.relation : ''}" placeholder="e.g. Family, Friend, Neighbor, etc.">
                                </div>
                                <div class="mb-3">
                                    <label for="contactPhone" class="form-label">Phone Number</label>
                                    <input type="tel" class="form-control" id="contactPhone" required value="${contact ? contact.phone : ''}">
                                </div>
                                <div class="mb-3">
                                    <label for="contactImage" class="form-label">Contact Image</label>
                                    <input type="file" class="form-control" id="contactImage" accept="image/*">
                                    ${contact && contact.image ? `
                                    <div class="mt-2">
                                        <img src="${contact.image}" alt="Current contact image" class="img-thumbnail" style="max-height: 100px;">
                                        <p class="form-text">Current image will be kept if no new image is selected</p>
                                    </div>` : ''}
                                </div>
                                <div class="mb-3 form-check">
                                    <input type="checkbox" class="form-check-input" id="priorityContact" ${contact && contact.priority ? 'checked' : ''}>
                                    <label class="form-check-label" for="priorityContact">Priority Contact</label>
                                </div>
                                ${contact ? `<input type="hidden" id="contactId" value="${contact.id}">` : ''}
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary save-contact">Save Contact</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Show modal
        const modal = document.getElementById('addContactModal');
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }

    showContextMenu(button, contactId) {
        // Remove existing context menu
        if (this.contextMenu) {
            this.contextMenu.remove();
            this.contextMenu = null;
        }

        // Create context menu
        const rect = button.getBoundingClientRect();
        const menuHtml = `
            <div class="context-menu" style="top: ${rect.bottom + window.scrollY}px; left: ${rect.left + window.scrollX - 150}px;" data-contact-id="${contactId}">
                <div class="context-menu-item edit-contact">
                    <i class="fas fa-edit"></i> Edit Contact
                </div>
                <div class="context-menu-item delete-contact">
                    <i class="fas fa-trash"></i> Delete Contact
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', menuHtml);
        this.contextMenu = document.querySelector('.context-menu');
    }

    addContact(name, relation, phone, priority) {
        const imageInput = document.getElementById('contactImage');
        const file = imageInput.files[0];
        
        // Create contact object without image first
        const newContact = {
            id: Date.now(),
            name,
            relation,
            phone,
            priority,
            // Default image if no file is selected
            image: `https://via.placeholder.com/150?text=${name.charAt(0)}`
        };
        
        if (file) {
            // If file is selected, read it as data URL
            const reader = new FileReader();
            reader.onload = (e) => {
                // Update contact with the image data URL
                newContact.image = e.target.result;
                
                // Save and render after image is loaded
                this.contacts.push(newContact);
                this.saveContacts();
                this.renderContacts();
                ToastManager.show('Contact added successfully!');
            };
            reader.readAsDataURL(file);
        } else {
            // If no file, save contact with default image
            this.contacts.push(newContact);
            this.saveContacts();
            this.renderContacts();
            ToastManager.show('Contact added successfully!');
        }
    }

    editContact(contactId) {
        const contact = this.contacts.find(c => c.id === contactId);
        if (contact) {
            this.showContactModal(contact);
        }
    }

    updateContact(contactId, name, relation, phone, priority) {
        const index = this.contacts.findIndex(c => c.id === contactId);
        if (index !== -1) {
            const imageInput = document.getElementById('contactImage');
            const file = imageInput.files[0];
            
            // If no new image is uploaded, keep the existing image
            if (!file) {
                this.contacts[index] = {
                    ...this.contacts[index],
                    name,
                    relation,
                    phone,
                    priority
                };
                this.saveContacts();
                this.renderContacts();
                ToastManager.show('Contact updated successfully!');
                return;
            }
            
            // If new image is uploaded, read it as data URL
            const reader = new FileReader();
            reader.onload = (e) => {
                this.contacts[index] = {
                    ...this.contacts[index],
                    name,
                    relation,
                    phone,
                    priority,
                    image: e.target.result
                };
                this.saveContacts();
                this.renderContacts();
                ToastManager.show('Contact updated successfully!');
            };
            reader.readAsDataURL(file);
        }
    }

    deleteContact(contactId) {
        if (confirm('Are you sure you want to delete this contact?')) {
            this.contacts = this.contacts.filter(c => c.id !== contactId);
            this.saveContacts();
            this.renderContacts();
            ToastManager.show('Contact deleted successfully!');
        }
    }

    callContact(contactId) {
        const contact = this.contacts.find(c => c.id === contactId);
        if (contact) {
            window.location.href = `tel:${contact.phone.replace(/[^0-9]/g, '')}`;
        }
    }

    messageContact(contactId) {
        const contact = this.contacts.find(c => c.id === contactId);
        if (contact) {
            window.location.href = `sms:${contact.phone.replace(/[^0-9]/g, '')}`;
        }
    }

    saveContacts() {
        localStorage.setItem('emergencyContacts', JSON.stringify(this.contacts));
    }

    renderContacts() {
        const container = document.querySelector('.contacts-grid');
        if (!container) return;

        if (this.contacts.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-user-friends fa-3x"></i>
                    <h3>No Emergency Contacts</h3>
                    <p>Add your emergency contacts to quickly reach them in case of emergency.</p>
                    <button class="btn-add-empty"><i class="fas fa-plus"></i> Add Contact</button>
                </div>
            `;
            const addEmptyButton = container.querySelector('.btn-add-empty');
            if (addEmptyButton) {
                addEmptyButton.addEventListener('click', () => this.showContactModal());
            }
        } else {
            container.innerHTML = this.contacts.map(contact => `
                <div class="contact-card ${contact.priority ? 'priority-contact' : ''}" data-contact-id="${contact.id}">
                    <div class="contact-avatar">
                        <img src="${contact.image}" alt="${contact.name}" onerror="this.src='https://via.placeholder.com/75?text=${contact.name.charAt(0)}'">
                    </div>
                    <div class="contact-content">
                        <h3>${contact.name}</h3>
                        <p class="contact-relation">${contact.relation}</p>
                        <p class="contact-phone">${contact.phone}</p>
                    </div>
                    <div class="contact-actions">
                        <button class="btn-call" title="Call Contact"><i class="fas fa-phone-alt"></i></button>
                        <button class="btn-message" title="Message Contact"><i class="fas fa-comment"></i></button>
                        <button class="btn-edit" title="More Options"><i class="fas fa-ellipsis-v"></i></button>
                    </div>
                </div>
            `).join('');
        }
    }
}

// Template Management System
class TemplateManager {
    constructor() {
        // Initialize templates from localStorage or use default templates
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
        const addButton = document.querySelector('.message-template-section .btn-add');
        if (addButton) {
            addButton.addEventListener('click', () => this.showTemplateModal());
        }

        // Template Actions - Using event delegation for dynamically created elements
        document.addEventListener('click', (e) => {
            const target = e.target;
            const buttonElement = target.closest('button');
            
            if (!buttonElement) return;
            
            const templateCard = buttonElement.closest('.template-card');
            if (!templateCard) return;
            
            const templateId = parseInt(templateCard.dataset.templateId);
            if (isNaN(templateId)) return;
            
            if (buttonElement.classList.contains('btn-edit')) {
                this.editTemplate(templateId);
            } else if (buttonElement.classList.contains('btn-delete')) {
                this.deleteTemplate(templateId);
            } else if (buttonElement.classList.contains('btn-send')) {
                this.sendTemplate(templateId);
            }
        });
    }

    showTemplateModal(template = null) {
        // Remove existing modal if any
        const existingModal = document.getElementById('templateModal');
        if (existingModal) {
            const bsModal = bootstrap.Modal.getInstance(existingModal);
            if (bsModal) bsModal.dispose();
            existingModal.remove();
        }

        const modalHtml = `
            <div class="modal fade" id="templateModal" tabindex="-1" aria-labelledby="templateModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="templateModalLabel">${template ? 'Edit' : 'Create New'} Template</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <form id="templateForm">
                                <div class="mb-3">
                                    <label for="templateTitle" class="form-label">Title</label>
                                    <input type="text" class="form-control" id="templateTitle" required value="${template ? template.title : ''}">
                                </div>
                                <div class="mb-3">
                                    <label for="templateContent" class="form-label">Message Content</label>
                                    <textarea class="form-control" id="templateContent" rows="4" required>${template ? template.content : ''}</textarea>
                                    <div class="form-text">Use [Current Location] as a placeholder for your location</div>
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
        ToastManager.show('Template created successfully!');
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
            ToastManager.show('Template updated successfully!');
        }
    }

    deleteTemplate(templateId) {
        if (confirm('Are you sure you want to delete this template?')) {
            this.templates = this.templates.filter(t => t.id !== templateId);
            this.saveTemplates();
            this.renderTemplates();
            ToastManager.show('Template deleted successfully!');
        }
    }

    async sendTemplate(templateId) {
        const template = this.templates.find(t => t.id === templateId);
        if (!template) return;

        // Get user's current location
        try {
            let locationText = 'Unknown Location';
            
            try {
                if (navigator.geolocation) {
                    const position = await new Promise((resolve, reject) => {
                        navigator.geolocation.getCurrentPosition(resolve, reject, {
                            enableHighAccuracy: true,
                            timeout: 5000,
                            maximumAge: 0
                        });
                    });
                    
                    const { latitude, longitude } = position.coords;
                    locationText = `Latitude: ${latitude}, Longitude: ${longitude}`;
                }
            } catch (error) {
                console.error('Error getting location:', error);
            }
            
            // Process the template content, replacing placeholders
            const processedContent = template.content.replace(/\[Current Location\]/g, locationText);
            
            // Get contacts from localStorage
            const contacts = JSON.parse(localStorage.getItem('emergencyContacts')) || [];
            
            if (contacts.length === 0) {
                ToastManager.show('No emergency contacts found. Please add contacts first.', 'danger');
                return;
            }
            
            // In a real app, you would send SMS messages to all contacts
            // For this demo, we'll simulate it with a success message
            ToastManager.show(`Emergency message sent to ${contacts.length} contacts!`);
            
            // For demonstration, open SMS app with the first contact
            if (contacts.length > 0) {
                const firstContact = contacts[0];
                window.location.href = `sms:${firstContact.phone.replace(/[^0-9]/g, '')}?body=${encodeURIComponent(processedContent)}`;
            }
        } catch (error) {
            console.error('Error sending template:', error);
            ToastManager.show('Error sending message: ' + error.message, 'danger');
        }
    }

    saveTemplates() {
        localStorage.setItem('emergencyTemplates', JSON.stringify(this.templates));
    }

    renderTemplates() {
        const container = document.querySelector('.templates-container');
        if (!container) return;

        if (this.templates.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-comment-dots fa-3x"></i>
                    <h3>No Message Templates</h3>
                    <p>Create message templates to quickly send in case of an emergency.</p>
                    <button class="btn-add-empty"><i class="fas fa-plus"></i> Create First Template</button>
                </div>
            `;
            
            // Add event listener to the empty state add button
            const addEmptyButton = container.querySelector('.btn-add-empty');
            if (addEmptyButton) {
                addEmptyButton.addEventListener('click', () => this.showTemplateModal());
            }
            
            return;
        }

        container.innerHTML = this.templates.map(template => `
            <div class="template-card" data-template-id="${template.id}">
                <div class="template-header">
                    <h3>${template.title}</h3>
                    <div class="template-actions">
                        <button class="btn-edit" title="Edit Template"><i class="fas fa-edit"></i></button>
                        <button class="btn-delete" title="Delete Template"><i class="fas fa-trash"></i></button>
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
}

// SOS Button Functionality
class SOSManager {
    constructor() {
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        const sosButton = document.getElementById('sos-button');
        if (sosButton) {
            sosButton.addEventListener('click', () => this.activateSOS());
        }
    }

    async activateSOS() {
        try {
            // Get user's current location
            let locationText = 'Unknown Location';
            
            try {
                if (navigator.geolocation) {
                    const position = await new Promise((resolve, reject) => {
                        navigator.geolocation.getCurrentPosition(resolve, reject, {
                            enableHighAccuracy: true,
                            timeout: 5000,
                            maximumAge: 0
                        });
                    });
                    
                    const { latitude, longitude } = position.coords;
                    locationText = `Latitude: ${latitude}, Longitude: ${longitude}`;
                }
            } catch (error) {
                console.error('Error getting location:', error);
            }
            
            // Get contacts from localStorage
            const contacts = JSON.parse(localStorage.getItem('emergencyContacts')) || [];
            
            if (contacts.length === 0) {
                ToastManager.show('No emergency contacts found. Please add contacts first.', 'danger');
                return;
            }
            
            // Get the first template or create a default one
            const templates = JSON.parse(localStorage.getItem('emergencyTemplates')) || [];
            let messageContent = 'EMERGENCY! I need help immediately. I\'m at ' + locationText;
            
            if (templates.length > 0) {
                messageContent = templates[0].content.replace(/\[Current Location\]/g, locationText);
            }
            
            // Show SOS activated message
            ToastManager.show('SOS Emergency activated! Contacting your emergency contacts...');
            
            // Animate the SOS button
            const sosButton = document.getElementById('sos-button');
            if (sosButton) {
                sosButton.classList.add('sos-active');
                setTimeout(() => {
                    sosButton.classList.remove('sos-active');
                }, 5000);
            }
            
            // In a real app, you would send SMS messages to all contacts
            // For this demo, we'll simulate it with a success message after a delay
            setTimeout(() => {
                ToastManager.show(`Emergency alert sent to ${contacts.length} contacts with your location!`);
                
                // For demonstration, open SMS app with the first contact
                if (contacts.length > 0) {
                    const firstContact = contacts[0];
                    window.location.href = `sms:${firstContact.phone.replace(/[^0-9]/g, '')}?body=${encodeURIComponent(messageContent)}`;
                }
            }, 1500);
            
        } catch (error) {
            console.error('Error in SOS activation:', error);
            ToastManager.show('Error activating SOS: ' + error.message, 'danger');
        }
    }
}

// Add CSS for context menu and other dynamic elements
const addDynamicStyles = () => {
    const styleId = 'emergency-manager-styles';
    if (document.getElementById(styleId)) return;
    
    const dynamicStyles = document.createElement('style');
    dynamicStyles.id = styleId;
    dynamicStyles.textContent = `
        .context-menu {
            position: absolute;
            background: rgba(20, 20, 20, 0.9);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            z-index: 1050;
            overflow: hidden;
            min-width: 180px;
        }
        
        .context-menu-item {
            padding: 12px 15px;
            color: white;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
        }
        
        .context-menu-item:hover {
            background: #00d8ff;
        }
        
        .context-menu-item i {
            margin-right: 10px;
            width: 16px;
            text-align: center;
        }
        
        .delete-contact {
            color: #ff5555;
        }
        
        .delete-contact:hover {
            background: #ff5555;
            color: white;
        }
        
        .contact-content h3 {
            font-size: 1.4rem;
            margin-bottom: 8px;
            color: white;
            font-weight: 600;
        }
        
        .contact-relation {
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.9rem;
            margin-bottom: 5px;
        }
        
        .contact-phone {
            color: #00d8ff;
            font-size: 1.1rem;
            font-weight: 600;
            margin: 0;
        }
        
        .priority-contact {
            border-left: 3px solid #ff9500;
            position: relative;
        }
        
        .priority-contact::after {
            content: '⭐';
            position: absolute;
            top: 10px;
            right: 10px;
            font-size: 14px;
            opacity: 0.7;
        }
        
        .sos-active {
            animation: sos-pulse 0.5s infinite alternate;
        }
        
        @keyframes sos-pulse {
            0% {
                transform: scale(1);
                box-shadow: 0 8px 25px rgba(255, 0, 0, 0.4);
            }
            100% {
                transform: scale(1.1);
                box-shadow: 0 15px 40px rgba(255, 0, 0, 0.7);
            }
        }
    `;
    document.head.appendChild(dynamicStyles);
};

// Initialize all managers when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Add dynamic styles
    addDynamicStyles();
    
    // Initialize managers
    new ContactManager();
    new TemplateManager();
    new SOSManager();
});