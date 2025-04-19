// Summary Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('Summary page loaded');
    
    // Auto-refresh messages every 30 seconds
    setInterval(function() {
        refreshSummary();
    }, 30000);

    // Initial load
    refreshSummary();
});

// Function to remove emojis from text
function removeEmojis(text) {
    if (!text) return '';
    // First, replace emojis followed by spaces with empty string (removes both emoji and space)
    let cleanText = text.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}][ ]?/gu, '');
    
    // Then do another pass to catch any emojis that didn't have spaces after them
    cleanText = cleanText.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '');
    
    // Clean up any double spaces that might have been created
    cleanText = cleanText.replace(/\s{2,}/g, ' ').trim();
    
    return cleanText;
}

// Function to refresh message summary
function refreshSummary() {
    console.log('Refreshing summary data...');
    
    fetch('/refresh_summary')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Received messages:', data.messages);
                console.log('Total messages received:', data.messages.length);
                updateSummaryDisplay(data.messages);
            } else {
                console.error('Error refreshing summary:', data.error);
            }
        })
        .catch(error => {
            console.error('Error fetching summary data:', error);
        });
}

// Update the summary display with new message data
function updateSummaryDisplay(messages) {
    const messagesContainer = document.querySelector('.messages-container');
    
    if (!messagesContainer) {
        console.error('Messages container not found');
        return;
    }
    
    if (!messages || messages.length === 0) {
        console.log('No messages found to display');
        messagesContainer.innerHTML = `
            <div class="no-messages">
                <p>No recent messages found</p>
            </div>
        `;
        return;
    }
    
    let html = '';
    let messageCount = 0;
    
    messages.forEach(message => {
        messageCount++;
        console.log(`Processing message ${messageCount}:`, message);
        
        // Create the chat name part
        let chatNameHTML = `<h2 class="summary-chat-name">${message.chat_name}</h2>`;
        
        // Create the message text part
        let messageTextHTML = '';
        if (message.multi_messages) {
            console.log(`Message ${messageCount} has multiple messages:`, message.message_count);
            
            // Check if this is an AI summary
            const isAiSummary = message.is_ai_summary || false;
            console.log(`Is AI summary: ${isAiSummary}`);
            
            // If it's an AI summary, display just the summary
            if (isAiSummary) {
                let cleanMessage = removeEmojis(message.message_text);
                console.log(`AI summary (filtered): ${cleanMessage}`);
                messageTextHTML = `<span class="summary-message-text ai-summary">${cleanMessage}</span>`;
            } else {
                // Join all messages with a space
                let allMessages = '';
                for (let i = 0; i < message.message_count; i++) {
                    if (i > 0) allMessages += ' ';
                    let cleanMessage = removeEmojis(message.messages[i].message_text);
                    console.log(`Sub-message ${i+1} (filtered):`, cleanMessage);
                    allMessages += cleanMessage;
                }
                messageTextHTML = `<span class="summary-message-text">${allMessages}</span>`;
            }
        } else {
            let cleanMessage = removeEmojis(message.message_text);
            console.log(`Message ${messageCount} text (filtered):`, cleanMessage);
            messageTextHTML = `<span class="summary-message-text">${cleanMessage}</span>`;
        }
        
        // Combine them into a single line
        html += `
            <div class="message-summary">
                <div class="message-line">
                    ${chatNameHTML}${messageTextHTML}
                </div>
            </div>
        `;
    });
    
    console.log(`Total messages processed: ${messageCount}`);
    messagesContainer.innerHTML = html;
}

function createMessageElement(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'summary-message';
    
    const chatName = document.createElement('div');
    chatName.className = 'summary-chat-name';
    chatName.textContent = message.chat_name;
    
    const messageText = document.createElement('div');
    messageText.className = 'summary-message-text';
    
    // Process and display the message text
    let cleanedText = removeEmojis(message.message_text);
    messageText.textContent = cleanedText;
    
    // Add AI summary class if this is an AI-generated summary
    if (message.is_ai_summary) {
        messageText.classList.add('ai-summary');
    }
    
    // Add cached indicator if this summary was from the cache
    if (message.is_cached) {
        const cachedIndicator = document.createElement('span');
        cachedIndicator.className = 'cached-indicator';
        cachedIndicator.textContent = ' ⟳'; // Recycling symbol to indicate cache
        cachedIndicator.title = 'Using cached summary';
        messageText.appendChild(cachedIndicator);
    }
    
    messageElement.appendChild(chatName);
    messageElement.appendChild(messageText);
    
    return messageElement;
}

// Helper function to remove emojis and trailing spaces
function removeEmojis(text) {
    if (!text) return "";
    
    // Emoji regex pattern
    const emojiRegex = /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu;
    
    // Remove emojis and any spaces that follow them
    return text.replace(emojiRegex, '').replace(/\s+/g, ' ').trim();
}

function refreshMessages() {
    const messagesContainer = document.getElementById('messages-container');
    messagesContainer.innerHTML = '<div class="loading-indicator">Loading messages...</div>';
    
    fetch('/refresh_summary')
        .then(response => response.json())
        .then(data => {
            console.log('Received messages:', data.messages);
            
            if (!data.success) {
                messagesContainer.innerHTML = `<div class="error-message">${data.error || 'Error loading messages'}</div>`;
                return;
            }
            
            if (!data.messages || data.messages.length === 0) {
                messagesContainer.innerHTML = '<div class="empty-message">No messages available</div>';
                return;
            }
            
            // Clear the container
            messagesContainer.innerHTML = '';
            
            // Add each message to the container
            data.messages.forEach(message => {
                const messageElement = createMessageElement(message);
                messagesContainer.appendChild(messageElement);
            });
        })
        .catch(error => {
            console.error('Error fetching messages:', error);
            messagesContainer.innerHTML = '<div class="error-message">Error loading messages. Please try again.</div>';
        });
} 