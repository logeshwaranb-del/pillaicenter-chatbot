// ==================== FINAL UPDATED CHATBOT.JS (With Email OTP Verification) ====================

let sessionId = localStorage.getItem("pillai_chat_session_id") || null;
let userInfo = JSON.parse(localStorage.getItem("pillai_user_info")) || null;
let verifiedEmail = null;

function createChatWidget() {
    const html = `
        <div id="chat-widget" style="position: fixed; bottom: 20px; right: 20px; z-index: 99999; font-family: Arial, sans-serif;">
            
            <button id="chat-btn" style="width: 60px; height: 60px; border-radius: 50%; background: #1a365d; color: white; border: none; font-size: 26px; cursor: pointer; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">💬</button>
            
            <div id="chat-window" style="display: none; position: absolute; bottom: 75px; right: 0; width: 360px; height: 580px; background: white; border-radius: 12px; box-shadow: 0 8px 25px rgba(0,0,0,0.2); flex-direction: column; overflow: hidden; border: 1px solid #ddd;">
                
                <!-- Header -->
                <div style="background: #1a365d; color: white; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: bold; font-size: 15px;">Pillai Center Assistant</span>
                    
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <button id="end-chat-btn" style="background: #e74c3c; color: white; border: none; padding: 5px 10px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: bold;">End Chat</button>
                        <button id="minimize-btn" style="background: none; border: none; color: white; font-size: 20px; cursor: pointer; padding: 0 4px;">−</button>
                        <button id="close-btn" style="background: none; border: none; color: white; font-size: 22px; cursor: pointer; padding: 0 4px;">×</button>
                    </div>
                </div>

                <!-- ==================== EMAIL VERIFICATION + REGISTRATION ==================== -->
                <div id="email-verification-area" style="padding: 25px; display: flex; flex-direction: column; gap: 14px; background: white;">
                    <h3 style="margin: 0 0 10px 0; text-align: center; color: #1a365d;">Verify Your Email</h3>
                    
                    <input type="text" id="reg-name" placeholder="Full Name" style="padding: 12px; border: 1px solid #ccc; border-radius: 8px; width: 100%;">
                    <input type="email" id="reg-email" placeholder="Email Address" style="padding: 12px; border: 1px solid #ccc; border-radius: 8px; width: 100%;">
                    <input type="tel" id="reg-phone" placeholder="Mobile Number" style="padding: 12px; border: 1px solid #ccc; border-radius: 8px; width: 100%;">
                    
                    <button id="send-otp-btn" style="background: #1a365d; color: white; border: none; padding: 14px; border-radius: 8px; cursor: pointer; font-size: 16px;">
                        Send Verification Code
                    </button>

                    <!-- OTP Section -->
                    <div id="otp-section" style="display: none; flex-direction: column; gap: 10px; margin-top: 10px;">
                        <input type="text" id="otp-input" placeholder="Enter 6-digit Code" 
                               style="padding: 12px; border: 1px solid #ccc; border-radius: 8px; width: 100%; text-align: center; letter-spacing: 4px;">
                        
                        <button id="verify-otp-btn" style="background: #27ae60; color: white; border: none; padding: 14px; border-radius: 8px; cursor: pointer; font-size: 16px;">
                            Verify Code
                        </button>
                        
                        <button id="resend-otp-btn" style="background: #f39c12; color: white; border: none; padding: 10px; border-radius: 8px; cursor: pointer; font-size: 14px;">
                            Resend Code
                        </button>
                    </div>
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
    const emailVerificationArea = document.getElementById('email-verification-area');
    const messages = document.getElementById('chat-messages');
    const chatInputArea = document.getElementById('chat-input-area');
    const sendBtn = document.getElementById('send-btn');
    const chatInput = document.getElementById('chat-input');

    // OTP Elements
    const sendOtpBtn = document.getElementById('send-otp-btn');
    const otpSection = document.getElementById('otp-section');
    const verifyOtpBtn = document.getElementById('verify-otp-btn');
    const resendOtpBtn = document.getElementById('resend-otp-btn');
    const regName = document.getElementById('reg-name');
    const regEmail = document.getElementById('reg-email');
    const regPhone = document.getElementById('reg-phone');
    const otpInput = document.getElementById('otp-input');

    // Open Chat Button
    chatBtn.addEventListener('click', () => {
        chatWindow.style.display = 'flex';
        chatBtn.style.display = 'none';

        if (!verifiedEmail) {
            emailVerificationArea.style.display = 'flex';
            messages.style.display = 'none';
            chatInputArea.style.display = 'none';
        } else {
            emailVerificationArea.style.display = 'none';
            messages.style.display = 'block';
            chatInputArea.style.display = 'flex';
        }
    });

    // Close & Minimize
    closeBtn.addEventListener('click', () => {
        chatWindow.style.display = 'none';
        chatBtn.style.display = 'block';
    });

    minimizeBtn.addEventListener('click', () => {
        chatWindow.style.display = 'none';
        chatBtn.style.display = 'block';
    });

    // End Chat
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

    // ==================== SEND OTP ====================
    sendOtpBtn.addEventListener('click', async () => {
        const name = regName.value.trim();
        const email = regEmail.value.trim();
        const phone = regPhone.value.trim();

        if (!name || !email || !phone) {
            alert("Please fill Name, Email and Mobile Number");
            return;
        }

        sendOtpBtn.innerText = "Sending...";
        sendOtpBtn.disabled = true;

        try {
            const res = await fetch("/send-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: email })
            });

            const data = await res.json();

            if (data.status === "success") {
                alert("Verification code sent to your email!");
                otpSection.style.display = "flex";
                sendOtpBtn.style.display = "none";
                
                // Store user data temporarily
                window.tempUserData = { name, email, phone };
            } else {
                alert(data.message || "Failed to send OTP");
            }
        } catch (error) {
            alert("Error sending OTP");
        }

        sendOtpBtn.innerText = "Send Verification Code";
        sendOtpBtn.disabled = false;
    });

    // ==================== VERIFY OTP ====================
    verifyOtpBtn.addEventListener('click', async () => {
        const email = regEmail.value.trim();
        const otp = otpInput.value.trim();

        if (!otp) {
            alert("Please enter the verification code");
            return;
        }

        try {
            const res = await fetch("/verify-otp", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: email, otp: otp })
            });

            const data = await res.json();

            if (data.status === "success") {
                verifiedEmail = email;
                alert("Email verified successfully!");

                // Hide verification section
                emailVerificationArea.style.display = "none";

                // Save user data
                const userData = window.tempUserData;
                if (userData) {
                    await fetch("/save-user", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(userData)
                    });
                }

                // Start Chat
                messages.style.display = 'block';
                chatInputArea.style.display = 'flex';
                addMessage("bot", `Thank you ${userData.name}! How can I help you today?`);

            } else {
                alert(data.message || "Invalid verification code");
            }
        } catch (error) {
            alert("Error verifying code");
        }
    });

    // Resend OTP
    resendOtpBtn.addEventListener('click', () => {
        otpSection.style.display = "none";
        sendOtpBtn.style.display = "block";
        otpInput.value = "";
    });

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
            const lastUserMsg = getLastUserMessage().toLowerCase();
            const isInformational = lastUserMsg.includes("what") || lastUserMsg.includes("how") || lastUserMsg.includes("tell me") || lastUserMsg.includes("about") || lastUserMsg.includes("details");
            const isGeneralSupport = text.toLowerCase().includes("contact") || text.toLowerCase().includes("support") || text.toLowerCase().includes("reach");

            if (isInformational && !isGeneralSupport) {
                const source = sources[0];
                if (source.url) {
                    html += `<br><br><a href="${source.url}" target="_blank" style="display:inline-block; background:#1e40af; color:white; padding:8px 16px; border-radius:6px; text-decoration:none; font-size:13px; font-weight:bold;">📄 Read full page</a>`;
                }
            }
        }

        msg.innerHTML = html;
        messages.appendChild(msg);
        messages.scrollTop = messages.scrollHeight;
    }

    function getLastUserMessage() {
        const allMessages = messages.querySelectorAll("div");
        for (let i = allMessages.length - 1; i >= 0; i--) {
            if (allMessages[i].style.background === "rgb(26, 54, 93)") {
                return allMessages[i].textContent || "";
            }
        }
        return "";
    }
}

window.onload = function() {
    initChat();
};