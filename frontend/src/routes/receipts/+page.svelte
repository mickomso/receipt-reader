<script lang="ts">
  import { onMount } from 'svelte';
  import { deleteReceipt, listReceipts } from '$lib/api';
  import StatusBadge from '$lib/components/StatusBadge.svelte';
  import type { ReceiptListItem } from '$lib/types';

  let receipts: ReceiptListItem[] = [];
  let loading = true;
  let error = '';
  let deletingId = '';
  let pendingDelete: { id: string; label: string } | null = null;

  // Resumen operativo
  let summary = {
    total: 0,
    confirmed: 0,
    pending: 0,
    needsReview: 0,
    failed: 0,
    totalAmount: 0
  };

  onMount(async () => {
    try {
      const data = await listReceipts(0, 100);
      receipts = data.items;
      computeSummary();
    } catch (err: unknown) {
      error = err instanceof Error ? err.message : 'Error al cargar los tickets.';
    } finally {
      loading = false;
    }
  });

  function computeSummary() {
    summary = {
      total: receipts.length,
      confirmed: 0,
      pending: 0,
      needsReview: 0,
      failed: 0,
      totalAmount: 0
    };

    for (const r of receipts) {
      switch (r.status) {
        case 'confirmed': summary.confirmed++; break;
        case 'extracted':
        case 'processing':
        case 'uploaded': summary.pending++; break;
        case 'needs_review': summary.needsReview++; break;
        case 'failed': summary.failed++; break;
      }
      summary.totalAmount += Number(r.totals?.calculated_total ?? 0);
    }
  }

  function fmtDate(d: string | null): string {
    if (!d) return '—';
    return new Date(d).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }

  function fmtAmount(val: string | null): string {
    if (!val) return '—';
    return parseFloat(val).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €';
  }

  function requestDelete(id: string, label: string) {
    pendingDelete = { id, label };
  }

  async function removeReceipt() {
    if (!pendingDelete) return;
    const { id } = pendingDelete;
    pendingDelete = null;
    deletingId = id;
    error = '';
    try {
      await deleteReceipt(id);
      receipts = receipts.filter((receipt) => receipt.id !== id);
      computeSummary();
    } catch (err: unknown) {
      error = err instanceof Error ? err.message : 'No se pudo eliminar el ticket.';
    } finally {
      deletingId = '';
    }
  }

</script>

<svelte:head>
  <title>Receipt Reader | Mis tickets</title>
</svelte:head>

