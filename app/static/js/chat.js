document.getElementById("send-button").addEventListener("click", sendMessage);

document.addEventListener("DOMContentLoaded", function () {
    const chatBox = document.getElementById("chat-box");

    const greeting = document.createElement("div");
    greeting.className = "bot-message";
    greeting.innerHTML = "Привіт! Я твій віртуальний помічник. Запитай мене про щось.";
    
    chatBox.appendChild(greeting);
    chatBox.scrollTop = chatBox.scrollHeight;
});

document.getElementById("user-input").addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});

function sendMessage() {
    if (window.currentEventSource) {
        window.currentEventSource.close();
    }

    let userInput = document.getElementById("user-input").value;
    if (userInput.trim() === "") return;

    let chatBox = document.getElementById("chat-box");

    let userMessage = document.createElement("div");
    userMessage.className = "user-message";
    userMessage.textContent = userInput;
    chatBox.appendChild(userMessage);

    document.getElementById("user-input").value = "";

    let botMessage = document.createElement("div");
    botMessage.className = "bot-message";
    chatBox.appendChild(botMessage);

    const eventSource = new EventSource(`/ask-stream?question=${encodeURIComponent(userInput)}`);
    window.currentEventSource = eventSource;

    eventSource.addEventListener("end", function () {
        eventSource.close();
    });
    
    let fullText = "";
    botMessage.classList.add("typing");

    eventSource.onmessage = function (event) {
        if (event.data) {
            fullText += event.data;
            botMessage.innerHTML = fullText.replace(/\n/g, "<br>");
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    };

    eventSource.onopen = () => {
        console.log("✅ EventSource connection opened");
    };
    
    eventSource.onerror = (error) => {
        console.error("❌ EventSource error", error);
        botMessage.classList.remove("typing");
        eventSource.close();
    };
}
