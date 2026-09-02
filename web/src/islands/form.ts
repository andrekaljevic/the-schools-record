/** Inline validation, JSON submission and honest receipts for the record's forms. */
import { esc } from '../lib/html';

interface Receipt { status: 'forwarded' | 'failed'; reference: string; detail: string; durable: boolean; fields: Record<string, string>; error?: string; errors?: Record<string, string> }

for (const form of document.querySelectorAll<HTMLFormElement>('form[data-island="form"]')) {
  const started = form.querySelector<HTMLInputElement>('[data-started]');
  if (started) started.value = String(Date.now());
  const status = form.querySelector<HTMLElement>('[data-status]')!;
  const receiptNode = form.querySelector<HTMLElement>('[data-receipt]')!;
  const kindLabel = form.dataset.kind === 'correction-report' ? 'Report' : 'Enquiry';

  const fields = () => [...form.querySelectorAll<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>('[name]')].filter((el) => el.name !== 'website' && el.name !== 'started');

  function setError(el: HTMLElement, message: string | null): void {
    const wrap = el.closest<HTMLElement>('.field, .form-consent');
    if (!wrap) return;
    let note = wrap.querySelector<HTMLElement>('.field-error');
    if (message) {
      if (!note) { note = document.createElement('p'); note.className = 'field-error'; note.id = `${el.id}-error`; wrap.appendChild(note); }
      note.textContent = message;
      wrap.classList.add('is-invalid');
      el.setAttribute('aria-invalid', 'true');
      el.setAttribute('aria-describedby', note.id);
    } else {
      note?.remove();
      wrap.classList.remove('is-invalid');
      el.removeAttribute('aria-invalid');
      el.removeAttribute('aria-describedby');
    }
  }

  function validate(): boolean {
    let firstInvalid: HTMLElement | null = null;
    for (const el of fields()) {
      let message: string | null = null;
      const value = el instanceof HTMLInputElement && el.type === 'checkbox' ? (el.checked ? 'on' : '') : el.value.trim();
      if (el.required && (value === '' || value === 'Select one')) message = el.type === 'checkbox' ? 'Please confirm the privacy notice.' : 'This field is required.';
      else if (el instanceof HTMLInputElement && el.type === 'email' && value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) message = 'Please give a valid email address.';
      else if (!(el instanceof HTMLSelectElement) && el.maxLength > 0 && value.length > el.maxLength) message = `Please keep this under ${el.maxLength} characters.`;
      setError(el, message);
      if (message && !firstInvalid) firstInvalid = el;
    }
    if (firstInvalid) { firstInvalid.focus(); status.textContent = 'Please complete every required field and confirm the privacy notice.'; return false; }
    status.textContent = '';
    return true;
  }

  function transcript(values: Record<string, string>): string {
    return Object.entries(values).filter(([, value]) => value !== '').map(([key, value]) => `${key}: ${value}`).join('\n');
  }

  function showReceipt(receipt: Receipt, values: Record<string, string>): void {
    const ok = receipt.status === 'forwarded';
    receiptNode.className = `form-receipt${ok ? '' : ' is-error'}`;
    receiptNode.innerHTML =
      `<p class="eyebrow">${ok ? `${kindLabel} received` : `${kindLabel} not recorded`}</p>` +
      `<h2>${ok ? 'Thank you. Your submission has been received for review.' : 'Your submission could not be stored.'}</h2>` +
      `<p>${esc(receipt.detail)} Reference <code>${esc(receipt.reference)}</code>.</p>` +
      `<p>No payment has been taken and no automated email has been sent. A human review is the next step.</p>` +
      (receipt.durable ? '' : '<p><strong>Please keep a copy.</strong> The entry below is your record of what was written.</p>') +
      `<details class="submission-copy" open><summary>Copy of your submission</summary><pre>${esc(transcript(values))}</pre></details>`;
    receiptNode.hidden = false;
    receiptNode.focus();
    for (const el of form.querySelectorAll<HTMLElement>('.form-grid, .form-actions')) el.hidden = ok;
  }

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!validate()) return;
    const button = form.querySelector<HTMLButtonElement>('button[type="submit"]')!;
    button.disabled = true;
    status.textContent = 'Sending…';
    const values: Record<string, string> = {};
    for (const el of fields()) values[el.name] = el instanceof HTMLInputElement && el.type === 'checkbox' ? (el.checked ? 'on' : '') : el.value.trim();
    const payload = { ...values, website: form.querySelector<HTMLInputElement>('[name="website"]')?.value ?? '', started: started?.value ?? '' };
    let receipt: Receipt;
    try {
      const response = await fetch(form.action, { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json' }, body: JSON.stringify(payload) });
      const type = response.headers.get('content-type') ?? '';
      if (type.includes('application/json')) {
        receipt = (await response.json()) as Receipt;
        if (receipt.errors) {
          for (const [key, message] of Object.entries(receipt.errors)) { const el = form.querySelector<HTMLElement>(`[name="${key}"]`); if (el) setError(el, message); }
          status.textContent = receipt.error ?? 'Please check the highlighted fields.';
          button.disabled = false;
          return;
        }
      } else {
        receipt = { status: 'failed', reference: '—', detail: `No review endpoint is available at this address (HTTP ${response.status}), so the submission has not been stored.`, durable: false, fields: values };
      }
    } catch {
      receipt = { status: 'failed', reference: '—', detail: 'The submission could not be sent (network error), so it has not been stored.', durable: false, fields: values };
    }
    status.textContent = '';
    button.disabled = false;
    showReceipt(receipt, values);
  });
}

export {};
