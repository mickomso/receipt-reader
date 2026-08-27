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
  <title>Receipt Reader | Analizar ticket</title>
</svelte:head>

<div class="workspace">
  <section class="intro" data-od-id="introduccion-analisis">
    <p class="eyebrow">Lectura de recibos</p>
    <h1 data-od-id="titulo-principal">TU TICKET,<br />EN DATOS CLAROS.</h1>
    <p class="lede">
      Carga una imagen y obtén una lectura estructurada de productos, cantidades y precios.
      Revisa el resultado antes de guardarlo.
    </p>
    <ul class="facts" aria-label="Características del servicio" data-od-id="caracteristicas">
      <li>JPEG, PNG o WebP</li>
      <li>Hasta 10 MB por archivo</li>
      <li>Totales verificados</li>
    </ul>
  </section>

  {#if processing}
    <div class="processing-overlay card" data-od-id="estado-procesando">
      <div class="spinner"></div>
      <p>Analizando tu ticket con Gemini…</p>
    </div>
  {:else}
    <UploadForm on:uploaded={onUploaded} />
  {/if}
</div>

{#if processError}
  <div class="alert alert-warning page-alert">
    No se pudo completar el procesamiento: {processError}.
    Puedes ver el estado del ticket en <a href="/receipts">Mis tickets</a>.
  </div>
{/if}

<style>
  .workspace {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(400px, 510px);
    align-items: start;
    gap: clamp(48px, 8vw, 118px);
  }

  .intro {
    padding-top: 24px;
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
    max-width: 500px;
    margin: 28px 0 0;
    color: var(--muted);
    font-size: 17px;
    line-height: 1.65;
  }

  .facts {
    display: flex;
    flex-wrap: wrap;
    gap: 14px 30px;
    margin: 42px 0 0;
    padding: 0;
    color: var(--muted);
    font-size: 13px;
    list-style: none;
  }

  .facts li {
    display: flex;
    align-items: center;
    gap: 9px;
  }

  .facts li::before {
    width: 6px;
    height: 6px;
    border: 1px solid var(--accent);
    border-radius: 50%;
    content: '';
  }

  .processing-overlay {
    max-width: 520px;
    margin: 0 auto;
    text-align: center;
    padding: 2.5rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    min-height: 260px;
    justify-content: center;
  }

  .spinner {
    width: 42px;
    height: 42px;
    border: 4px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  .page-alert {
    max-width: 520px;
    margin: 1rem auto 0;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  @media (max-width: 800px) {
    .workspace {
      grid-template-columns: 1fr;
      gap: 42px;
    }

    .intro {
      padding-top: 0;
    }
  }

  @media (max-width: 520px) {
    .facts {
      gap: 12px 18px;
      margin-top: 32px;
    }

    h1 {
      font-size: 42px;
    }
  }
</style>
