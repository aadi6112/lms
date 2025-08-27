// static/js/components/modal.js - COMPLETE FIXED VERSION
/**
 * FieldEditor - Handles field display and editing with global access
 */
class FieldEditor {
    constructor(fieldsGridElement, onFieldChange) {
        this.fieldsGrid = fieldsGridElement;
        this.onFieldChange = onFieldChange;
        this.fields = {};
        this.isEditMode = false;
        
        // CRITICAL FIX: Store global reference for HTML onclick handlers
        window.currentFieldEditor = this;
        
        console.log('📝 FieldEditor initialized with global access');
    }

    displayFields(fieldsData) {
        this.fields = { ...fieldsData };
        this.renderFields();
    }

    renderFields() {
        if (!this.fieldsGrid) return;

        const fieldCount = Object.keys(this.fields).length;

        if (fieldCount === 0) {
            this.fieldsGrid.innerHTML = `
                <div class="empty-state" style="padding: 32px; text-align: center; color: var(--text-secondary);">
                    <i class="fas fa-list-alt" style="font-size: 24px; margin-bottom: 8px; color: var(--text-tertiary);"></i>
                    <p>No fields found</p>
                </div>
            `;
            return;
        }

        const html = Object.entries(this.fields).map(([fieldName, fieldValue]) => {
            const fieldId = this.generateFieldId(fieldName);
            const isEmpty = !fieldValue || fieldValue === '' || fieldValue === 'N/A';
            const safeFieldName = this.escapeForAttribute(fieldName);

            return `
                <div class="field-item" data-field-name="${safeFieldName}">
                    <div class="field-name">${this.formatFieldName(fieldName)}</div>
                    <div class="field-value-container">
                        <div class="field-value ${isEmpty ? 'empty' : ''}" id="${fieldId}_display">
                            ${isEmpty ? 'No data' : this.escapeHtml(String(fieldValue))}
                        </div>
                        <input type="text" class="field-input" id="${fieldId}_input" 
                               value="${this.escapeHtml(String(fieldValue || ''))}" style="display: none;">
                    </div>
                    <i class="fas fa-edit field-edit-icon" 
                       onclick="window.currentFieldEditor.toggleFieldEdit('${safeFieldName}', '${fieldId}')" 
                       style="opacity: 0; cursor: pointer;" 
                       title="Click to edit this field"></i>
                </div>
            `;
        }).join('');

        this.fieldsGrid.innerHTML = html;

        // Bind input events
        this.bindFieldEvents();
    }

