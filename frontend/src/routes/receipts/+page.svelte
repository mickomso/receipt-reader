<script lang="ts">
  import { onMount } from 'svelte';
  import { listReceipts } from '$lib/api';
  import StatusBadge from '$lib/components/StatusBadge.svelte';
  import type { Receipt } from '$lib/types';

  let receipts: Receipt[] = [];
  let loading = true;
  let error = '';

  onMount(async () => {
    try {
      const data = await listReceipts(0, 50);
      receipts = data.items;
    } catch (err: unknown) {
      error = err instanceof Error ? err.message : 'Error al cargar los tickets.';
    } finally {
      loading = false;
    }
  });

  function fmtDate(d: string | null): string {
    if (!d) return 'No disponible';
    return new Date(d).toLocaleDateString('es-ES', { dateStyle: 'medium' });
  }
</script>

<svelte:head>
  <title>Receipt Reader — Mis tickets</title>
</svelte:head>

<div class="page-header">
  <h1>Mis tickets</h1>
  <a href="/" class="btn btn-primary">+ Subir nuevo</a>
</div>

{#if loading}
  <p class="muted">Cargando…</p>
{:else if error}
  <div class="alert alert-error">{error}</div>
{:else if receipts.length === 0}
  <div class="card empty-state">
    <p>No has subido ningún ticket todavía.</p>
    <a href="/" class="btn btn-primary">Subir primer ticket</a>
  </div>
{:else}
  <div class="card">
    <table>
      <thead>
        <tr>
          <th>Fichero</th>
          <th>Comercio</th>
          <th>Fecha</th>
          <th>Total</th>
          <th>Estado</th>
          <th>Creado</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {#each receipts as r (r.id)}
          <tr>
            <td class="filename">{r.filename}</td>
            <td>{r.commerce ?? '—'}</td>
            <td>{r.date ?? '—'}</td>
            <td>—</td>
            <td><StatusBadge status={r.status} /></td>
            <td class="date">{fmtDate(r.created_at)}</td>
            <td>
              <a href="/receipts/{r.id}" class="btn btn-outline btn-sm">Ver</a>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
{/if}

<style>
  .page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.5rem;
  }
  h1 { margin: 0; }
  .muted { color: var(--color-muted); }
  .empty-state { text-align: center; padding: 3rem; }
  .empty-state p { margin-bottom: 1rem; }
  .filename { font-size: .85rem; font-family: monospace; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .date { color: var(--color-muted); font-size: .85rem; }
  .btn-sm { padding: .25rem .7rem; font-size: .82rem; }
</style>
