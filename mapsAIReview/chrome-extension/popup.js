// DOM elements
const statusText = document.getElementById('status-text');
const chatContainer = document.getElementById('chat-container');
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const sendText = document.getElementById('send-text');
const sendLoading = document.getElementById('send-loading');
const loading = document.getElementById('loading');
// Removed results, jsonOutput, copyBtn, downloadBtn since export functionality was removed
const errorDiv = document.getElementById('error');
const successMessage = document.getElementById('success-message');

let currentUrl = '';
let reviewData = null;
let conversationHistory = [];
let restaurantData = null;

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
    await checkCurrentPage();
    setupEventListeners();
});

// Event listeners
function setupEventListeners() {
    sendBtn.addEventListener('click', handleSendMessage);
    chatInput.addEventListener('keypress', handleKeyPress);
}

// Set up example button listeners when chat interface is shown
function setupExampleButtonListeners() {
    const exampleBtns = document.querySelectorAll('.example-btn');
    console.log('Found example buttons:', exampleBtns.length);
    
    exampleBtns.forEach(btn => {
        // Remove any existing listeners to prevent duplicates
        btn.replaceWith(btn.cloneNode(true));
    });
    
    // Re-query after cloning to get fresh elements
    const freshExampleBtns = document.querySelectorAll('.example-btn');
    freshExampleBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const question = btn.getAttribute('data-question');
            console.log('Button clicked, question:', question);
            if (chatInput && question) {
                chatInput.value = question;
                handleSendMessage();
            }
        });
    });
}

// Check if current page is Google Maps restaurant page
async function checkCurrentPage() {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        currentUrl = tab.url;
        
        if (!isGoogleMapsPage(currentUrl)) {
            showError('Please navigate to a restaurant page on Google Maps');
            return;
        }
        
        // Immediately fetch restaurant data from API
        statusText.textContent = 'Loading restaurant data...';
        await loadRestaurantData();
        
    } catch (error) {
        console.error('Error checking page:', error);
        showError('Error checking current page');
    }
}

// Load restaurant data immediately when extension opens
async function loadRestaurantData() {
    try {
        console.log('Fetching restaurant data for:', currentUrl);
        
        // Make API call to get restaurant data
        const response = await fetch('http://localhost:5000/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: currentUrl,
                num_reviews: 50
            })
        });
        
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }
        
        restaurantData = await response.json();
        console.log('Restaurant data loaded:', restaurantData);
        
        // Extract restaurant info from the loaded data
        const locationDetails = restaurantData.locationDetails;
        if (locationDetails && locationDetails.title) {
            statusText.textContent = `Ready to chat about ${locationDetails.title}`;
        } else {
            statusText.textContent = 'Ready to chat about this restaurant';
        }
        showChatInterface();
        
    } catch (error) {
        console.error('Error loading restaurant data:', error);
        
        // Fallback to basic extraction if API fails
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        const basicName = await getBasicRestaurantName(tab);
        
        if (basicName) {
            statusText.textContent = `Ready to chat about ${basicName}`;
        } else {
            statusText.textContent = 'Ready to chat about this restaurant';
        }
        
        showChatInterface();
        showError('Could not connect to local server. Make sure it\'s running on port 5000.');
    }
}

// Check if URL is Google Maps
function isGoogleMapsPage(url) {
    return url.includes('google.com/maps') || url.includes('maps.google.com');
}

// Extract restaurant info from the tab
async function extractRestaurantInfo(tab) {
    try {
        // Try to get restaurant name from page title or content script
        const results = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            function: getRestaurantDataFromPage
        });
        
        return results[0]?.result || null;
    } catch (error) {
        console.error('Error extracting restaurant info:', error);
        return null;
    }
}

// Function that runs in the content script context
function getRestaurantDataFromPage() {
    // Try to find restaurant name and rating from the page
    let name = '';
    let rating = '';
    
    // Look for restaurant name in various selectors
    const nameSelectors = [
        'h1[data-attrid="title"]',
        'h1.x3AX1-LfntMc-header-title-title',
        '[data-value="title"]',
        'h1'
    ];
    
    for (const selector of nameSelectors) {
        const element = document.querySelector(selector);
        if (element && element.textContent.trim()) {
            name = element.textContent.trim();
            break;
        }
    }
    
    // Look for rating
    const ratingSelectors = [
        '[data-value="rating"] span',
        '.ceNzKf',
        '[aria-label*="stars"]'
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
    
    if (name) {
        return { name, rating: rating || 'N/A' };
    }
    
    return null;
}

// Get basic restaurant name even if full extraction fails
async function getBasicRestaurantName(tab) {
    try {
        const results = await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            function: getRestaurantNameOnly
        });
        
        return results[0]?.result || null;
    } catch (error) {
        console.error('Error extracting basic restaurant name:', error);
        return null;
    }
}

