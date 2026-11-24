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
  const form = jQuery('#formulario-cambio-clave');
  if (!form.length) return;
  form.validate({
    errorElement: 'span',
    errorClass: 'field-error',
    rules: {
      old_password: { required: true },
      new_password1: { required: true, minlength: 12 },
      new_password2: { required: true, equalTo: '#id_new_password1' }
    },
    messages: {
      old_password: { required: 'Escribe la contraseña temporal.' },
      new_password1: { required: 'Escribe una contraseña nueva.', minlength: 'Usa al menos 12 caracteres.' },
      new_password2: { required: 'Confirma la contraseña nueva.', equalTo: 'Las contraseñas no coinciden.' }
    },
    errorPlacement: function (error, element) {
      jQuery('#' + element.attr('name') + '-error').empty().append(error);
    },
    highlight: function (element) { jQuery(element).addClass('is-invalid').attr('aria-invalid', 'true'); },
    unhighlight: function (element) {
      jQuery(element).removeClass('is-invalid').removeAttr('aria-invalid');
      jQuery('#' + element.name + '-error').empty();
    },
    submitHandler: function (nativeForm) {
      const button = document.getElementById('change-password-submit');
      if (button) {
        button.disabled = true;
        button.querySelector('span').textContent = 'Actualizando…';
      }
      nativeForm.submit();
    }
  });
});
