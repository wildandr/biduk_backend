import os
from flask import Flask, request, jsonify, render_template_string, session
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API key from environment variable
DEEPSEEK_API_KEY="sk-bfcc9685e30a4bb3bb9d0d3d2445d7f4"

if not DEEPSEEK_API_KEY:
    print("Error: DEEPSEEK_API_KEY not found in .env file or environment variables.")
    exit()

# Configure the DeepSeek API client
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management

def load_tourism_data():
    """Load tourism data from data.txt file"""
    try:
        with open('data.txt', 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print("Error: data.txt file not found.")
        return None

def ask_chatbot(question, tourism_data, conversation_history=None):
    """Ask question to the chatbot with tourism context and conversation history"""
    
    system_prompt = f"""You are a tourism assistant expert about Biduk-Biduk, Berau Regency, East Kalimantan. You are enthusiastic, helpful and always promoting tourism positively.
    
CRITICAL: Answer questions based STRICTLY and ONLY on the tourism data provided below. DO NOT add information from outside the given context or make up details that are not explicitly stated in the data.

Tourism Data for Biduk-Biduk:
{tourism_data}

ANTI-HALLUCINATION RULES:
1. If asked about specific details NOT in the data (like airline names, specific hotel prices, specific tour operators), provide general guidance without specifics
2. For questions you cannot answer completely, provide what information IS available and redirect to contact: "Untuk informasi lebih detail, silakan hubungi Pokdarwis Desir di 0812-1000-2190 atau bidukbidukpokdarwis@gmail.com" (adapt to the question language)
3. NEVER include phrases like "tidak ada informasi" or "informasi tidak tersedia" or "data tidak mencantumkan"
4. NEVER add disclaimers or notes about missing information - just smoothly provide what you do know

LANGUAGE DETECTION AND RESPONSE RULES:
- DETECT the language of the user's question first
- RESPOND in the EXACT SAME LANGUAGE as the question
- If question is in Arabic, answer in Arabic
- If question is in English, answer in English  
- If question is in Indonesian, answer in Indonesian
- If question is in Chinese, answer in Chinese
- If question is in Japanese, answer in Japanese
- And so on for ANY language

CONVERSATION STYLE:
1. For greetings (hello, hi), respond with a warm greeting AND ask how you can help with information about Biduk-Biduk tourism
2. Be proactive, enthusiastic, and confident in all responses
3. After answering, ask a follow-up question ONLY about topics mentioned in the data
4. ONLY focus on POSITIVE aspects of Biduk-Biduk tourism
5. NEVER mention limitations, problems, challenges about infrastructure, transportation, etc.
6. Present all facilities and access routes in a PURELY positive light
7. If information is partial or limited, present what you DO know confidently without mentioning any gaps
8. AVOID cautionary language or any phrases suggesting incomplete information

FORMAT INSTRUCTIONS:
1. Answer SHORT and RELEVANT to the question only
2. NO emojis or symbols
3. NO markdown formatting (no **, #, etc.)
4. For lists, use simple numbers followed by a period (1. 2. 3.)
5. Use plain line breaks instead of markdown formatting
6. Answer in the SAME language as the question
7. NEVER add disclaimers, notes or statements about information limitations
8. Remove ANY phrase that suggests incomplete information"""

    try:
        # Initialize messages with system prompt
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if available
        if conversation_history:
            messages.extend(conversation_history)
        else:
            # If no history, just add the current question
            messages.append({"role": "user", "content": question})
            
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            max_tokens=1500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# HTML Template with embedded CSS
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chatbot Pariwisata Biduk-Biduk</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .chat-container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 800px;
            height: 600px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .chat-header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }

        .chat-header h1 {
            font-size: 1.5rem;
            margin-bottom: 5px;
        }

        .chat-header p {
            opacity: 0.9;
            font-size: 0.9rem;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .message {
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 18px;
            line-height: 1.5;
            word-wrap: break-word;
        }
        
        .bot-message {
            white-space: pre-line; /* Preserve line breaks */
        }

        .user-message {
            background: #007bff;
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 6px;
        }

        .bot-message {
            background: #f1f3f4;
            color: #333;
            align-self: flex-start;
            border-bottom-left-radius: 6px;
        }

        .loading {
            background: #f1f3f4;
            color: #666;
            align-self: flex-start;
            font-style: italic;
        }

        .chat-input {
            padding: 20px;
            border-top: 1px solid #e0e0e0;
            background: #fafafa;
        }

        .input-group {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .controls {
            display: flex;
            justify-content: flex-end;
            margin-bottom: 10px;
        }
        
        #clearButton {
            background: #f44336;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 15px;
            cursor: pointer;
            font-size: 12px;
            transition: background-color 0.3s;
        }
        
        #clearButton:hover {
            background: #d32f2f;
        }

        #messageInput {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            outline: none;
            font-size: 14px;
            transition: border-color 0.3s;
        }

        #messageInput:focus {
            border-color: #007bff;
        }

        #sendButton {
            background: #007bff;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: background-color 0.3s;
            min-width: 80px;
        }

        #sendButton:hover:not(:disabled) {
            background: #0056b3;
        }

        #sendButton:disabled {
            background: #ccc;
            cursor: not-allowed;
        }

        .welcome-message {
            text-align: center;
            color: #666;
            font-style: italic;
            margin: 20px;
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .chat-container {
                height: 90vh;
                border-radius: 15px;
            }
            
            .chat-header h1 {
                font-size: 1.3rem;
            }
            
            .message {
                max-width: 90%;
            }
            
            .input-group {
                flex-direction: column;
                gap: 10px;
            }
            
            #messageInput {
                border-radius: 15px;
            }
            
            #sendButton {
                width: 100%;
                border-radius: 15px;
            }
        }

        @media (max-width: 480px) {
            .chat-header {
                padding: 15px;
            }
            
            .chat-messages {
                padding: 15px;
            }
            
            .chat-input {
                padding: 15px;
            }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>Chatbot Pariwisata Biduk-Biduk</h1>
            <p>Tanyakan tentang wisata di Biduk-Biduk, Kalimantan Timur</p>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="welcome-message">
                Selamat datang di Asisten Pariwisata Biduk-Biduk! Apa yang ingin Anda ketahui tentang keindahan surga tersembunyi di Kalimantan Timur ini?
            </div>
        </div>
        
        <div class="chat-input">
            <div class="controls">
                <button id="clearButton">Hapus Percakapan</button>
            </div>
            <div class="input-group">
                <input type="text" id="messageInput" placeholder="Ketik pertanyaan Anda di sini..." maxlength="500">
                <button id="sendButton">Kirim</button>
            </div>
        </div>
    </div>

    <script>
        const chatMessages = document.getElementById('chatMessages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const clearButton = document.getElementById('clearButton');

        function addMessage(message, isUser = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
            // Format response for better readability
            if (!isUser) {
                // For bot messages, parse basic formatting
                message = message.replace(/(\\d+)\\.\s/g, '<br>$1. '); // Handle numbered lists
                message = message.replace(/\\n/g, '<br>'); // Replace newlines with <br>
                messageDiv.innerHTML = message;
            } else {
                messageDiv.textContent = message;
            }
            chatMessages.appendChild(messageDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

        function addLoadingMessage() {
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'message loading';
            loadingDiv.textContent = 'Mencari jawaban...';
            loadingDiv.id = 'loadingMessage';
            chatMessages.appendChild(loadingDiv);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            return loadingDiv;
        }

        function removeLoadingMessage() {
            const loadingMessage = document.getElementById('loadingMessage');
            if (loadingMessage) {
                loadingMessage.remove();
            }
        }

        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            addMessage(message, true);
            messageInput.value = '';
            sendButton.disabled = true;
            
            const loadingMessage = addLoadingMessage();

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message }),
                });

                const data = await response.json();
                removeLoadingMessage();
                addMessage(data.response);
            } catch (error) {
                removeLoadingMessage();
                addMessage('Maaf, terjadi kesalahan. Silakan coba lagi.');
            } finally {
                sendButton.disabled = false;
                messageInput.focus();
            }
        }

        sendButton.addEventListener('click', sendMessage);
        
        messageInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !sendButton.disabled) {
                sendMessage();
            }
        });

        // Function to clear conversation
        async function clearConversation() {
            try {
                const response = await fetch('/clear', {
                    method: 'POST',
                });
                
                if (response.ok) {
                    // Clear the chat messages in the UI
                    while (chatMessages.firstChild) {
                        chatMessages.removeChild(chatMessages.firstChild);
                    }
                    
                    // Add welcome message back
                    const welcomeMessage = document.createElement('div');
                    welcomeMessage.className = 'welcome-message';
                    welcomeMessage.textContent = 'Selamat datang di Asisten Pariwisata Biduk-Biduk! Apa yang ingin Anda ketahui tentang keindahan surga tersembunyi di Kalimantan Timur ini?';
                    chatMessages.appendChild(welcomeMessage);
                }
            } catch (error) {
                console.error('Error clearing conversation:', error);
            }
        }
        
        // Add event listener for clear button
        clearButton.addEventListener('click', clearConversation);

        // Focus input on load
        messageInput.focus();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    # Clear the conversation history when the page is loaded
    if 'conversation' in session:
        session.pop('conversation')
    return render_template_string(HTML_TEMPLATE)

@app.route('/clear', methods=['POST'])
def clear_conversation():
    # Clear the conversation history
    if 'conversation' in session:
        session.pop('conversation')
    return jsonify({'status': 'success'})

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'response': 'Silakan masukkan pertanyaan.'})
        
        # Load tourism data
        tourism_data = load_tourism_data()
        if not tourism_data:
            return jsonify({'response': 'Data pariwisata tidak dapat dimuat.'})
        
        # Initialize conversation history if it doesn't exist in the session
        if 'conversation' not in session:
            session['conversation'] = []
        
        # Add the user message to the conversation history
        session['conversation'].append({"role": "user", "content": user_message})
        
        # Get response from chatbot
        response = ask_chatbot(user_message, tourism_data, session['conversation'])
        
        # Add the assistant's response to the conversation history
        session['conversation'].append({"role": "assistant", "content": response})
        
        # Save the session
        session.modified = True
        
        return jsonify({'response': response})
    
    except Exception as e:
        return jsonify({'response': f'Terjadi kesalahan: {str(e)}'})

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
