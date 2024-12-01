document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("message-input");
    const messages = document.getElementById("messages");

    form.addEventListener("submit", (e) => {
        e.preventDefault();
        const message = input.value.trim();

        if (message) {
            const newMessage = document.createElement("div");
            newMessage.textContent = `You: ${message}`;
            messages.appendChild(newMessage);

            input.value = "";
            messages.scrollTop = messages.scrollHeight;
        }
    });
});
