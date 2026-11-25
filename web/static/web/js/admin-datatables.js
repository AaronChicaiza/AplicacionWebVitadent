document.addEventListener('DOMContentLoaded', function () {
  if (window.jQuery && window.Swal) {
    window.jQuery(function ($) {
      const notices = $('.admin-notification');
      if (!notices.length) return;
      const toast = window.Swal.mixin({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 4200,
        timerProgressBar: true,
        didOpen: function (element) {
          element.addEventListener('mouseenter', window.Swal.stopTimer);
          element.addEventListener('mouseleave', window.Swal.resumeTimer);
        }
      });
      notices.each(function () {
        const notice = $(this);
        const type = (notice.data('message-type') || 'info').split(' ')[0];
        const message = $.trim(notice.text());
        const lowerMessage = message.toLocaleLowerCase('es');
        let title = 'Información';
        let icon = 'info';
        let iconColor;
        if (type === 'success') {
          icon = 'success';
          iconColor = '#218838';
          if (/actualiz|guardaron/.test(lowerMessage)) title = 'Actualizado exitosamente';
          else if (/eliminó/.test(lowerMessage)) title = 'Eliminado exitosamente';
          else if (/registr|cread|creó|guardó/.test(lowerMessage)) title = 'Registrado exitosamente';
          else title = 'Operación realizada exitosamente';
        } else if (type === 'error') {
          title = 'No se pudo completar';
          icon = 'error';
          iconColor = '#c83e45';
        } else if (type === 'warning') {
          title = 'Revisa esta acción';
          icon = 'warning';
          iconColor = '#d08a18';
        }
        toast.fire({ icon: icon, iconColor: iconColor, title: title, text: message });
        notice.attr('hidden', 'hidden');
      });
    });
  }

  const language = {
    emptyTable: 'No hay registros para mostrar',
    info: 'Mostrando _START_ a _END_ de _TOTAL_ registros',
    infoEmpty: 'Mostrando 0 registros',
    infoFiltered: '(filtrado de _MAX_ registros)',
    lengthMenu: 'Mostrar _MENU_ registros',
    loadingRecords: 'Cargando…',
    processing: 'Procesando…',
    search: 'Buscar:',
    zeroRecords: 'No se encontraron coincidencias',
    paginate: { first: 'Primera', last: 'Última', next: 'Siguiente', previous: 'Anterior' },
    aria: { sortAscending: ': ordenar ascendente', sortDescending: ': ordenar descendente' },
    buttons: { copyTitle: 'Copiado', copySuccess: { 1: 'Se copió una fila', _: 'Se copiaron %d filas' } }
  };

  document.querySelectorAll('table[data-datatable]').forEach(function (table) {
    if (!window.DataTable) return;
    const actionColumn = Number(table.dataset.actionColumn || -1);
    const exportOptions = { columns: function (index) { return index !== actionColumn; } };
    const buttons = table.dataset.export === 'none' ? [] : [
      { extend: 'copyHtml5', text: 'Copiar', exportOptions: exportOptions },
      { extend: 'csvHtml5', text: 'CSV', exportOptions: exportOptions },
      { extend: 'excelHtml5', text: 'Excel', exportOptions: exportOptions },
      { extend: 'pdfHtml5', text: 'PDF', orientation: 'landscape', pageSize: 'A4', exportOptions: exportOptions }
    ];
    new DataTable(table, {
      pageLength: 10,
      lengthMenu: [10, 25, 50, 100],
      order: [],
      autoWidth: false,
      scrollX: true,
      columnDefs: actionColumn >= 0 ? [{ targets: actionColumn, orderable: false, searchable: false }] : [],
      language: language,
      layout: {
        topStart: {
          buttons: buttons
        },
        topEnd: 'search',
        bottomStart: 'info',
        bottomEnd: 'paging'
      }
    });
  });

  document.querySelectorAll('[data-open-crud]').forEach(function (button) {
    button.addEventListener('click', function () {
      const modalElement = document.getElementById(button.dataset.openCrud);
      if (!modalElement || !window.bootstrap) return;
      const form = modalElement.querySelector('form');
      if (form) {
        form.reset();
        const action = form.querySelector('[name="accion"]');
        const id = form.querySelector('[name="registro_id"]');
        if (action) action.value = 'crear';
        if (id) id.value = '';
      }
      const title = modalElement.querySelector('[data-modal-title]');
      if (title) title.textContent = button.dataset.createTitle || 'Agregar registro';
      window.bootstrap.Modal.getOrCreateInstance(modalElement).show();
    });
  });

  document.querySelectorAll('[data-edit-record]').forEach(function (button) {
    button.addEventListener('click', function () {
      const modalElement = document.getElementById(button.dataset.editRecord);
      if (!modalElement || !window.bootstrap) return;
      const form = modalElement.querySelector('form');
      if (!form) return;
      form.reset();
      const action = form.querySelector('[name="accion"]');
      const id = form.querySelector('[name="registro_id"]');
      if (action) action.value = 'editar';
      if (id) id.value = button.dataset.recordId || '';
      Object.keys(button.dataset).forEach(function (key) {
        if (!key.startsWith('record')) return;
        const fieldName = key.slice(6).replace(/^[A-Z]/, function (letter) { return letter.toLowerCase(); });
        const field = form.elements.namedItem(fieldName);
        if (!field) return;
        if (field.type === 'checkbox') field.checked = button.dataset[key] === 'true';
        else field.value = button.dataset[key];
      });
      const title = modalElement.querySelector('[data-modal-title]');
      if (title) title.textContent = button.dataset.editTitle || 'Editar registro';
      window.bootstrap.Modal.getOrCreateInstance(modalElement).show();
    });
  });

  document.querySelectorAll('form[data-delete-confirm]').forEach(function (form) {
    form.addEventListener('submit', function (event) {
      if (form.dataset.confirmed === 'true') return;
      event.preventDefault();
      const submitter = event.submitter;
      const message = form.dataset.deleteConfirm || 'Se eliminará este registro si no tiene información asociada.';
      const confirmed = window.Swal
        ? window.Swal.fire({
            title: '¿Confirmas esta acción?',
            text: message,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Continuar',
            cancelButtonText: 'Volver',
            confirmButtonColor: '#a43f36',
            cancelButtonColor: '#536662'
          }).then(function (result) { return result.isConfirmed; })
        : Promise.resolve(window.confirm(message));
      confirmed.then(function (ok) {
        if (!ok) return;
        form.dataset.confirmed = 'true';
        if (submitter) form.requestSubmit(submitter);
        else form.requestSubmit();
      });
    });
  });

  document.querySelectorAll('.admin-crud-form').forEach(function (form) {
    form.querySelectorAll('input:not([type="hidden"]):not([type="checkbox"]), select, textarea').forEach(function (field) {
      field.classList.add(field.tagName === 'SELECT' ? 'form-select' : 'form-control');
    });
  });
});
