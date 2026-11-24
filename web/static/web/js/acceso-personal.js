document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('[data-toggle-password]').forEach(function (button) {
    button.addEventListener('click', function () {
      const input = document.getElementById(button.dataset.togglePassword);
      if (!input) return;
      const visible = input.type === 'password';
      input.type = visible ? 'text' : 'password';
      button.setAttribute('aria-pressed', String(visible));
      button.setAttribute('aria-label', visible ? 'Ocultar contraseña' : 'Mostrar contraseña');
    });
  });

  if (!window.jQuery || !jQuery.validator) return;
  const form = jQuery('#formulario-acceso');
  if (!form.length) return;

  jQuery.validator.addMethod('usuarioVitadent', function (value, element) {
    return this.optional(element) || /^[A-Za-z0-9_.@+-]+$/.test(value);
  }, 'Usa letras, números y los símbolos . _ @ + -');

  form.validate({
    errorElement: 'span',
    errorClass: 'field-error',
    focusInvalid: true,
    rules: {
      username: { required: true, maxlength: 150, usuarioVitadent: true },
      password: { required: true }
    },
    messages: {
      username: {
        required: 'Escribe el usuario asignado por VitaDent.',
        maxlength: 'El usuario no puede superar 150 caracteres.'
      },
      password: { required: 'Escribe tu contraseña.' }
    },
    errorPlacement: function (error, element) {
      const target = element.attr('name') === 'username' ? '#username-error' : '#password-error';
      jQuery(target).empty().append(error);
    },
    highlight: function (element) {
      jQuery(element).addClass('is-invalid').attr('aria-invalid', 'true');
    },
    unhighlight: function (element) {
      jQuery(element).removeClass('is-invalid').removeAttr('aria-invalid');
      const target = element.name === 'username' ? '#username-error' : '#password-error';
      jQuery(target).empty();
    },
    submitHandler: function (nativeForm) {
      const button = document.getElementById('login-submit');
      if (button) {
        button.disabled = true;
        button.querySelector('span').textContent = 'Verificando acceso…';
      }
      nativeForm.submit();
    }
  });
});
