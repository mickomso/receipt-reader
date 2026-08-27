<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { getReceipt, patchReceipt, confirmReceipt } from '$lib/api';
  import type { ReceiptDetail, ReceiptItem } from '$lib/types';
  import StatusBadge from '$lib/components/StatusBadge.svelte';
  import ReceiptTable from '$lib/components/ReceiptTable.svelte';
  import TotalsCard from '$lib/components/TotalsCard.svelte';
  import ConfidenceBadge from '$lib/components/ConfidenceBadge.svelte';

  let receipt: ReceiptDetail | null = null;
  let loading = true;
  let loadError = '';
  let confirming = false;
  let confirmError = '';
  let confirmSuccess = false;
  let editedItems: ReceiptItem[] = [];

  $: id = $page.params.id ?? '';

  onMount(async () => {
    if (!id) return;
    try {
      receipt = await getReceipt(id);
      editedItems = receipt.items;
    } catch (err: unknown) {
      loadError = err instanceof Error ? err.message : 'Error al cargar el ticket.';
    } finally {
      loading = false;
    }
  });

  function onItemsChange(event: CustomEvent<ReceiptItem[]>) {
    editedItems = event.detail;
  }

  async function confirm() {
    if (!receipt) return;
    confirming = true;
    confirmError = '';
    try {
      const corrections = editedItems !== receipt.items ? { items: editedItems } : null;
      receipt = await confirmReceipt(id, corrections);
      confirmSuccess = true;
    } catch (err: unknown) {
      confirmError = err instanceof Error ? err.message : 'Error al confirmar.';
    } finally {
      confirming = false;
    }
  }

  function fmt(val: string | null): string {
    return val ?? 'No disponible';
  }

  $: canConfirm =
    receipt?.status === 'extracted' || receipt?.status === 'needs_review';

  $: hasMathIssues =
    receipt?.totals?.totals_valid === false ||
    receipt?.items.some((i) => i.line_valid === false) ||
    false;

  $: overallConfidence =
    receipt?.items.length
      ? receipt.items.reduce((sum, i) => sum + (i.confidence ?? 0), 0) / receipt.items.length
      : null;
</script>

<svelte:head>
  <title>Receipt Reader — Detalle ticket</title>
</svelte:head>

<div class="breadcrumb">
  <a href="/receipts">← Mis tickets</a>
</div>

{#if loading}
  <p>Cargando…</p>
{:else if loadError}
  <div class="alert alert-error">{loadError}</div>
{:else if receipt}
  <div class="detail-header">
    <div class="detail-title">
      <h1>{receipt.commerce ?? receipt.filename}</h1>
      <StatusBadge status={receipt.status} />
    </div>
    <div class="meta">
      <span>📅 {fmt(receipt.date)}</span>
      <span>🕐 {fmt(receipt.time)}</span>
      <span>🏪 {fmt(receipt.commerce)}</span>
      <span>🔖 Nº {fmt(receipt.ticket_number)}</span>
      <span>💳 {fmt(receipt.payment_method)}</span>
    </div>
  </div>

  {#if receipt.status === 'failed'}
    <div class="alert alert-error">
      <strong>Error en el procesamiento:</strong>
      {receipt.error_message ?? 'Error desconocido. Vuelve a subir la imagen.'}
    </div>
  {/if}

  {#if receipt.status === 'needs_review'}
    <div class="alert alert-warning">
      Este ticket requiere revisión manual. Comprueba y corrige los valores marcados antes de confirmar.
    </div>
  {/if}

  {#if hasMathIssues}
    <div class="alert alert-warning">
      Se han detectado <strong>discrepancias matemáticas</strong>. Las líneas o el total no cuadran.
      Revisa los valores antes de confirmar.
    </div>
  {/if}

  {#if confirmSuccess}
    <div class="alert alert-success">Ticket confirmado correctamente.</div>
  {/if}

  {#if confirmError}
    <div class="alert alert-error">{confirmError}</div>
  {/if}

  <!-- Items table -->
  <div class="section">
    <div class="section-header">
      <h2>Artículos ({receipt.items.length})</h2>
      {#if overallConfidence != null}
        <span class="conf-label">Confianza global:
          <ConfidenceBadge confidence={overallConfidence} needsReview={receipt.status === 'needs_review'} />
        </span>
      {/if}
    </div>
    <div class="card">
      <ReceiptTable
        items={receipt.items}
        editable={canConfirm}
        on:change={onItemsChange}
      />
    </div>
  </div>

  <!-- Totals -->
  {#if receipt.totals}
    <div class="section">
      <TotalsCard totals={receipt.totals} currency={receipt.currency} />
    </div>
  {/if}

  <!-- Confirm button -->
  {#if canConfirm}
    <div class="confirm-bar">
      <button
        class="btn btn-success"
        disabled={confirming}
        on:click={confirm}
      >
        {confirming ? 'Confirmando…' : '✓ Confirmar ticket'}
      </button>
      <span class="hint">
        Una vez confirmado, el ticket quedará archivado y no podrá editarse.
      </span>
    </div>
  {/if}
{/if}

<style>
  .breadcrumb { margin-bottom: 1.5rem; }
  .detail-header { margin-bottom: 1.5rem; }
  .detail-title {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: .5rem;
  }
h1, h2 {
    font-family: 'Montserrat', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }
h1 { margin: 0; font-size: 1.5rem; }
  h2 { margin: 0; font-size: 1.1rem; }
  .meta {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    color: var(--color-muted);
    font-size: .875rem;
  }
  .section { margin-bottom: 1.5rem; }
  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: .75rem;
  }
  .conf-label {
    font-size: .85rem;
    color: var(--color-muted);
    display: flex;
    align-items: center;
    gap: .5rem;
  }
  .confirm-bar {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    padding: 1.25rem 0;
  }
  .hint { color: var(--color-muted); font-size: .875rem; }
</style>
