// static/js/core/auth.js - Authentication Management Module
class AuthManager {
    constructor(apiService) {
        this.api = apiService;
        this.currentUser = null;
        this.sessionToken = null;
        this.listeners = [];
    }

    /**
     * Subscribe to authentication state changes
     */
    subscribe(callback) {
        this.listeners.push(callback);
        return () => {
            this.listeners = this.listeners.filter(listener => listener !== callback);
        };
    }

    /**
     * Notify all listeners of authentication state changes
     */
    notify() {
        this.listeners.forEach(callback => callback(this.currentUser));
    }

    /**
     * Get current user
     */
    getCurrentUser() {
        return this.currentUser;
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return this.currentUser !== null;
    }

    /**
     * Login with username and password
     */
    async login(username, password) {
        try {
            console.log('🔐 Attempting login...', { username });
            
            const result = await this.api.login(username, password);
            
            if (result.success) {
                console.log('✅ Login successful!');
                
                // Store session token in cookie
                this.sessionToken = result.session_token;
                document.cookie = `session_token=${this.sessionToken}; path=/; max-age=86400`;
                
                // Store user data
                this.currentUser = result.user;
                
                // Notify listeners
                this.notify();
                
                return {
                    success: true,
                    user: this.currentUser
                };
            } else {
                throw new Error(result.message || 'Login failed');
            }
        } catch (error) {
            console.error('❌ Login failed:', error.message);
            throw error;
        }
    }

    /**
     * Logout current user
     */
    async logout() {
        try {
            console.log('🚪 Logging out...');
            
            // Call logout API
            await this.api.logout();
            
            // Clear session data
            this.clearSession();
            
            console.log('✅ Logout successful');
            
            return { success: true };
        } catch (error) {
            console.error('❌ Logout error:', error);
            // Clear session even if API call fails
            this.clearSession();
            throw error;
        }
    }

    /**
     * Clear session data
     */
    clearSession() {
        // Clear cookie
        document.cookie = 'session_token=; path=/; max-age=0';
        
        // Clear memory
        this.currentUser = null;
        this.sessionToken = null;
        
        // Notify listeners
        this.notify();
    }

    /**
     * Check if user is already authenticated (on page load)
     */
    async checkAuthStatus() {
        try {
            console.log('🔍 Checking authentication status...');
            
            const result = await this.api.getCurrentUser();
            
            if (result.success && result.user) {
                console.log('✅ User already authenticated:', result.user.username);
                this.currentUser = result.user;
                this.notify();
                return true;
            } else {
                console.log('📝 No active session found');
                return false;
            }
        } catch (error) {
            console.log('📝 Authentication check failed, assuming not logged in');
            this.clearSession();
            return false;
        }
    }

    /**
     * Get user display name
     */
    getUserDisplayName() {
        if (!this.currentUser) return 'Guest';
        return this.currentUser.full_name || this.currentUser.username || 'User';
    }

    /**
     * Get user role
     */
    getUserRole() {
        return this.currentUser?.role || 'user';
    }

    /**
     * Check if user has specific role
     */
    hasRole(role) {
        return this.getUserRole() === role;
    }

    /**
     * Check if user is admin
     */
    isAdmin() {
        return this.hasRole('admin');
    }

    /**
     * Get session info for debugging
     */
    getSessionInfo() {
        return {
            isAuthenticated: this.isAuthenticated(),
            user: this.currentUser,
            sessionToken: this.sessionToken ? 'Present' : 'None',
            role: this.getUserRole()
        };
    }
}

// Session storage utilities
class SessionStorage {
    /**
     * Store data in session storage with expiration
     */
    static setItem(key, value, expirationMinutes = 60) {
        const expirationTime = Date.now() + (expirationMinutes * 60 * 1000);
        const item = {
            value: value,
            expiration: expirationTime
        };
        try {
            localStorage.setItem(key, JSON.stringify(item));
        } catch (error) {
            console.warn('SessionStorage not available, using memory storage');
        }
    }

    /**
     * Get data from session storage
     */
    static getItem(key) {
        try {
            const item = localStorage.getItem(key);
            if (!item) return null;

            const parsedItem = JSON.parse(item);
            
            // Check if expired
            if (Date.now() > parsedItem.expiration) {
                localStorage.removeItem(key);
                return null;
            }
            
            return parsedItem.value;
        } catch (error) {
            console.warn('SessionStorage not available');
            return null;
        }
    }

    /**
     * Remove item from session storage
     */
    static removeItem(key) {
        try {
            localStorage.removeItem(key);
        } catch (error) {
            console.warn('SessionStorage not available');
        }
    }

    /**
     * Clear all session storage
     */
    static clear() {
        try {
            localStorage.clear();
        } catch (error) {
            console.warn('SessionStorage not available');
        }
    }
}

// Form validation utilities
class AuthValidation {
    /**
     * Validate username
     */
    static validateUsername(username) {
        if (!username || username.trim().length === 0) {
            return { valid: false, message: 'Username is required' };
        }
        
        if (username.length < 3) {
            return { valid: false, message: 'Username must be at least 3 characters' };
        }
        
        if (username.length > 50) {
            return { valid: false, message: 'Username must be less than 50 characters' };
        }
        
        return { valid: true };
    }

    /**
     * Validate password
     */
    static validatePassword(password) {
        if (!password || password.length === 0) {
            return { valid: false, message: 'Password is required' };
        }
        
        if (password.length < 6) {
            return { valid: false, message: 'Password must be at least 6 characters' };
        }
        
        return { valid: true };
    }

    /**
     * Validate login form
     */
    static validateLoginForm(username, password) {
        const usernameValidation = this.validateUsername(username);
        if (!usernameValidation.valid) {
            return usernameValidation;
        }
        
        const passwordValidation = this.validatePassword(password);
        if (!passwordValidation.valid) {
            return passwordValidation;
        }
        
        return { valid: true };
    }
}

// Export classes
window.AuthManager = AuthManager;
window.SessionStorage = SessionStorage;
window.AuthValidation = AuthValidation;

console.log('🔐 Authentication module loaded successfully!');
