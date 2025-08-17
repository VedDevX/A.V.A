// ==================================================
// script.js → Handles frontend interaction for chatbot
// ==================================================

// ============================
// Function to send message to backend
// ============================
async function sendChat() {
    // Get the input box where user types messages
    const input = document.getElementById("msg");      

    // Get the container where chat messages appear
    const chatContainer = document.getElementById("chat"); 

    // Get the "Send" button element
    const btn = document.getElementById("sendBtn");    

    // Get the text typed by the user and remove leading/trailing spaces
    const userMsg = input.value.trim();

    // If user didn't type anything, show a prompt and return early
    if (!userMsg) {
        appendMessage("Bot", "Please type something so I can help.");
        return;
    }

    // Show user's message in the chat
    appendMessage("You", userMsg);

    // Clear the input box so user can type the next message
    input.value = ""; 

    try {
        // Disable the send button while waiting for response to prevent double clicks
        btn.disabled = true;

        // Send the message to backend via POST request
        const res = await fetch("/api/chat", {
            method: "POST", // HTTP POST method
            headers: { "Content-Type": "application/json" }, // Tell server we're sending JSON
            body: JSON.stringify({ message: userMsg }) // Convert message to JSON string
        });

        // If server returns an error status
        if (!res.ok) {
            let err = "Error communicating with server."; // Default error message
            try {
                // Try to parse error details from server response
                const maybeJson = await res.json();
                if (maybeJson && maybeJson.error) err = maybeJson.error;
            } catch (_) {} // Ignore parsing errors
            appendMessage("Bot", err); // Show error in chat
            return;
        }

        // Parse JSON response from server, e.g., { reply: "Hello!" }
        const data = await res.json(); 

        // Show bot's reply or fallback text if reply missing
        appendMessage("Bot", data.reply ?? "(no reply)");
    } catch (e) {
        // Catch network or other unexpected errors
        appendMessage("Bot", "Network error. Please try again.");
    } finally {
        // Re-enable the send button no matter what happens
        btn.disabled = false;
    }
}

// ============================
// Append a message to chat container
// ============================
function appendMessage(sender, msg) {
    // Get the chat container
    const chatContainer = document.getElementById("chat");

    // Create a new div element for this message
    const messageEl = document.createElement("div");

    // Add a class depending on sender ("You" → user, otherwise bot)
    messageEl.className = sender === "You" ? "user-msg" : "bot-msg";

    // Set the inner HTML to show sender name and message
    messageEl.innerHTML = `<strong>${sender}:</strong> ${msg}`;

    // Add this message div to the chat container
    chatContainer.appendChild(messageEl);

    // Scroll chat to bottom so newest message is visible
    scrollToBottom();
}

// ============================
// Auto-scroll to bottom
// ============================
function scrollToBottom() {
    // Get the chat container
    const chatContainer = document.getElementById("chat");

    // Set scroll position to the height of the container
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// ============================
// Support pressing ENTER key
// ============================
document.getElementById("msg").addEventListener("keydown", (e) => {
    // Check if Enter key is pressed without holding Shift
    if (e.key === "Enter" && !e.shiftKey) { 
        e.preventDefault(); // Prevent adding a new line
        sendChat();          // Send the message
    }
});
