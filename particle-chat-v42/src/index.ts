/**
 * Particle Chat v42 - Claude-powered chat on Cloudflare Workers
 * 
 * This is a simple chat application that uses the Anthropic Claude API
 * to provide conversational AI capabilities on Cloudflare's edge network.
 */

import Anthropic from '@anthropic-ai/sdk';

interface Env {
  ANTHROPIC_API_KEY: string;
  NODE_ENV: string;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface ChatRequest {
  messages: ChatMessage[];
  model?: string;
  max_tokens?: number;
}

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    // Handle CORS preflight requests
    if (request.method === 'OPTIONS') {
      return handleCORS();
    }

    const url = new URL(request.url);

    // Route: GET / - Serve the chat UI
    if (url.pathname === '/' && request.method === 'GET') {
      return new Response(getHTML(), {
        headers: {
          'Content-Type': 'text/html;charset=UTF-8',
          ...getCORSHeaders(),
        },
      });
    }

    // Route: POST /api/chat - Handle chat requests
    if (url.pathname === '/api/chat' && request.method === 'POST') {
      try {
        const chatRequest: ChatRequest = await request.json();
        
        if (!chatRequest.messages || !Array.isArray(chatRequest.messages)) {
          return jsonResponse({ error: 'Invalid request: messages array required' }, 400);
        }

        const anthropic = new Anthropic({
          apiKey: env.ANTHROPIC_API_KEY,
        });

        const response = await anthropic.messages.create({
          model: chatRequest.model || 'claude-sonnet-4-20250514',
          max_tokens: chatRequest.max_tokens || 1024,
          messages: chatRequest.messages,
        });

        return jsonResponse({
          response: response.content[0].type === 'text' ? response.content[0].text : '',
          usage: response.usage,
        });
      } catch (error: any) {
        console.error('Error processing chat request:', error);
        return jsonResponse({
          error: 'Failed to process chat request',
          details: error.message,
        }, 500);
      }
    }

    // Route: GET /health - Health check endpoint
    if (url.pathname === '/health' && request.method === 'GET') {
      return jsonResponse({
        status: 'ok',
        version: 'v42',
        timestamp: new Date().toISOString(),
      });
    }

    // 404 for all other routes
    return jsonResponse({ error: 'Not found' }, 404);
  },
};

// Helper function to create JSON responses with CORS headers
function jsonResponse(data: any, status: number = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      ...getCORSHeaders(),
    },
  });
}

// CORS headers
function getCORSHeaders(): Record<string, string> {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

// Handle CORS preflight requests
function handleCORS(): Response {
  return new Response(null, {
    status: 204,
    headers: getCORSHeaders(),
  });
}

// Simple HTML UI for the chat interface
function getHTML(): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Particle Chat v42 - Claude AI</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
      padding: 20px;
    }
    
    .container {
      background: white;
      border-radius: 20px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
      width: 100%;
      max-width: 800px;
      height: 600px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 20px;
      text-align: center;
    }
    
    .header h1 {
      font-size: 24px;
      font-weight: 600;
    }
    
    .header p {
      font-size: 14px;
      opacity: 0.9;
      margin-top: 5px;
    }
    
    .messages {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 15px;
    }
    
    .message {
      display: flex;
      gap: 10px;
      animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
      from {
        opacity: 0;
        transform: translateY(10px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
    
    .message.user {
      flex-direction: row-reverse;
    }
    
    .message-content {
      max-width: 70%;
      padding: 12px 16px;
      border-radius: 18px;
      line-height: 1.5;
    }
    
    .message.user .message-content {
      background: #667eea;
      color: white;
    }
    
    .message.assistant .message-content {
      background: #f1f3f4;
      color: #333;
    }
    
    .input-area {
      padding: 20px;
      border-top: 1px solid #e0e0e0;
      display: flex;
      gap: 10px;
    }
    
    #messageInput {
      flex: 1;
      padding: 12px 16px;
      border: 2px solid #e0e0e0;
      border-radius: 25px;
      font-size: 14px;
      outline: none;
      transition: border-color 0.3s;
    }
    
    #messageInput:focus {
      border-color: #667eea;
    }
    
    #sendButton {
      padding: 12px 30px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border: none;
      border-radius: 25px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: transform 0.2s;
    }
    
    #sendButton:hover:not(:disabled) {
      transform: scale(1.05);
    }
    
    #sendButton:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    
    .loading {
      display: flex;
      gap: 5px;
      padding: 12px 16px;
    }
    
    .loading span {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #667eea;
      animation: bounce 1.4s infinite ease-in-out both;
    }
    
    .loading span:nth-child(1) {
      animation-delay: -0.32s;
    }
    
    .loading span:nth-child(2) {
      animation-delay: -0.16s;
    }
    
    @keyframes bounce {
      0%, 80%, 100% {
        transform: scale(0);
      }
      40% {
        transform: scale(1);
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🌟 Particle Chat v42</h1>
      <p>Powered by Claude AI on Cloudflare Workers</p>
    </div>
    
    <div class="messages" id="messages">
      <div class="message assistant">
        <div class="message-content">
          Hello! I'm Claude, running on Cloudflare's edge network. How can I help you today?
        </div>
      </div>
    </div>
    
    <div class="input-area">
      <input 
        type="text" 
        id="messageInput" 
        placeholder="Type your message..."
        onkeypress="if(event.key === 'Enter') sendMessage()"
      />
      <button id="sendButton" onclick="sendMessage()">Send</button>
    </div>
  </div>

  <script>
    const messagesContainer = document.getElementById('messages');
    const messageInput = document.getElementById('messageInput');
    const sendButton = document.getElementById('sendButton');
    let conversationHistory = [];

    async function sendMessage() {
      const message = messageInput.value.trim();
      if (!message) return;

      // Disable input while processing
      messageInput.disabled = true;
      sendButton.disabled = true;

      // Add user message to UI
      addMessage('user', message);
      conversationHistory.push({ role: 'user', content: message });

      // Clear input
      messageInput.value = '';

      // Show loading indicator
      const loadingDiv = document.createElement('div');
      loadingDiv.className = 'message assistant';
      loadingDiv.innerHTML = '<div class="loading"><span></span><span></span><span></span></div>';
      messagesContainer.appendChild(loadingDiv);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;

      try {
        // Send request to API
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            messages: conversationHistory,
          }),
        });

        const data = await response.json();

        // Remove loading indicator
        loadingDiv.remove();

        if (response.ok && data.response) {
          // Add assistant message to UI and history
          addMessage('assistant', data.response);
          conversationHistory.push({ role: 'assistant', content: data.response });
        } else {
          addMessage('assistant', 'Sorry, I encountered an error. Please try again.');
          console.error('API error:', data);
        }
      } catch (error) {
        loadingDiv.remove();
        addMessage('assistant', 'Sorry, I encountered a connection error. Please try again.');
        console.error('Network error:', error);
      } finally {
        // Re-enable input
        messageInput.disabled = false;
        sendButton.disabled = false;
        messageInput.focus();
      }
    }

    function addMessage(role, content) {
      const messageDiv = document.createElement('div');
      messageDiv.className = \`message \${role}\`;
      messageDiv.innerHTML = \`<div class="message-content">\${escapeHtml(content)}</div>\`;
      messagesContainer.appendChild(messageDiv);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }

    // Focus input on load
    messageInput.focus();
  </script>
</body>
</html>`;
}
