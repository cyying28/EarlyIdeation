// Content script for Google Maps pages
// This script runs in the context of the Google Maps page

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'getRestaurantData') {
        const data = extractRestaurantData();
        sendResponse(data);
    } else if (request.action === 'getCurrentUrl') {
        sendResponse({ url: window.location.href });
    }
});

// Extract restaurant data from the current page
function extractRestaurantData() {
    try {
        let name = '';
        let rating = '';
        let address = '';
        let reviewCount = '';
        
        // Try multiple selectors for restaurant name
        const nameSelectors = [
            'h1[data-attrid="title"]',
            'h1.x3AX1-LfntMc-header-title-title',
            'h1.DUwDvf',
            '[data-value="title"]',
            'h1',
            '.qrShPb'
        ];
        
        for (const selector of nameSelectors) {
            const element = document.querySelector(selector);
            if (element && element.textContent.trim()) {
                name = element.textContent.trim();
                break;
            }
        }
        
        // Try multiple selectors for rating
        const ratingSelectors = [
            '[data-value="rating"] span',
            '.ceNzKf',
            '.F7nice span[aria-hidden="true"]',
            '[jsaction*="pane.rating.moreReviews"]',
            'span[aria-label*="stars"]'
        ];
        
        for (const selector of ratingSelectors) {
            const element = document.querySelector(selector);
            if (element && element.textContent.trim()) {
                const ratingMatch = element.textContent.match(/[\d.]+/);
                if (ratingMatch) {
                    rating = ratingMatch[0];
                    break;
                }
            }
        }
        
        // Try to get address
        const addressSelectors = [
            '[data-value="address"]',
            '.Io6YTe',
            '.rogA2c'
        ];
        
        for (const selector of addressSelectors) {
            const element = document.querySelector(selector);
            if (element && element.textContent.trim()) {
                address = element.textContent.trim();
                break;
            }
        }
        
        // Try to get review count
        const reviewSelectors = [
            '[data-value="review_count"]',
            'button[jsaction*="pane.rating.moreReviews"] span',
            '.F7nice span:not([aria-hidden="true"])'
        ];
        
        for (const selector of reviewSelectors) {
            const element = document.querySelector(selector);
            if (element && element.textContent.trim()) {
                const reviewMatch = element.textContent.match(/[\d,]+/);
                if (reviewMatch) {
                    reviewCount = reviewMatch[0];
                    break;
                }
            }
        }
        
        // Return the extracted data
        const result = {
            name: name || 'Unknown Restaurant',
            rating: rating || 'N/A',
            address: address || '',
            reviewCount: reviewCount || '',
            url: window.location.href,
            timestamp: new Date().toISOString()
        };
        
        console.log('Extracted restaurant data:', result);
        return result;
        
    } catch (error) {
        console.error('Error extracting restaurant data:', error);
        return {
            name: 'Error extracting data',
            rating: 'N/A',
            address: '',
            reviewCount: '',
            url: window.location.href,
            timestamp: new Date().toISOString()
        };
    }
}

// Optional: Monitor page changes and update data
let lastUrl = window.location.href;
const observer = new MutationObserver(() => {
    const currentUrl = window.location.href;
    if (currentUrl !== lastUrl) {
        lastUrl = currentUrl;
        // Page URL changed, could notify popup if needed
        console.log('Google Maps page changed:', currentUrl);
    }
});

// Start observing for changes
observer.observe(document.body, {
    childList: true,
    subtree: true
});

// Clean up observer when page unloads
window.addEventListener('beforeunload', () => {
    observer.disconnect();
}); 