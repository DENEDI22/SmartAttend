/**
 * Admin inline-edit change detection.
 * Tracks inputs/selects with data-original attribute.
 * Enables save/reset buttons only when changes exist.
 */
document.addEventListener('DOMContentLoaded', () => {
  // --- Inline edit change detection ---
  const form = document.getElementById('edit-form');
  if (form) {
    const inputs = form.querySelectorAll('input[data-original], select[data-original]');
    const saveBtn = document.getElementById('save-btn');
    const resetBtn = document.getElementById('reset-btn');

    function hasChanges() {
      return Array.from(inputs).some(el => el.value !== el.dataset.original);
    }

    function updateButtons() {
      const changed = hasChanges();
      if (saveBtn) saveBtn.disabled = !changed;
      if (resetBtn) resetBtn.disabled = !changed;
    }

    inputs.forEach(el => el.addEventListener('input', updateButtons));

    if (saveBtn) {
      saveBtn.addEventListener('click', () => {
        const submitForm = document.createElement('form');
        submitForm.method = 'POST';
        submitForm.action = form.dataset.action || '/admin/devices/update';
        inputs.forEach(el => {
          const hidden = document.createElement('input');
          hidden.type = 'hidden';
          hidden.name = el.name;
          hidden.value = el.value;
          submitForm.appendChild(hidden);
        });
        document.body.appendChild(submitForm);
        submitForm.submit();
      });
    }

    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        inputs.forEach(el => { el.value = el.dataset.original; });
        updateButtons();
      });
    }
  }

  // --- Schedule conflict check (used in Plan 04) ---
  const conflictForm = document.querySelector('[data-conflict-check]');
  if (conflictForm) {
    const addBtn = conflictForm.querySelector('[data-add-btn]');
    const errorDiv = conflictForm.querySelector('[data-conflict-error]');
    const fields = ['device_id', 'weekday', 'start_time', 'end_time'];

    async function checkConflict() {
      const params = new URLSearchParams();
      let allFilled = true;
      fields.forEach(f => {
        const el = conflictForm.querySelector(`[name="${f}"]`);
        if (el && el.value) {
          params.set(f, el.value);
        } else {
          allFilled = false;
        }
      });
      if (!allFilled) {
        if (addBtn) addBtn.disabled = true;
        if (errorDiv) errorDiv.textContent = '';
        return;
      }
      try {
        const resp = await fetch(`/admin/api/schedule/check-conflict?${params}`);
        const data = await resp.json();
        if (data.conflict) {
          if (errorDiv) errorDiv.textContent = data.message;
          if (addBtn) addBtn.disabled = true;
        } else {
          if (errorDiv) errorDiv.textContent = '';
          if (addBtn) addBtn.disabled = false;
        }
      } catch {
        if (addBtn) addBtn.disabled = false;
        if (errorDiv) errorDiv.textContent = '';
      }
    }

    fields.forEach(f => {
      const el = conflictForm.querySelector(`[name="${f}"]`);
      if (el) el.addEventListener('change', checkConflict);
    });
  }
});
