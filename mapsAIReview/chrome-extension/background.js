// Background service worker for Restaurant Review Scraper extension

// Install event
chrome.runtime.onInstalled.addListener((details) => {
    console.log('Restaurant Review Scraper extension installed');
    
    if (details.reason === 'install') {
        // First time install
        console.log('First time installation');
        
        // Set default settings
        chrome.storage.local.set({
            defaultReviewCount: 50,
            serverUrl: 'http://localhost:5000'
        });
    }
});

// Handle extension icon click (optional additional functionality)
chrome.action.onClicked.addListener((tab) => {
    // This is only called if no popup is defined, but we have a popup
    console.log('Extension icon clicked on tab:', tab.url);
});

// Listen for messages from content scripts or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Background script received message:', request);
    
    switch (request.action) {
        case 'checkServer':
            checkServerStatus().then(sendResponse);
            return true; // Will respond asynchronously
            
        case 'getSettings':
            chrome.storage.local.get(['defaultReviewCount', 'serverUrl'], sendResponse);
            return true;
            
        case 'saveSettings':
            chrome.storage.local.set(request.settings, () => {
                sendResponse({ success: true });
            });
            return true;
            
        default:
            sendResponse({ error: 'Unknown action' });
    }
});

// Check if local server is running
async function checkServerStatus() {
    try {
        const response = await fetch('http://localhost:5000/health', {
            method: 'GET',
            signal: AbortSignal.timeout(5000) // 5 second timeout
        });
        
        return {
            running: response.ok,
            status: response.status
        };
    } catch (error) {
        return {
            running: false,
            error: error.message
        };
    }
}

// Optional: Monitor tab updates to show/hide extension icon
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url) {
        const isGoogleMaps = tab.url.includes('google.com/maps') || tab.url.includes('maps.google.com');
        
        if (isGoogleMaps) {
            // Could update icon to show it's active on Google Maps
            chrome.action.setBadgeText({
                tabId: tabId,
                text: '📍'
            });
            chrome.action.setBadgeBackgroundColor({
                tabId: tabId,
                color: '#4CAF50'
            });
        } else {
            // Clear badge on non-Google Maps pages
            chrome.action.setBadgeText({
                tabId: tabId,
                text: ''
            });
        }
    }
});

// Clean up when tabs are closed
chrome.tabs.onRemoved.addListener((tabId) => {
    console.log('Tab closed:', tabId);
}); 
