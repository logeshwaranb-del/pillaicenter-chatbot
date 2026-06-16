// ==================== FINAL UPDATED CHATBOT.JS ====================

let sessionId = localStorage.getItem("pillai_chat_session_id") || null;
let userInfo = JSON.parse(localStorage.getItem("pillai_user_info")) || null;

function createChatWidget() {
    const html = `
        <div id="chat-widget" style="position: fixed; bottom: 20px; right: 20px; z-index: 99999; font-family: Arial, sans-serif;">
            
            <button id="chat-btn" style="width: 60px; height: 60px; border-radius: 50%; background: #1a365d; color: white; border: none; font-size: 26px; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">💬</button>
            
            <div id="chat-window" style="display: none; position: absolute; bottom: 75px; right: 0; width: 360px; height: 560px; background: white; border-radius: 12px; box-shadow: 0 8px 25px rgba(0,0,0,0.2); flex-direction: column; overflow: hidden; border: 1px solid #ddd;">
                
                <!-- Header -->
                <div style="background: #1a365d; color: white; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: bold; font-size: 15px;">Pillai Center Assistant</span>
                    
                    <div style="display: flex; align-items: center; gap: 6px;">
                        
                        <!-- End Chat Button -->
                        <button id="end-chat-btn" 
                                style="background: #e74c3c; color: white; border: none; padding: 5px 10px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: bold;">
                            End Chat
                        </button>
                        
                        <!-- Minimize Button -->
                        <button id="minimize-btn" 
                                style="background: none; border: none; color: white; font-size: 20px; cursor: pointer; padding: 0 4px;">
                            −
                        </button>
                        
                        <!-- Close Button -->
                        <button id="close-btn" 
                                style="background: none; border: none; color: white; font-size: 22px; cursor: pointer; padding: 0 4px;">
                            ×
                        </button>
                    </div>
                </div>

                <!-- Registration Form -->
                <div id="registration-area" style="padding: 25px; display: none; flex-direction: column; gap: 14px; background: white;">
                    <h3 style="margin: 0 0 15px 0; text-align: center; color: #1a365d;">Create Your Account</h3>
                    
                    <input type="text" id="reg-name" placeholder="Full Name" style="padding: 12px; border: 1px solid #ccc; border-radius: 8px; width: 100%;">
                    <input type="email" id="reg-email" placeholder="Email Address" style="padding: 12px; border: 1px solid #ccc; border-radius: 8px; width: 100%;">
                    <input type="tel" id="reg-phone" placeholder="Mobile Number" style="padding: 12px; border: 1px solid #ccc; border-radius: 8px; width: 100%;">
                    
                    <button id="reg-submit" style="background: #1a365d; color: white; border: none; padding: 14px; border-radius: 8px; cursor: pointer; font-size: 16px; margin-top: 10px;">
                        Register & Start Chat
                    </button>
                </div>

                <!-- Chat Messages -->
                <div id="chat-messages" style="flex: 1; padding: 15px; overflow-y: auto; background: #f8f9fa; font-size: 14px; display: none;"></div>

                <!-- Chat Input -->
                <div id="chat-input-area" style="padding: 10px; border-top: 1px solid #ddd; display: none; gap: 8px; background: white;">
                    <input type="text" id="chat-input" placeholder="Type your message..." style="flex: 1; padding: 10px; border: 1px solid #ccc; border-radius: 20px; font-size: 14px;">
                    <button id="send-btn" style="background: #1a365d; color: white; border: none; padding: 10px 16px; border-radius: 20px; cursor: pointer;">Send</button>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', html);
}

function initChat() {
    createChatWidget();

    const chatBtn = document.getElementById('chat-btn');
    const chatWindow = document.getElementById('chat-window');
    const closeBtn = document.getElementById('close-btn');
    const minimizeBtn = document.getElementById('minimize-btn');
    const endChatBtn = document.getElementById('end-chat-btn');
    const registrationArea = document.getElementById('registration-area');
    const messages = document.getElementById('chat-messages');
    const chatInputArea = document.getElementById('chat-input-area');
    const sendBtn = document.getElementById('send-btn');
    const chatInput = document.getElementById('chat-input');
    const regSubmit = document.getElementById('reg-submit');

    // Open Chat
    chatBtn.addEventListener('click', () => {
        chatWindow.style.display = 'flex';
        chatBtn.style.display = 'none';

        if (!userInfo) {
            registrationArea.style.display = 'flex';
        } else {
            messages.style.display = 'block';
            chatInputArea.style.display = 'flex';
            addMessage("bot", `Welcome back, ${userInfo.name}! How can I help you?`);
        }
    });

    // Close Chat
    closeBtn.addEventListener('click', () => {
        chatWindow.style.display = 'none';
        chatBtn.style.display = 'block';
    });

    // Minimize Chat
    minimizeBtn.addEventListener('click', () => {
        chatWindow.style.display = 'none';
        chatBtn.style.display = 'block';
    });

    // End Chat Button
    endChatBtn.addEventListener('click', async () => {
        if (confirm("Are you sure you want to end this chat?")) {
            try {
                await fetch("/end-chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ session_id: sessionId })
                });
            } catch (e) {}

            messages.innerHTML = "";
            addMessage("bot", "Thank you for chatting with us! Have a great day.");
            chatInputArea.style.display = "none";

            setTimeout(() => {
                chatWindow.style.display = "none";
                chatBtn.style.display = "block";
            }, 3000);
        }
    });

    // ==================== REGISTRATION ====================
    regSubmit.addEventListener('click', () => {
        const name = document.getElementById('reg-name').value.trim();
        const email = document.getElementById('reg-email').value.trim();
        const phone = document.getElementById('reg-phone').value.trim();

        if (!name || !email || !phone) {
            alert("Please fill Name, Email and Phone Number");
            return;
        }

        // Save locally
        userInfo = { name, email, phone };
        localStorage.setItem("pillai_user_info", JSON.stringify(userInfo));

        // Hide registration and show chat
        registrationArea.style.display = 'none';
        messages.style.display = 'block';
        chatInputArea.style.display = 'flex';

        addMessage("bot", `Thank you ${name}! How can I help you today?`);

        // Send data to MySQL
        fetch("/save-user", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email, phone })
        })
        .then(response => response.json())
        .then(data => {
            console.log("Server Response:", data);
            if (data.status === "success") {
                console.log("✅ Data saved in MySQL successfully");
            } else {
                console.log("❌ Failed to save:", data.message);
            }
        })
        .catch(error => {
            console.log("Error sending data to server:", error);
        });
    });
    // ========================================================

    function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        addMessage("user", text);
        chatInput.value = "";

        fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text, session_id: sessionId })
        })
        .then(res => res.json())
        .then(data => {
            if (data.answer) {
                addMessage("bot", data.answer, data.sources);
            }
        })
        .catch(() => {
            addMessage("bot", "Sorry, there was a connection error.");
        });
    }

    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === "Enter") sendMessage();
    });

    function addMessage(role, text, sources = []) {
        const msg = document.createElement("div");
        msg.style.cssText = role === "user" 
            ? "background:#1a365d; color:white; padding:10px 14px; border-radius:16px; margin:8px 0; max-width:80%; margin-left:auto;"
            : "background:#e9ecef; padding:10px 14px; border-radius:16px; margin:8px 0; max-width:80%;";

        let html = text;

        if (role === "bot" && sources && sources.length > 0 && !text.toLowerCase().includes("sorry")) {
            const source = sources[0];
            if (source.url) {
                html += `<br><br><small style="color:#1e40af; font-size:12px;">
                    📄 <a href="${source.url}" target="_blank" style="color:#1e40af; text-decoration:none;">Read full page</a>
                </small>`;
            }
        }

        msg.innerHTML = html;
        messages.appendChild(msg);
        messages.scrollTop = messages.scrollHeight;
    }
}

window.onload = function() {
    initChat();
};