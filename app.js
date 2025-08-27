// static/js/app.js - COMPLETE FINAL VERSION
class PolicyManagementApp {
    constructor() {
        console.log('🚀 Policy Management App initializing...');
        
        // Initialize core services
        this.api = new EndorsementAPI();
        this.auth = new AuthManager(this.api);
        
        // Modal will be initialized after DOM is ready
        this.endorsementModal = null;
        
        // Application state
        this.state = {
            endorsements: [],
            allEndorsementTypes: [],
            filters: {
                status: '',
                type: '',
                search: '',
                sortBy: 'created_at',
                sortOrder: 'DESC'
            }
        };
        
        // DOM elements will be initialized after DOM is ready
        this.elements = {};
        
        // Bind methods to preserve context
        this.handleLogin = this.handleLogin.bind(this);
        this.handleLogout = this.handleLogout.bind(this);
        this.handleFileUpload = this.handleFileUpload.bind(this);
        this.handleJsonUpload = this.handleJsonUpload.bind(this);
        this.handleSearch = this.handleSearch.bind(this);
        this.loadEndorsements = this.loadEndorsements.bind(this);
        this.viewEndorsementCombinations = this.viewEndorsementCombinations.bind(this);
    }

    /**
     * Initialize the application
     */
    async init() {
        console.log('🔧 App initialization starting...');
        
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeApp());
        } else {
            this.initializeApp();
        }
    }

    /**
     * Initialize app after DOM is ready
     */
    async initializeApp() {
        try {
            console.log('🎯 DOM ready, initializing app components...');
            
            // Initialize DOM elements
            this.initializeElements();
            
            // Initialize modal components - CRITICAL FIX
            this.initializeModal();
            
            // Set up authentication state management
            this.setupAuthenticationHandlers();
            
            // Bind UI event listeners
            this.bindEventListeners();
            
            // Check if user is already authenticated
            const isAuthenticated = await this.auth.checkAuthStatus();
            
            if (isAuthenticated) {
                this.showApp();
                await this.initializeDashboard();
            } else {
                this.showLogin();
            }
            
            // Start periodic tasks
            this.startPeriodicTasks();
            
            console.log('✅ App initialization complete!');
            
        } catch (error) {
            console.error('❌ App initialization failed:', error);
            UIUtils.showMessage('Application initialization failed: ' + error.message, true);
        }
    }

    /**
     * Initialize modal components - NEW METHOD
     */
    initializeModal() {
        console.log('🔗 Initializing modal integration...');
        
        const modalElement = document.getElementById('endorsementModal');
        
        if (modalElement && window.EndorsementModal) {
            this.endorsementModal = new EndorsementModal(modalElement, this.api);
            
            // Set data change callback to refresh main list
            this.endorsementModal.setDataChangeCallback(() => {
                console.log('🔄 Modal triggered data refresh');
                this.loadEndorsements();
            });
            
            console.log('✅ Modal components initialized');
        } else {
            console.warn('⚠️ Modal element or EndorsementModal class not found');
        }
    }

    /**
     * Initialize DOM element references
     */
    initializeElements() {
        console.log('🔍 Initializing DOM elements...');
        
        // Login elements
        this.elements.loginScreen = document.getElementById('loginScreen');
        this.elements.loginForm = document.getElementById('loginForm');
        this.elements.loginError = document.getElementById('loginError');
        this.elements.usernameInput = document.getElementById('username');
        this.elements.passwordInput = document.getElementById('password');
        
        // App elements
        this.elements.appContainer = document.getElementById('appContainer');
        this.elements.currentUserName = document.getElementById('currentUserName');
        this.elements.logoutBtn = document.getElementById('logoutBtn');
        
        // Search and filter elements
        this.elements.searchInput = document.getElementById('searchInput');
        this.elements.statusFilter = document.getElementById('statusFilter');
        this.elements.typeFilter = document.getElementById('typeFilter');
        this.elements.sortBy = document.getElementById('sortBy');
        
        // Upload elements
        this.elements.uploadBtn = document.getElementById('uploadBtn');
        this.elements.fileInput = document.getElementById('fileInput');
        this.elements.jsonUploadBtn = document.getElementById('jsonUploadBtn');
        
        // Endorsements list elements
        this.elements.endorsementsList = document.getElementById('endorsementsList');
        this.elements.loadingState = document.getElementById('loadingState');
        this.elements.emptyState = document.getElementById('emptyState');
        this.elements.endorsementsCount = document.getElementById('endorsementsCount');
        
        // Stats elements
        this.elements.totalEndorsements = document.getElementById('totalEndorsements');
        this.elements.approvedEndorsements = document.getElementById('approvedEndorsements');
        this.elements.pendingEndorsements = document.getElementById('pendingEndorsements');
        this.elements.rejectedEndorsements = document.getElementById('rejectedEndorsements');
        
        // JSON upload modal elements
        this.elements.jsonModal = document.getElementById('jsonUploadModal');
        this.elements.jsonTextArea = document.getElementById('jsonTextArea');
        this.elements.submitJsonUpload = document.getElementById('submitJsonUpload');
        this.elements.cancelJsonUpload = document.getElementById('cancelJsonUpload');
        this.elements.closeJsonModal = document.getElementById('closeJsonModal');
        
        console.log('✅ DOM elements initialized');
    }

    /**
     * Set up authentication state handlers
     */
    setupAuthenticationHandlers() {
        // Subscribe to authentication state changes
        this.auth.subscribe((user) => {
            if (user) {
                this.showApp();
                this.initializeDashboard();
            } else {
                this.showLogin();
            }
        });
    }

    /**
     * Bind all UI event listeners
     */
    bindEventListeners() {
        console.log('🔗 Binding event listeners...');
        
        // Login form
        if (this.elements.loginForm) {
            this.elements.loginForm.addEventListener('submit', this.handleLogin);
        }
        
        // Logout button
        if (this.elements.logoutBtn) {
            this.elements.logoutBtn.addEventListener('click', this.handleLogout);
        }
        
        // Search and filters
        if (this.elements.searchInput) {
            this.elements.searchInput.addEventListener('input', 
                UIUtils.debounce(this.handleSearch, 300)
            );
        }
        
        if (this.elements.statusFilter) {
            this.elements.statusFilter.addEventListener('change', this.loadEndorsements);
        }
        
        if (this.elements.typeFilter) {
            this.elements.typeFilter.addEventListener('change', this.loadEndorsements);
        }
        
        if (this.elements.sortBy) {
            this.elements.sortBy.addEventListener('change', this.loadEndorsements);
        }
        
        // File upload
        if (this.elements.uploadBtn && this.elements.fileInput) {
            this.elements.uploadBtn.addEventListener('click', () => {
                this.elements.fileInput.click();
            });
            
            this.elements.fileInput.addEventListener('change', this.handleFileUpload);
        }
        
        // JSON upload
        if (this.elements.jsonUploadBtn) {
            this.elements.jsonUploadBtn.addEventListener('click', this.showJsonUploadModal.bind(this));
        }
        
        if (this.elements.submitJsonUpload) {
            this.elements.submitJsonUpload.addEventListener('click', this.handleJsonUpload);
        }
        
        if (this.elements.cancelJsonUpload) {
            this.elements.cancelJsonUpload.addEventListener('click', this.closeJsonUploadModal.bind(this));
        }
        
        if (this.elements.closeJsonModal) {
            this.elements.closeJsonModal.addEventListener('click', this.closeJsonUploadModal.bind(this));
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyboardShortcuts.bind(this));
        
        // JSON modal overlay click to close
        if (this.elements.jsonModal) {
            this.elements.jsonModal.addEventListener('click', (e) => {
                if (e.target === this.elements.jsonModal) {
                    this.closeJsonUploadModal();
                }
            });
        }
        
        console.log('✅ Event listeners bound');
    }

    /**
     * Handle login form submission
     */
    async handleLogin(e) {
        e.preventDefault();
        
        const username = this.elements.usernameInput.value.trim();
        const password = this.elements.passwordInput.value;
        
        // Validate inputs
        const validation = AuthValidation.validateLoginForm(username, password);
        if (!validation.valid) {
            this.showLoginError(validation.message);
            return;
        }
        
        try {
            this.hideLoginError();
            await this.auth.login(username, password);
            // Auth state change will trigger showApp automatically
        } catch (error) {
            this.showLoginError(error.message);
        }
    }

    /**
     * Handle logout
     */
    async handleLogout() {
        try {
            await this.auth.logout();
            // Auth state change will trigger showLogin automatically
        } catch (error) {
            console.error('Logout error:', error);
            // Force show login even if logout API fails
            this.showLogin();
        }
    }

    /**
     * Handle search input
     */
    handleSearch() {
        this.state.filters.search = this.elements.searchInput.value.trim();
        this.loadEndorsements();
    }

    /**
     * Handle file upload
     */
    async handleFileUpload(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        console.log('📁 File selected:', file.name, UIUtils.formatFileSize(file.size));
        
        // Validate file type
        const allowedTypes = ['.xlsx', '.xls', '.json'];
        if (!UIUtils.isValidFileType(file, allowedTypes)) {
            UIUtils.showMessage(`Invalid file type. Allowed: ${allowedTypes.join(', ')}`, true);
            return;
        }
        
        try {
            const result = await this.api.uploadFile(file);
            
            if (result.success) {
                UIUtils.showMessage(`${result.message} (${result.data.combinations_created} combinations created)`);
                await this.loadEndorsements();
                await this.loadEndorsementTypes();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            UIUtils.showMessage('Upload failed: ' + error.message, true);
        } finally {
            // Clear file input
            this.elements.fileInput.value = '';
        }
    }

    /**
     * Handle JSON upload
     */
    async handleJsonUpload() {
        const jsonText = this.elements.jsonTextArea.value.trim();
        
        if (!jsonText) {
            UIUtils.showMessage('Please enter JSON data', true);
            return;
        }
        
        // Validate JSON format
        const validation = DataUtils.validateJSON(jsonText);
        if (!validation.valid) {
            UIUtils.showMessage(validation.message, true);
            return;
        }
        
        try {
            const result = await this.api.uploadJsonData(jsonText);
            
            if (result.success) {
                UIUtils.showMessage(`${result.message} (${result.data.combinations_created} combinations created)`);
                this.closeJsonUploadModal();
                await this.loadEndorsements();
                await this.loadEndorsementTypes();
            } else {
                throw new Error(result.message);
            }
        } catch (error) {
            UIUtils.showMessage('JSON upload failed: ' + error.message, true);
        }
    }

    /**
     * Handle keyboard shortcuts
     */
    handleKeyboardShortcuts(e) {
        // ESC key to close modals
        if (e.key === 'Escape') {
            if (this.endorsementModal && this.endorsementModal.modal && this.endorsementModal.modal.style.display === 'flex') {
                this.endorsementModal.close();
            } else if (this.elements.jsonModal && this.elements.jsonModal.style.display === 'flex') {
                this.closeJsonUploadModal();
            }
        }
        
        // Ctrl+Enter in JSON textarea to submit
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && 
            e.target === this.elements.jsonTextArea) {
            this.handleJsonUpload();
        }
    }

    /**
     * Load endorsements from API
     */
    async loadEndorsements() {
        try {
            console.log('📋 Loading endorsements...');
            
            UIUtils.showLoading(this.elements.loadingState, true);
            UIUtils.toggleVisibility(this.elements.emptyState, false);
            
            // Collect current filter values
            const filters = {
                status: this.elements.statusFilter?.value || '',
                endorsement_type: this.elements.typeFilter?.value || '',
                search_term: this.state.filters.search || '',
                sort_by: this.elements.sortBy?.value || 'created_at',
                sort_order: 'DESC',
                grouped: true,
                limit: 100
            };
            
            const result = await this.api.getEndorsements(filters);
            
            if (result.success) {
                this.state.endorsements = result.data || [];
                this.renderEndorsements();
                this.updateStats();
                this.updateCount();
                console.log(`✅ Loaded ${this.state.endorsements.length} endorsements`);
            } else {
                throw new Error(result.message || 'Failed to load endorsements');
            }
            
        } catch (error) {
            console.error('❌ Failed to load endorsements:', error);
            UIUtils.showMessage('Failed to load endorsements: ' + error.message, true);
            this.state.endorsements = [];
            this.renderEndorsements();
        } finally {
            UIUtils.showLoading(this.elements.loadingState, false);
        }
    }

    /**
     * Load endorsement types for filter dropdown
     */
    async loadEndorsementTypes() {
        try {
            const result = await this.api.getEndorsementTypes();
            
            if (result.success) {
                this.state.allEndorsementTypes = result.data || [];
                this.populateTypeFilter();
                console.log(`✅ Loaded ${this.state.allEndorsementTypes.length} endorsement types`);
            }
        } catch (error) {
            console.error('❌ Failed to load endorsement types:', error);
        }
    }

    /**
     * Populate endorsement type filter dropdown
     */
    populateTypeFilter() {
        if (!this.elements.typeFilter) return;
        
        this.elements.typeFilter.innerHTML = '<option value="">All Types</option>';
        
        this.state.allEndorsementTypes.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            this.elements.typeFilter.appendChild(option);
        });
    }

    /**
     * Render endorsements list
     */
    renderEndorsements() {
        if (!this.elements.endorsementsList) return;
        
        if (this.state.endorsements.length === 0) {
            this.elements.endorsementsList.innerHTML = '';
            UIUtils.toggleVisibility(this.elements.emptyState, true);
            return;
        }
        
        UIUtils.toggleVisibility(this.elements.emptyState, false);
        
        const html = this.state.endorsements.map(endorsement => {
            // Escape values for safe HTML
            const policyNum = (endorsement.policy_number || 'N/A').replace(/'/g, '&apos;');
            const endoType = (endorsement.endorsement_type || 'Unknown Type').replace(/'/g, '&apos;');
            
            return `
                <div class="endorsement-item" onclick="app.viewEndorsementCombinations('${policyNum}', '${endoType}')">
                    <div class="endorsement-main">
                        <div class="endorsement-policy">Policy #${endorsement.policy_number || 'N/A'}</div>
                        <div class="endorsement-type">${endorsement.endorsement_type || 'Unknown Type'}</div>
                        <div class="endorsement-meta">Version: ${endorsement.endorsement_version || 'N/A'} • Created: ${DateUtils.formatDate(endorsement.created_at)}</div>
                    </div>
                    <div style="color: var(--text-secondary); font-size: 13px;">${endorsement.concepto_id || 'N/A'}</div>
                    <div style="color: var(--text-secondary); font-size: 13px;">${endorsement.endorsement_validity || 'N/A'}</div>
                    <div style="color: var(--text-tertiary); font-size: 12px;">${DateUtils.formatDate(endorsement.updated_at)}</div>
                    <div>
                        <span class="combination-badge">${endorsement.combination_count || 1} combinations</span>
                    </div>
                    <div>
                        <span class="status-badge status-${DataUtils.getStatusClass(endorsement.status)}">
                            <i class="fas ${DataUtils.getStatusIcon(endorsement.status)}"></i>
                            ${endorsement.status}
                        </span>
                    </div>
                </div>
            `;
        }).join('');
        
        this.elements.endorsementsList.innerHTML = html;
    }

    /**
     * Update statistics dashboard
     */
    updateStats() {
        const total = this.state.endorsements.length;
        const approved = this.state.endorsements.filter(e => e.status === 'Approved').length;
        const pending = this.state.endorsements.filter(e => e.status === 'In Review').length;
        const rejected = this.state.endorsements.filter(e => e.status === 'Rejected').length;
        
        // Animate counter updates
        if (this.elements.totalEndorsements) {
            UIUtils.animateCounter(this.elements.totalEndorsements, total);
        }
        if (this.elements.approvedEndorsements) {
            UIUtils.animateCounter(this.elements.approvedEndorsements, approved);
        }
        if (this.elements.pendingEndorsements) {
            UIUtils.animateCounter(this.elements.pendingEndorsements, pending);
        }
        if (this.elements.rejectedEndorsements) {
            UIUtils.animateCounter(this.elements.rejectedEndorsements, rejected);
        }
    }

    /**
     * Update endorsements count display
     */
    updateCount() {
        if (this.elements.endorsementsCount) {
            this.elements.endorsementsCount.textContent = `${this.state.endorsements.length} endorsement groups`;
        }
    }

    /**
     * View endorsement combinations - UPDATED with proper modal integration
     */
    async viewEndorsementCombinations(policyNumber, endorsementType) {
        console.log(`👁️ Viewing combinations for Policy ${policyNumber}, Type: ${endorsementType}`);
        
        if (!this.endorsementModal) {
            console.error('❌ Modal not initialized!');
            UIUtils.showMessage('Modal system not ready. Please refresh the page.', true);
            return;
        }
        
        // Use the sophisticated modal system
        try {
            await this.endorsementModal.open(policyNumber, endorsementType);
        } catch (error) {
            console.error('❌ Failed to open modal:', error);
            UIUtils.showMessage('Failed to open endorsement details: ' + error.message, true);
        }
    }

    /**
     * Show login screen
     */
    showLogin() {
        console.log('📱 Showing login screen');
        UIUtils.toggleVisibility(this.elements.loginScreen, true);
        UIUtils.toggleVisibility(this.elements.appContainer, false);
        this.elements.appContainer?.classList.remove('show');
        
        // Clear login form
        if (this.elements.usernameInput) this.elements.usernameInput.value = '';
        if (this.elements.passwordInput) this.elements.passwordInput.value = '';
        this.hideLoginError();
    }

    /**
     * Show main application
     */
    showApp() {
        console.log('📱 Showing main application');
        UIUtils.toggleVisibility(this.elements.loginScreen, false);
        UIUtils.toggleVisibility(this.elements.appContainer, true);
        this.elements.appContainer?.classList.add('show');
        
        // Update user display name
        if (this.elements.currentUserName) {
            this.elements.currentUserName.textContent = this.auth.getUserDisplayName();
        }
    }

    /**
     * Show login error
     */
    showLoginError(message) {
        if (this.elements.loginError) {
            this.elements.loginError.querySelector('span').textContent = message;
            this.elements.loginError.style.display = 'flex';
        }
    }

    /**
     * Hide login error
     */
    hideLoginError() {
        if (this.elements.loginError) {
            this.elements.loginError.style.display = 'none';
        }
    }

    /**
     * Initialize dashboard after login
     */
    async initializeDashboard() {
        console.log('📊 Initializing dashboard...');
        
        try {
            await Promise.all([
                this.loadEndorsements(),
                this.loadEndorsementTypes()
            ]);
            
            // Check server time
            this.checkServerTime();
            
            console.log('✅ Dashboard initialized');
        } catch (error) {
            console.error('❌ Dashboard initialization failed:', error);
            UIUtils.showMessage('Failed to load dashboard data: ' + error.message, true);
        }
    }

    /**
     * Show JSON upload modal
     */
    showJsonUploadModal() {
        this.elements.jsonModal.style.display = 'flex';
        this.elements.jsonTextArea.value = '';
        this.elements.jsonTextArea.focus();
    }

    /**
     * Close JSON upload modal
     */
    closeJsonUploadModal() {
        this.elements.jsonModal.style.display = 'none';
        this.elements.jsonTextArea.value = '';
    }

    /**
     * Check server time synchronization
     */
    async checkServerTime() {
        try {
            const result = await this.api.getSystemTime();
            
            if (result.success) {
                const serverData = result.data;
                console.log('🕐 Server Time Info:', serverData);
                
                const statusElement = document.getElementById('serverTimeStatus');
                if (statusElement) {
                    statusElement.textContent = '✅ Synchronized';
                    statusElement.style.color = 'var(--text-primary)';
                }
            }
        } catch (error) {
            console.error('❌ Failed to get server time:', error);
            const statusElement = document.getElementById('serverTimeStatus');
            if (statusElement) {
                statusElement.textContent = '❌ Check Failed';
                statusElement.style.color = 'var(--text-secondary)';
            }
        }
    }

    /**
     * Start periodic tasks
     */
    startPeriodicTasks() {
        // Update time display every second
        setInterval(() => DateUtils.updateCurrentTimeDisplay(), 1000);
        DateUtils.updateCurrentTimeDisplay(); // Initial call
        
        // Check server time every 30 seconds
        setInterval(() => this.checkServerTime(), 30000);
        setTimeout(() => this.checkServerTime(), 2000); // Initial check after 2 seconds
    }

    /**
     * Get application status for debugging
     */
    getStatus() {
        return {
            authenticated: this.auth.isAuthenticated(),
            user: this.auth.getCurrentUser(),
            endorsementsCount: this.state.endorsements.length,
            currentFilters: this.state.filters,
            modalInitialized: !!this.endorsementModal
        };
    }
}

// Initialize the application when script loads
console.log('🚀 App controller loaded, initializing...');

// Create global app instance
window.app = new PolicyManagementApp();

// Start the application
app.init();

console.log('✅ Complete Integration Ready!');