    bindFieldEvents() {
        const inputs = this.fieldsGrid.querySelectorAll('.field-input');
        inputs.forEach(input => {
            // Remove existing listeners to prevent duplicates
            const newInput = input.cloneNode(true);
            input.parentNode.replaceChild(newInput, input);
            
            // Add new listeners with proper binding
            newInput.addEventListener('input', () => this.onFieldChange());
            newInput.addEventListener('blur', (e) => this.updateFieldValue(e.target));
            newInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.target.blur();
                } else if (e.key === 'Escape') {
                    this.cancelFieldEdit(e.target);
                }
            });
        });
    }

    toggleFieldEdit(fieldName, fieldId) {
        console.log(`🔄 Toggle edit for field: ${fieldName}`);
        
        const displayEl = document.getElementById(`${fieldId}_display`);
        const inputEl = document.getElementById(`${fieldId}_input`);

        if (!displayEl || !inputEl) {
            console.error('❌ Field elements not found:', fieldId);
            return;
        }

        if (displayEl.style.display === 'none') {
            // Save and show display
            const newValue = inputEl.value.trim();
            displayEl.textContent = newValue || 'No data';
            displayEl.className = `field-value ${!newValue ? 'empty' : ''}`;
            displayEl.style.display = 'block';
            inputEl.style.display = 'none';

            // Update fields data
            this.fields[fieldName] = newValue;
            console.log(`💾 Field updated: ${fieldName} = "${newValue}"`);
            
            // Notify parent of change
            this.onFieldChange();
        } else {
            // Show input for editing
            if (!this.isEditMode) {
                console.log('⚠️ Edit mode not enabled');
                return;
            }
            
            displayEl.style.display = 'none';
            inputEl.style.display = 'block';
            inputEl.focus();
            inputEl.select();
            console.log(`✏️ Editing field: ${fieldName}`);
        }
    }

    updateFieldValue(inputEl) {
        const fieldItem = inputEl.closest('[data-field-name]');
        if (!fieldItem) return;

        const fieldName = fieldItem.getAttribute('data-field-name');
        const fieldId = this.generateFieldId(fieldName);
        
        this.toggleFieldEdit(fieldName, fieldId);
    }

    cancelFieldEdit(inputEl) {
        const fieldItem = inputEl.closest('[data-field-name]');
        if (!fieldItem) return;

        const fieldName = fieldItem.getAttribute('data-field-name');
        const originalValue = this.fields[fieldName];
        
        // Restore original value
        inputEl.value = originalValue || '';
        
        const fieldId = this.generateFieldId(fieldName);
        this.toggleFieldEdit(fieldName, fieldId);
    }

    setEditMode(enabled) {
        console.log(`🎛️ Field editor edit mode: ${enabled ? 'ON' : 'OFF'}`);
        this.isEditMode = enabled;
        
        // Show/hide edit icons
        const editIcons = this.fieldsGrid.querySelectorAll('.field-edit-icon');
        editIcons.forEach(icon => {
            icon.style.opacity = enabled ? '1' : '0';
            icon.style.cursor = enabled ? 'pointer' : 'default';
        });

        if (!enabled) {
            // Reset all fields to display mode
            const inputs = this.fieldsGrid.querySelectorAll('.field-input');
            const displays = this.fieldsGrid.querySelectorAll('.field-value');
            
            inputs.forEach(input => input.style.display = 'none');
            displays.forEach(display => display.style.display = 'block');
        }
    }

    getUpdatedFields() {
        const updatedFields = {};
        
        const fieldItems = this.fieldsGrid.querySelectorAll('[data-field-name]');
        fieldItems.forEach(item => {
            const fieldName = item.getAttribute('data-field-name');
            const input = item.querySelector('.field-input');
            if (input) {
                updatedFields[fieldName] = input.value.trim();
            }
        });

        console.log('📊 Updated fields collected:', Object.keys(updatedFields).length);
        return updatedFields;
    }

    generateFieldId(fieldName) {
        return `field_${fieldName.replace(/[^a-zA-Z0-9]/g, '_')}`;
    }

    formatFieldName(fieldName) {
        return fieldName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    escapeForAttribute(text) {
        return text.replace(/['"\\]/g, '\\$&').replace(/\n/g, '\\n');
    }
}

/**
 * EndorsementModal - Main modal controller
 */
class EndorsementModal {
    constructor(modalElement, api) {
        this.modal = modalElement;
        this.api = api;
        this.isEditMode = false;
        this.hasUnsavedChanges = false;
        this.currentCombinations = [];
        this.currentCombinationIndex = 0;
        this.currentEndorsementId = null;
        this.originalFieldValues = {};

        this.initializeElements();
        this.bindEvents();
        
        console.log('📋 EndorsementModal initialized');
    }

    initializeElements() {
        // Modal structure elements
        this.elements = {
            modal: this.modal,
            title: this.modal.querySelector('#modalTitle'),
            loading: this.modal.querySelector('#modalLoading'),
            content: this.modal.querySelector('#modalContent'),
            closeBtn: this.modal.querySelector('#closeModal'),
            closeModalBtn: this.modal.querySelector('#closeModalBtn'),
            
            // Combination selector elements
            combinationSelector: this.modal.querySelector('#combinationSelector'),
            combinationTabs: this.modal.querySelector('#combinationTabs'),
            editModeToggle: this.modal.querySelector('#editModeToggle'),
            
            // Field editor elements
            statusEditor: this.modal.querySelector('#statusEditor'),
            saveStatusBtn: this.modal.querySelector('#saveStatusBtn'),
            fieldsGrid: this.modal.querySelector('#fieldsGrid'),
            
            // Action buttons
            saveAllBtn: this.modal.querySelector('#saveAllBtn'),
            cancelEditBtn: this.modal.querySelector('#cancelEditBtn'),
            deleteBtn: this.modal.querySelector('#deleteBtn')
        };

        // Initialize sub-components
        this.combinationSelector = new CombinationSelector(
            this.elements.combinationSelector,
            this.elements.combinationTabs,
            this.elements.editModeToggle,
            (index) => this.showCombination(index)
        );

        this.fieldEditor = new FieldEditor(
            this.elements.fieldsGrid,
            () => this.markAsChanged()
        );

        this.statusManager = new StatusManager(
            this.elements.statusEditor,
            this.elements.saveStatusBtn,
            (status) => this.saveStatus(status)
        );
    }

    bindEvents() {
        // Modal close events
        if (this.elements.closeBtn) {
            this.elements.closeBtn.addEventListener('click', () => this.close());
        }
        
        if (this.elements.closeModalBtn) {
            this.elements.closeModalBtn.addEventListener('click', () => this.close());
        }

        // Edit mode toggle
        if (this.elements.editModeToggle) {
            this.elements.editModeToggle.addEventListener('click', () => this.toggleEditMode());
        }

        // Action buttons
        if (this.elements.saveAllBtn) {
            this.elements.saveAllBtn.addEventListener('click', () => this.saveAllChanges());
        }

        if (this.elements.cancelEditBtn) {
            this.elements.cancelEditBtn.addEventListener('click', () => this.cancelChanges());
        }

        if (this.elements.deleteBtn) {
            this.elements.deleteBtn.addEventListener('click', () => this.deleteEndorsement());
        }

        // Close on overlay click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });
    }

    /**
     * Open modal and load endorsement combinations
     */
    async open(policyNumber, endorsementType) {
        console.log(`📋 Opening modal for Policy ${policyNumber}, Type: ${endorsementType}`);
        
        this.modal.style.display = 'flex';
        this.showLoading(true);
        this.setEditMode(false);

        // Update title
        if (this.elements.title) {
            this.elements.title.textContent = `${endorsementType} - Policy #${policyNumber}`;
        }

        try {
            const result = await this.api.getEndorsementCombinations(policyNumber, endorsementType);
            
            if (result.success) {
                this.currentCombinations = result.data;
                this.currentCombinationIndex = 0;
                this.currentEndorsementId = this.currentCombinations[0]?.id;

                this.setupModal();
                this.showCombination(0);
                
                this.showLoading(false);
                this.showContent(true);
            } else {
                throw new Error(result.message || 'Failed to load combinations');
            }
        } catch (error) {
            console.error('❌ Failed to load endorsement:', error);
            UIUtils.showMessage('Failed to load endorsement: ' + error.message, true);
            this.close();
        }
    }

    /**
     * Setup modal after data is loaded
     */
    setupModal() {
        // Setup combination selector
        this.combinationSelector.setup(this.currentCombinations);
        
        // Setup delete button text based on combination count
        this.updateDeleteButton();
    }

    /**
     * Show specific combination
     */
    showCombination(index) {
        if (this.hasUnsavedChanges && !confirm('You have unsaved changes. Are you sure you want to switch combinations?')) {
            return;
        }

        this.currentCombinationIndex = index;
        this.currentEndorsementId = this.currentCombinations[index]?.id;
        const combination = this.currentCombinations[index];

        console.log(`📋 Showing combination ${index + 1} of ${this.currentCombinations.length}`);

        // Update combination selector
        this.combinationSelector.setActive(index);

        // Update status manager
        this.statusManager.setStatus(combination.status || 'In Review');

        // Update field editor
        this.fieldEditor.displayFields(combination.spanish_fields || {});
        this.originalFieldValues = { ...combination.spanish_fields };

        // Reset change tracking
        this.hasUnsavedChanges = false;
        this.updateUI();
    }

    /**
     * Toggle edit mode
     */
    toggleEditMode() {
        this.setEditMode(!this.isEditMode);
    }

    /**
     * Set edit mode state
     */
    setEditMode(enabled) {
        this.isEditMode = enabled;
        
        // Update toggle button
        if (this.elements.editModeToggle) {
            this.elements.editModeToggle.innerHTML = enabled 
                ? '<i class="fas fa-eye"></i>' 
                : '<i class="fas fa-edit"></i>';
        }

        // Update field editor
        this.fieldEditor.setEditMode(enabled);

        // Update combination selector
        this.combinationSelector.setEditMode(enabled);

        this.updateUI();
    }

    /**
     * Mark as changed
     */
    markAsChanged() {
        this.hasUnsavedChanges = true;
        this.updateUI();
    }

    /**
     * Update UI based on current state
     */
    updateUI() {
        // Show/hide action buttons based on edit mode
        if (this.elements.saveAllBtn) {
            this.elements.saveAllBtn.style.display = this.isEditMode && this.hasUnsavedChanges ? 'inline-flex' : 'none';
        }
        
        if (this.elements.cancelEditBtn) {
            this.elements.cancelEditBtn.style.display = this.isEditMode ? 'inline-flex' : 'none';
        }

        if (this.elements.deleteBtn) {
            this.elements.deleteBtn.style.display = this.isEditMode ? 'inline-flex' : 'none';
        }
    }

    /**
     * Save status change
     */
    async saveStatus(newStatus) {
        if (!this.currentEndorsementId) {
            UIUtils.showMessage('No endorsement selected', true);
            return;
        }

        try {
            const currentCombination = this.currentCombinations[this.currentCombinationIndex];
            
            const updateData = {
                policy_number: currentCombination.policy_number,
                endorsement_type: currentCombination.endorsement_type,
                endorsement_version: currentCombination.endorsement_version,
                endorsement_validity: currentCombination.endorsement_validity,
                concepto_id: currentCombination.concepto_id,
                status: newStatus,
                spanish_fields: currentCombination.spanish_fields,
                json_data: currentCombination.json_data
            };

            const result = await this.api.updateEndorsement(this.currentEndorsementId, updateData);

            if (result.success) {
                UIUtils.showMessage(`Status updated to ${newStatus} successfully!`);
                
                // Update current combination
                this.currentCombinations[this.currentCombinationIndex] = result.data;
                
                // Hide save button
                this.statusManager.hideSaveButton();
                
                // Trigger refresh in main app
                this.onDataChanged?.();
            } else {
                throw new Error(result.message || 'Failed to update status');
            }
        } catch (error) {
            console.error('❌ Failed to save status:', error);
            UIUtils.showMessage('Failed to save status: ' + error.message, true);
        }
    }

    /**
     * Save all field changes
     */
    async saveAllChanges() {
        if (!this.currentEndorsementId) {
            UIUtils.showMessage('No endorsement selected', true);
            return;
        }

        try {
            // Get updated fields from field editor
            const updatedFields = this.fieldEditor.getUpdatedFields();
            const currentCombination = this.currentCombinations[this.currentCombinationIndex];

            const updateData = {
                policy_number: currentCombination.policy_number,
                endorsement_type: currentCombination.endorsement_type,
                endorsement_version: currentCombination.endorsement_version,
                endorsement_validity: currentCombination.endorsement_validity,
                concepto_id: currentCombination.concepto_id,
                status: currentCombination.status,
                spanish_fields: updatedFields,
                json_data: updatedFields
            };

            const result = await this.api.updateEndorsement(this.currentEndorsementId, updateData);

            if (result.success) {
                UIUtils.showMessage('Endorsement updated successfully!');

                // Update current combination
                this.currentCombinations[this.currentCombinationIndex] = result.data;

                // Refresh display
                this.fieldEditor.displayFields(result.data.spanish_fields);
                this.originalFieldValues = { ...result.data.spanish_fields };

                // Reset edit mode
                this.setEditMode(false);
                this.hasUnsavedChanges = false;

                // Trigger refresh in main app
                this.onDataChanged?.();
            } else {
                throw new Error(result.message || 'Failed to update endorsement');
            }
        } catch (error) {
            console.error('❌ Failed to save changes:', error);
            UIUtils.showMessage('Failed to save changes: ' + error.message, true);
        }
    }

    /**
     * Cancel changes and revert to original values
     */
    cancelChanges() {
        if (this.hasUnsavedChanges && !confirm('Are you sure you want to discard your changes?')) {
            return;
        }

        // Revert to original values
        this.fieldEditor.displayFields(this.originalFieldValues);
        this.setEditMode(false);
        this.hasUnsavedChanges = false;
    }

    /**
     * Delete endorsement or endorsement group
     */
    async deleteEndorsement() {
        const totalCombinations = this.currentCombinations.length;
        const firstCombination = this.currentCombinations[0];
        const policyNumber = firstCombination.policy_number;
        const endorsementType = firstCombination.endorsement_type;

        const confirmMessage = totalCombinations > 1
            ? `Are you sure you want to delete this ENTIRE endorsement group?\n\n` +
              `• Policy: ${policyNumber}\n` +
              `• Type: ${endorsementType}\n` +
              `• This will DELETE ALL ${totalCombinations} combinations\n\n` +
              `This action cannot be undone!`
            : `Are you sure you want to delete this endorsement?\n\n` +
              `• Policy: ${policyNumber}\n` +
              `• Type: ${endorsementType}\n\n` +
              `This action cannot be undone!`;

        if (!confirm(confirmMessage)) {
            return;
        }

        try {
            let result;
            
            if (totalCombinations > 1) {
                // Delete entire group
                result = await this.api.deleteEndorsementGroup(policyNumber, endorsementType);
            } else {
                // Delete single endorsement
                result = await this.api.deleteEndorsement(this.currentEndorsementId);
            }

            if (result.success) {
                const deletedCount = result.data?.deleted_combinations || 1;
                UIUtils.showMessage(`Successfully deleted ${deletedCount > 1 ? 'endorsement group' : 'endorsement'}!`);
                
                this.close();
                this.onDataChanged?.();
            } else {
                throw new Error(result.message || 'Failed to delete endorsement');
            }
        } catch (error) {
            console.error('❌ Failed to delete endorsement:', error);
            UIUtils.showMessage('Failed to delete endorsement: ' + error.message, true);
        }
    }

    /**
     * Update delete button text based on combination count
     */
    updateDeleteButton() {
        if (!this.elements.deleteBtn) return;

        const totalCombinations = this.currentCombinations.length;
        
        if (totalCombinations > 1) {
            this.elements.deleteBtn.innerHTML = `<i class="fas fa-trash"></i> Delete All ${totalCombinations} Combinations`;
            this.elements.deleteBtn.title = `This will delete all ${totalCombinations} combinations for this endorsement`;
        } else {
            this.elements.deleteBtn.innerHTML = `<i class="fas fa-trash"></i> Delete Endorsement`;
            this.elements.deleteBtn.title = 'Delete this endorsement';
        }
    }

    /**
     * Show/hide loading state
     */
    showLoading(show) {
        if (this.elements.loading) {
            this.elements.loading.style.display = show ? 'flex' : 'none';
        }
    }

    /**
     * Show/hide main content
     */
    showContent(show) {
        if (this.elements.content) {
            this.elements.content.style.display = show ? 'block' : 'none';
        }
    }

    /**
     * Close modal
     */
    close() {
        if (this.hasUnsavedChanges && !confirm('You have unsaved changes. Are you sure you want to close?')) {
            return;
        }

        this.modal.style.display = 'none';
        this.currentCombinations = [];
        this.currentCombinationIndex = 0;
        this.currentEndorsementId = null;
        this.setEditMode(false);
        this.hasUnsavedChanges = false;
    }

    /**
     * Set callback for when data changes (to refresh main list)
     */
    setDataChangeCallback(callback) {
        this.onDataChanged = callback;
    }
}

// Export for use in main app
window.EndorsementModal = EndorsementModal;
window.FieldEditor = FieldEditor;

console.log('✅ Enhanced Modal Components loaded successfully!');
