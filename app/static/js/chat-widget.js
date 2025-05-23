(function () {
  const iframeId = "chatbot-widget-iframe";
  const widgetUrl = "https://testai.ucu.org.ua/widget"; // !!!!!!!!!!!!!

  function createIframe() {
    const iframe = document.createElement("iframe");
    iframe.src = widgetUrl;
    iframe.id = iframeId;
    iframe.style.position = "fixed";
    iframe.style.bottom = "20px";
    iframe.style.right = "20px";
    iframe.style.width = "360px";
    iframe.style.height = "500px";
    iframe.style.border = "none";
    iframe.style.zIndex = "9999";
    iframe.style.boxShadow = "0 4px 16px rgba(0,0,0,0.2)";
    iframe.style.borderRadius = "12px";
    document.body.appendChild(iframe);
  }

  function removeIframe() {
    const iframe = document.getElementById(iframeId);
    if (iframe) {
      iframe.remove();
    }
  }

  const button = document.createElement("button");
  button.innerText = "ðŸ’¬";
  button.title = "Ð’Ñ–Ð´ÐºÑ€Ð¸Ñ‚Ð¸ Ñ‡Ð°Ñ‚ Ð· Ð±Ð¾Ñ‚Ð¾Ð¼";
  button.style.position = "fixed";
  button.style.bottom = "20px";
  button.style.right = "20px";
  button.style.width = "60px";
  button.style.height = "60px";
  button.style.borderRadius = "50%";
  button.style.border = "none";
  button.style.backgroundColor = "#4CAF50";
  button.style.color = "white";
  button.style.fontSize = "24px";
  button.style.cursor = "pointer";
  button.style.zIndex = "9998";
  button.style.boxShadow = "0 2px 8px rgba(0,0,0,0.2)";

  let opened = false;

  button.addEventListener("click", function () {
    if (!opened) {
      createIframe();
      opened = true;
    } else {
      removeIframe();
      opened = false;
    }
  });

  window.addEventListener("message", (event) => {
    if (event.data === "close-chatbot-widget") {
      removeIframe();
      opened = false;
    }
  });

  document.body.appendChild(button);
})();
