// static/js/components/status-manager.js
// Complete Status Manager and Combination Selector implementations

/**
 * StatusManager - Handles status changes in modal
 */
class StatusManager {
    constructor(statusSelectElement, saveButtonElement, onStatusSave) {
        this.statusSelect = statusSelectElement;
        this.saveButton = saveButtonElement;
        this.onStatusSave = onStatusSave;
        this.originalStatus = '';

        this.bindEvents();
        console.log('📊 StatusManager initialized');
    }

    bindEvents() {
        if (this.statusSelect) {
            this.statusSelect.addEventListener('change', () => this.handleStatusChange());
        }

        if (this.saveButton) {
            this.saveButton.addEventListener('click', () => this.saveStatus());
        }
    }

    setStatus(status) {
        this.originalStatus = status;
        if (this.statusSelect) {
            this.statusSelect.value = status;
        }
        this.hideSaveButton();
    }

    handleStatusChange() {
        const newStatus = this.statusSelect.value;
        
        if (newStatus !== this.originalStatus) {
            this.showSaveButton();
        } else {
            this.hideSaveButton();
        }
    }

    showSaveButton() {
        if (this.saveButton) {
            this.saveButton.style.display = 'inline-flex';
        }
    }

    hideSaveButton() {
        if (this.saveButton) {
            this.saveButton.style.display = 'none';
        }
    }

    saveStatus() {
        const newStatus = this.statusSelect.value;
        this.onStatusSave(newStatus);
        this.originalStatus = newStatus;
    }
}

/**
 * CombinationSelector - Handles combination navigation
 */
class CombinationSelector {
    constructor(selectorElement, tabsElement, editToggleElement, onCombinationChange) {
        this.selector = selectorElement;
        this.tabs = tabsElement;
        this.editToggle = editToggleElement;
        this.onCombinationChange = onCombinationChange;
        this.combinations = [];
        this.activeIndex = 0;
        
        console.log('🔀 CombinationSelector initialized');
    }

    setup(combinations) {
        this.combinations = combinations;
        this.activeIndex = 0;

        if (combinations.length <= 1) {
            if (this.selector) this.selector.style.display = 'none';
            return;
        }

        if (this.selector) this.selector.style.display = 'block';
        this.renderTabs();
    }

    renderTabs() {
        if (!this.tabs) return;

        this.tabs.innerHTML = '';
        
        this.combinations.forEach((combo, index) => {
            const tab = document.createElement('button');
            tab.className = `btn btn-sm ${index === this.activeIndex ? 'btn-primary' : 'btn-secondary'}`;
            
            // Create tab content
            const tabText = `Combination ${combo.combination_number || index + 1}`;
            tab.innerHTML = tabText;
            
            // Add status indicator
            if (combo.status) {
                const statusIcon = document.createElement('i');
                statusIcon.className = `fas ${this.getStatusIcon(combo.status)}`;
                statusIcon.style.marginLeft = '4px';
                statusIcon.style.fontSize = '10px';
                statusIcon.title = combo.status;
                tab.appendChild(statusIcon);
            }
            
            tab.onclick = () => this.selectCombination(index);
            tab.title = `View combination ${combo.combination_number || index + 1} - Status: ${combo.status || 'Unknown'}`;
            
            this.tabs.appendChild(tab);
        });
    }

    selectCombination(index) {
        if (index >= 0 && index < this.combinations.length) {
            this.activeIndex = index;
            this.updateActiveTab();
            this.onCombinationChange(index);
        }
    }

    setActive(index) {
        this.activeIndex = index;
        this.updateActiveTab();
    }

    updateActiveTab() {
        const tabs = this.tabs?.querySelectorAll('button');
        if (!tabs) return;

        tabs.forEach((tab, index) => {
            if (index === this.activeIndex) {
                tab.className = 'btn btn-sm btn-primary';
            } else {
                tab.className = 'btn btn-sm btn-secondary';
            }
        });
    }

    setEditMode(enabled) {
        // Update edit toggle button appearance
        if (this.editToggle) {
            this.editToggle.innerHTML = enabled 
                ? '<i class="fas fa-eye"></i>' 
                : '<i class="fas fa-edit"></i>';
            
            this.editToggle.title = enabled ? 'Exit Edit Mode' : 'Enter Edit Mode';
            
            // Update button style
            this.editToggle.className = enabled 
                ? 'btn btn-sm btn-primary' 
                : 'btn btn-sm btn-secondary';
        }
    }

    getStatusIcon(status) {
        switch (status?.toLowerCase()) {
            case 'approved': return 'fa-check-circle';
            case 'rejected': return 'fa-times-circle';
            case 'in review': 
            default: return 'fa-clock';
        }
    }

    getCurrentCombination() {
        return this.combinations[this.activeIndex];
    }

    getTotalCount() {
        return this.combinations.length;
    }
}

// Export to global scope
window.StatusManager = StatusManager;
window.CombinationSelector = CombinationSelector;

console.log('✅ Status Manager and Combination Selector loaded!');