<div class="workspace">
  <!-- Título y acción principal -->
  <section class="section-header">
    <div class="header-content">
      <p class="eyebrow">Mesa de trabajo</p>
      <h1>Mis tickets</h1>
      <p class="lede">Lista escaneable de alta densidad. Revisa estados, totales y accede al detalle.</p>
    </div>
  </section>

  <!-- Resumen operativo -->
  <section class="operational-summary" aria-label="Resumen operativo">
    <div class="summary-grid">
      <div class="summary-item">
        <span class="summary-label">Total</span>
        <span class="summary-value">{summary.total}</span>
      </div>
      <div class="summary-item accent">
        <span class="summary-label">Confirmados</span>
        <span class="summary-value">{summary.confirmed}</span>
      </div>
      <div class="summary-item warning">
        <span class="summary-label">Pendientes</span>
        <span class="summary-value">{summary.pending}</span>
      </div>
      <div class="summary-item warning">
        <span class="summary-label">Revisar</span>
        <span class="summary-value">{summary.needsReview}</span>
      </div>
      <div class="summary-item danger">
        <span class="summary-label">Error</span>
        <span class="summary-value">{summary.failed}</span>
      </div>
      <div class="summary-item accent">
        <span class="summary-label">Importe total</span>
        <span class="summary-value">{fmtAmount(String(summary.totalAmount.toFixed(2)))}</span>
      </div>
    </div>
  </section>

  <!-- Lista de tickets -->
  {#if loading}
    <div class="loading-state" aria-live="polite">
      <div class="spinner"></div>
      <p>Cargando tickets…</p>
    </div>
  {:else if error}
    <div class="alert alert-error">{error}</div>
  {:else if receipts.length === 0}
    <div class="empty-state card">
      <p>No has subido ningún ticket todavía.</p>
      <a href="/" class="btn btn-primary">Subir primer ticket</a>
    </div>
  {:else}
    <div class="list-heading">
      <div>
        <h2>Tickets registrados</h2>
        <p>Consulta el estado y el importe de cada ticket.</p>
      </div>
      <span class="list-count">{receipts.length} resultados</span>
    </div>
    <div class="tickets-table-wrapper">
      <table class="tickets-table" aria-label="Lista de tickets">
        <thead>
          <tr>
            <th scope="col">Comercio</th>
            <th scope="col">Fecha</th>
            <th scope="col" class="col-total">Total calculado</th>
            <th scope="col" class="col-status">Estado</th>
            <th scope="col" class="col-date">Creado</th>
            <th scope="col" class="col-action"></th>
          </tr>
        </thead>
        <tbody>
          {#each receipts as r (r.id)}
            <tr>
              <td class="col-commerce" data-label="Comercio">
                <div class="commerce-cell">
                  <span class="commerce-name">{r.commerce ?? '—'}</span>
                  <span class="commerce-filename">{r.filename}</span>
                </div>
              </td>
              <td class="col-date-main" data-label="Fecha">{fmtDate(r.date)}</td>
              <td class="col-total" data-label="Total calculado">
                {fmtAmount(r.totals?.calculated_total ?? null)}
              </td>
              <td class="col-status" data-label="Estado">
                <StatusBadge status={r.status} />
              </td>
              <td class="col-date-created" data-label="Creado">{fmtDate(r.created_at)}</td>
              <td class="col-action" data-label="Acción">
                <div class="row-actions">
                  <a href="/receipts/{r.id}" class="btn btn-outline btn-sm" aria-label="Ver detalle de {r.commerce ?? r.filename}">
                    Ver
                  </a>
                  <button
                    type="button"
                    class="btn btn-danger btn-sm"
                    disabled={deletingId === r.id}
                    on:click={() => requestDelete(r.id, r.commerce ?? r.filename)}
                    aria-label="Eliminar {r.commerce ?? r.filename}"
                  >
                    {deletingId === r.id ? '…' : 'Eliminar'}
                  </button>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
</div>

{#if pendingDelete}
  <div class="modal-backdrop" role="presentation">
    <div
      class="confirm-modal"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="delete-title"
      aria-describedby="delete-description"
    >
      <div class="modal-mark" aria-hidden="true">!</div>
      <p class="modal-eyebrow">Eliminar ticket</p>
      <h2 id="delete-title">¿Eliminar este ticket?</h2>
      <p id="delete-description">
        Se eliminará <strong>{pendingDelete.label}</strong> junto con sus datos e imagen. Esta acción no se puede deshacer.
      </p>
      <div class="modal-actions">
        <button type="button" class="btn btn-outline" on:click={() => (pendingDelete = null)}>
          Cancelar
        </button>
        <button type="button" class="btn btn-danger-confirm" on:click={removeReceipt}>
          Eliminar ticket
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  /* ========== WORKSPACE LAYOUT ========== */
  .workspace {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    gap: 0;
  }

  /* ========== SECTION HEADER ========== */
  .section-header {
    display: flex;
    flex-wrap: wrap;
    align-items: flex-end;
    justify-content: space-between;
    gap: 16px;
    padding: 24px 0 0;
  }

  .header-content {
    flex: 1;
    min-width: 280px;
  }

  .eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin: 0 0 20px;
    color: var(--accent);
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
  }

  .eyebrow::before {
    width: 22px;
    height: 1px;
    background: var(--accent);
    content: '';
  }

  h1 {
    max-width: 620px;
    margin: 0;
    font-family: var(--font-display);
    font-size: clamp(42px, 5vw, 68px);
    font-weight: 800;
    letter-spacing: -0.055em;
    line-height: 0.98;
  }

  .lede {
    margin: 28px 0 24px;
    color: var(--muted);
    font-size: 17px;
    line-height: 1.65;
    white-space: nowrap;
  }

  /* ========== OPERATIONAL SUMMARY ========== */
  .operational-summary {
    margin-bottom: 28px;
  }

  .summary-grid {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    align-items: end;
    gap: 0;
    border-bottom: 1px solid var(--border);
  }

  .summary-item {
    display: flex;
    flex-direction: column;
    gap: 5px;
    min-height: 68px;
    padding: 0 18px 14px;
    border-right: 1px solid var(--border);
  }

  .summary-item:first-child {
    padding-left: 0;
    border-top: 2px solid var(--accent);
    padding-top: 10px;
  }

  .summary-item:last-child {
    border-right: 0;
    padding-right: 0;
    border-top: 2px solid var(--accent);
    padding-top: 10px;
  }

  .summary-label {
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--muted);
  }

  .summary-value {
    font-family: var(--font-display);
    font-size: 24px;
    font-weight: 700;
    color: var(--fg);
    line-height: 1.2;
  }

  /* ========== LOADING / EMPTY ========== */
  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 60px 20px;
    gap: 16px;
    color: var(--muted);
  }

  .loading-state .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .empty-state {
    text-align: center;
    padding: 48px 24px;
  }

  .empty-state p {
    margin: 0 0 16px;
    color: var(--muted);
  }

  .empty-state .btn {
    margin-top: 8px;
  }

  .list-heading {
    display: flex;
    align-items: end;
    justify-content: space-between;
    gap: 16px;
    margin: 0 0 14px;
  }

  .list-heading h2 {
    margin: 0;
    color: var(--fg);
    font-family: var(--font-display);
    font-size: 18px;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.2;
  }

  .list-heading p {
    margin: 5px 0 0;
    color: var(--muted);
    font-size: 13px;
    line-height: 1.4;
  }

  .list-count {
    flex-shrink: 0;
    color: var(--muted);
    font-size: 12px;
  }

  /* ========== TICKETS TABLE ========== */
  .tickets-table-wrapper {
    overflow-x: auto;
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    background: rgba(18, 29, 48, 0.28);
  }

  .tickets-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
    font-family: var(--font-body);
  }

  .tickets-table thead {
    position: sticky;
    top: 0;
    z-index: 1;
  }

  .tickets-table th {
    padding: 12px 16px;
    text-align: left;
    font-family: var(--font-display);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--muted);
    background: var(--surface-soft);
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
  }

  .tickets-table td {
    padding: 16px;
    border-bottom: 1px solid var(--border);
    vertical-align: middle;
    color: var(--fg);
  }

  .tickets-table tbody tr:last-child td {
    border-bottom: none;
  }

  .tickets-table tbody tr {
    transition: background 0.12s ease;
  }

  .tickets-table tbody tr:hover td {
    background: rgba(56, 189, 248, 0.06);
  }

  .tickets-table :global(.badge) {
    min-height: 26px;
    padding: 4px 9px;
    border: 1px solid currentColor;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    text-transform: none;
  }

  .tickets-table :global(.badge-uploaded) {
    background: rgba(56, 189, 248, 0.12);
  }

  .tickets-table :global(.badge-processing),
  .tickets-table :global(.badge-needs_review) {
    background: rgba(245, 158, 11, 0.12);
  }

  .tickets-table :global(.badge-extracted),
  .tickets-table :global(.badge-confirmed) {
    background: rgba(34, 197, 94, 0.12);
  }

  .tickets-table :global(.badge-failed) {
    background: rgba(239, 68, 68, 0.12);
  }

  /* Columnas */
  .col-commerce { min-width: 280px; }
  .col-date { width: 120px; }
  .col-date-main { width: 110px; }
  .col-total { width: 110px; text-align: right; font-family: var(--font-display); font-weight: 600; }
  .col-status { width: 130px; }
  .col-date-created { width: 120px; color: var(--muted); font-size: 13px; }
  .col-action { width: 160px; text-align: right; }

  .row-actions {
    display: inline-flex;
    align-items: center;
    justify-content: flex-end;
    gap: 8px;
  }

  .btn-sm {
    min-height: 32px;
    padding: 0 10px;
    border-radius: 7px;
    font-size: 0.78rem;
  }

  .btn-danger {
    border-color: rgba(253, 164, 175, 0.45);
    color: var(--danger);
    background: transparent;
  }

  .btn-danger:hover:not(:disabled) {
    background: rgba(253, 164, 175, 0.1);
    border-color: var(--danger);
  }

  .btn-danger:disabled {
    cursor: wait;
    opacity: 0.6;
  }

  .modal-backdrop {
    position: fixed;
    inset: 0;
    z-index: 50;
    display: grid;
    place-items: center;
    padding: 24px;
    background: rgba(7, 15, 29, 0.78);
    backdrop-filter: blur(6px);
  }

  .confirm-modal {
    width: min(100%, 440px);
    padding: 28px;
    border: 1px solid var(--border);
    border-top: 2px solid var(--danger);
    background: var(--surface);
    box-shadow: 0 24px 70px rgba(0, 0, 0, 0.4);
  }

  .modal-mark {
    display: grid;
    width: 30px;
    height: 30px;
    margin-bottom: 18px;
    place-items: center;
    border: 1px solid rgba(253, 164, 175, 0.5);
    border-radius: 50%;
    color: var(--danger);
    font-family: var(--font-display);
    font-weight: 800;
  }

  .modal-eyebrow {
    margin: 0 0 8px;
    color: var(--danger);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }

  .confirm-modal h2 {
    margin: 0;
    font-family: var(--font-display);
    font-size: 24px;
    letter-spacing: -0.03em;
  }

  .confirm-modal p:not(.modal-eyebrow) {
    margin: 12px 0 0;
    color: var(--muted);
    font-size: 14px;
    line-height: 1.6;
  }

  .confirm-modal strong {
    color: var(--fg);
    font-weight: 600;
  }

  .modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
    margin-top: 26px;
  }

  .btn-danger-confirm {
    border-color: var(--danger);
    background: var(--danger);
    color: #26151b;
  }

  .btn-danger-confirm:hover {
    border-color: #fecdd3;
    background: #fecdd3;
  }

  /* Celda comercio */
  .commerce-cell {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .commerce-name {
    font-weight: 600;
    color: var(--fg);
  }

  .commerce-filename {
    font-size: 12px;
    color: var(--muted);
    font-family: var(--font-body);
  }

  /* ========== MOBILE REFlow ========== */
  @media (max-width: 900px) {
    .tickets-table thead {
      display: none;
    }

    .tickets-table,
    .tickets-table tbody,
    .tickets-table tr,
    .tickets-table td {
      display: block;
      width: 100%;
    }

    .tickets-table tr {
      padding: 16px 0;
      border-bottom: 1px solid var(--border);
      background: transparent;
    }

    .tickets-table tr:not(:first-child) {
      margin-top: 0;
      border-radius: 0;
      border: 0;
      border-bottom: 1px solid var(--border);
    }

    .tickets-table td {
      padding: 6px 0;
      border: none;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }

    .tickets-table td::before {
      content: attr(data-label);
      font-family: var(--font-display);
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: var(--muted);
      flex-shrink: 0;
    }

    .col-commerce { min-width: auto; }
    .col-date { display: none; }
    .col-date-main::before { content: 'Fecha'; }
    .col-total::before { content: 'Total'; }
    .col-status::before { content: 'Estado'; }
    .col-date-created::before { content: 'Creado'; }
    .col-action::before { content: ''; }
    .col-action {
      text-align: left;
      padding-top: 8px;
      border-top: 1px solid var(--border);
      margin-top: 4px;
    }
    .row-actions { display: flex; width: 100%; }
    .row-actions .btn { flex: 1; justify-content: center; }

    .commerce-cell {
      flex-direction: row;
      align-items: baseline;
      gap: 10px;
    }

    .commerce-filename {
      font-size: 11px;
    }
  }

  @media (max-width: 640px) {
    .section-header {
      flex-direction: column;
      align-items: stretch;
      padding: 24px 0 0;
    }

    .confirm-modal {
      padding: 24px;
    }

    .modal-actions {
      flex-direction: column-reverse;
    }

    .modal-actions .btn {
      width: 100%;
    }

    .lede {
      white-space: normal;
    }

    .list-heading {
      align-items: flex-start;
      flex-direction: column;
      gap: 6px;
      margin-bottom: 12px;
    }

    .summary-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .summary-item,
    .summary-item:first-child,
    .summary-item:last-child {
      padding: 10px 12px;
      border-top: 0;
    }

    .summary-item:nth-child(2n) {
      border-right: 0;
    }

  }

  @media (max-width: 420px) {
    .summary-grid {
      grid-template-columns: 1fr;
    }

    .summary-item,
    .summary-item:first-child,
    .summary-item:last-child {
      padding: 10px 0;
      border-right: 0;
      border-top: 0;
      border-bottom: 1px solid var(--border);
    }

    .summary-item:last-child {
      border-bottom: 0;
    }

  }
</style>
