<script lang="ts">
  import { goto } from '$app/navigation';
  import UploadForm from '$lib/components/UploadForm.svelte';
  import { processReceipt } from '$lib/api';

  let processing = false;
  let processError = '';

  async function onUploaded(event: CustomEvent<string>) {
    const id = event.detail;
    processing = true;
    processError = '';
    try {
      await processReceipt(id);
      goto(`/receipts/${id}`);
    } catch (err: unknown) {
      processError = err instanceof Error ? err.message : 'Error al procesar el ticket.';
      goto(`/receipts/${id}`);
    } finally {
      processing = false;
    }
  }
</script>

<svelte:head>
  <title>Receipt Reader — Subir ticket</title>
</svelte:head>

<section class="hero">
  <h1>Lector de tickets de supermercado</h1>
  <p class="subtitle">
    Sube la imagen de tu ticket, Gemini extrae los productos, cantidades y precios,
    y nosotros validamos los totales automáticamente.
  </p>
</section>

{#if processing}
  <div class="processing-overlay card">
    <div class="spinner"></div>
    <p>Analizando tu ticket con Gemini…</p>
  </div>
{:else}
  <UploadForm on:uploaded={onUploaded} />
{/if}

{#if processError}
  <div class="alert alert-warning" style="max-width:520px;margin:1rem auto 0;">
    No se pudo completar el procesamiento: {processError}.
    Puedes ver el estado del ticket en <a href="/receipts">Mis tickets</a>.
  </div>
{/if}

<style>
  .hero {
    text-align: center;
    margin-bottom: 2rem;
  }
  h1 { font-size: 1.75rem; margin-bottom: .5rem; }
  .subtitle { color: var(--color-muted); max-width: 520px; margin: 0 auto; }

  .processing-overlay {
    max-width: 520px;
    margin: 0 auto;
    text-align: center;
    padding: 2.5rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 4px solid var(--color-border);
    border-top-color: var(--color-primary);
    border-radius: 50%;
    animation: spin .8s linear infinite;
  }

  @keyframes spin { to { transform: rotate(360deg); } }
</style>
