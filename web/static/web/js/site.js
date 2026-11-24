document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#main-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      const open = toggle.getAttribute('aria-expanded') !== 'true';
      toggle.setAttribute('aria-expanded', String(open));
      nav.classList.toggle('open', open);
      toggle.setAttribute('aria-label', open ? 'Cerrar menú' : 'Abrir menú');
    });
  }

  const messages = document.querySelector('#chat-messages');
  const quickReplies = document.querySelector('#quick-replies');
  const chatForm = document.querySelector('#chat-form');
  const chatInput = document.querySelector('#chat-input');
  const csrf = chatForm?.querySelector('[name=csrfmiddlewaretoken]')?.value;
  const appendMessage = (kind, text) => {
    const row = document.createElement('div');
    row.className = `chat-message ${kind}-message`;
    if (kind === 'bot') {
      const avatar = document.createElement('span');
      avatar.className = 'message-avatar';
      avatar.textContent = 'VD';
      row.append(avatar);
    }
    const bubble = document.createElement('p');
    bubble.textContent = text;
    row.append(bubble);
    messages.append(row);
    row.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  };
  const sendMessage = async (text) => {
    appendMessage('user', text);
    if (quickReplies?.isConnected) quickReplies.remove();
    const button = chatForm?.querySelector('button[type=submit]');
    if (button) button.disabled = true;
    try {
      const response = await fetch('/citas/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf, 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify({ mensaje: text }),
        credentials: 'same-origin',
      });
      const result = await response.json();
      appendMessage('bot', result.respuesta || 'No pude procesar el mensaje. Intenta de nuevo.');
    } catch (_error) {
      appendMessage('bot', 'No se pudo conectar con el servidor. Tus datos no se enviaron; intenta nuevamente.');
    } finally {
      if (button) button.disabled = false;
      chatInput?.focus();
    }
  };
  if (quickReplies && messages) {
    quickReplies.addEventListener('click', (event) => {
      const button = event.target.closest('button[data-reply]');
      if (button) sendMessage(button.dataset.reply);
    });
  }
  if (chatForm && chatInput && messages) {
    chatForm.addEventListener('submit', (event) => {
      event.preventDefault();
      const text = chatInput.value.trim();
      if (!text || text.length > 500) return;
      chatInput.value = '';
      sendMessage(text);
    });
  }
  document.querySelector('#chat-reset')?.addEventListener('click', () => {
    sendMessage('reiniciar');
  });
});