// Function to get just the restaurant name
function getRestaurantNameOnly() {
    console.log('Attempting to extract restaurant name...');
    console.log('Current URL:', window.location.href);
    console.log('Page title:', document.title);
    
    // Try to find restaurant name in various selectors (updated for current Google Maps)
    const nameSelectors = [
        // Main title selectors
        'h1[data-attrid="title"]',
        'h1.x3AX1-LfntMc-header-title-title',
        '[data-value="title"]',
        
        // New Google Maps selectors
        '[data-value="title"] span',
        '.DUwDvf.lfPIob',
        '.x3AX1-LfntMc-header-title-title span',
        '.fontHeadlineSmall',
        
        // Generic selectors
        'h1',
        '[aria-level="1"]',
        '.section-hero-header-title',
        '.section-hero-header-title span',
        
        // Backup selectors
        '[role="main"] h1',
        '[role="main"] [aria-level="1"]'
    ];
    
    for (let i = 0; i < nameSelectors.length; i++) {
        const selector = nameSelectors[i];
        console.log(`Trying selector ${i + 1}/${nameSelectors.length}: ${selector}`);
        
        const element = document.querySelector(selector);
        if (element) {
            const name = element.textContent.trim();
            console.log(`Found element with text: "${name}"`);
            
            // Filter out common non-restaurant text
            if (name && 
                !name.includes('Google Maps') && 
                !name.includes('Directions') &&
                !name.includes('Reviews') &&
                name.length > 2 && 
                name.length < 100) {
                console.log(`Returning restaurant name: "${name}"`);
                return name;
            }
        } else {
            console.log(`No element found for selector: ${selector}`);
        }
}

    // Try page title as fallback
    console.log('Trying page title fallback...');
    if (document.title && !document.title.includes('Google Maps')) {
        const titleParts = document.title.split(' - ');
        if (titleParts[0] && titleParts[0].trim().length > 2) {
            const titleName = titleParts[0].trim();
            console.log(`Found name from title: "${titleName}"`);
            return titleName;
        }
    }
    
    // Try URL extraction as last resort
    console.log('Trying URL extraction...');
    const url = window.location.href;
    const placeMatch = url.match(/\/place\/([^\/]+)/);
    if (placeMatch) {
        const urlName = decodeURIComponent(placeMatch[1]).replace(/\+/g, ' ');
        console.log(`Found name from URL: "${urlName}"`);
        return urlName;
    }
    
    console.log('No restaurant name found');
    return null;
}

// Removed restaurant info display functions since the info card was removed

// Show chat interface
function showChatInterface() {
    chatContainer.style.display = 'block';
    chatInput.focus();
    
    // Set up example button listeners now that they're visible
    setupExampleButtonListeners();
}

// Handle key press in chat input
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        handleSendMessage();
    }
}

// Handle send message button click
async function handleSendMessage() {
    const question = chatInput.value.trim();
    
    if (!question) {
        return;
    }
    
    // Add user message to chat
    addMessageToChat(question, 'user');
    
    // Clear input and show loading
    chatInput.value = '';
    showSendLoading();
    hideError();
    
    try {
        const response = await askQuestionWithData(question, restaurantData);
        console.log('Chat response:', response);
        addMessageToChat(response.answer, 'bot');
        
        // Store conversation for potential JSON export
        conversationHistory.push({
            question: question,
            answer: response.answer,
            timestamp: new Date().toISOString()
        });
        
    } catch (error) {
        console.error('Error asking question:', error);
        addMessageToChat('Sorry, I encountered an error. Please try again.', 'bot');
        showError(error.message || 'Failed to get answer');
    } finally {
        hideSendLoading();
    }
}

// Add message to chat interface
function addMessageToChat(message, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = message;
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show loading state for send button
function showSendLoading() {
    sendBtn.disabled = true;
    sendText.style.display = 'none';
    sendLoading.style.display = 'inline';
}

// Hide loading state for send button
function hideSendLoading() {
    sendBtn.disabled = false;
    sendText.style.display = 'inline';
    sendLoading.style.display = 'none';
}

// Ask question using pre-loaded restaurant data
async function askQuestionWithData(question, restaurantData) {
    try {
        if (!restaurantData) {
            throw new Error('No restaurant data loaded. Please try refreshing the extension.');
        }
        
        // Make request to chat endpoint with pre-loaded data
        const response = await fetch('http://localhost:5000/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: currentUrl,
                question: question,
                restaurant_data: restaurantData  // Send pre-loaded data
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Server error' }));
            throw new Error(errorData.error || `Server returned ${response.status}`);
        }
        
        const data = await response.json();
        return data;
        
    } catch (error) {
        if (error.message.includes('fetch')) {
            throw new Error('Could not connect to local server. Make sure it\'s running on port 5000.');
        }
        throw error;
    }
}

// Legacy function (kept for compatibility)
async function askQuestion(url, question) {
    try {
        // First, try to check if local server is running
        const healthCheck = await fetch('http://localhost:5000/health', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!healthCheck.ok) {
            throw new Error('Local server not running. Please start the server first.');
        }
        
        // Make request to local server
        const response = await fetch('http://localhost:5000/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                question: question
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Server error' }));
            throw new Error(errorData.error || `Server returned ${response.status}`);
        }
        
        const data = await response.json();
        return data;
        
    } catch (error) {
        if (error.message.includes('fetch')) {
            throw new Error('Could not connect to local server. Make sure it\'s running on port 5000.');
        }
        throw error;
    }
}

// Show loading state
function showLoading() {
    loading.style.display = 'block';
}

// Hide loading state
function hideLoading() {
    loading.style.display = 'none';
}

// Removed copyToClipboard and downloadJson functions since export functionality was removed

// Show error message
function showError(message) {
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

// Hide error message
function hideError() {
    errorDiv.style.display = 'none';
}

// Show success message
function showSuccessMessage(message) {
    successMessage.textContent = message;
    successMessage.style.display = 'block';
    
    setTimeout(() => {
        successMessage.style.display = 'none';
    }, 3000);
} 
