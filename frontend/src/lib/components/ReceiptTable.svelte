<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { ReceiptItem } from '$lib/types';
  import ConfidenceBadge from './ConfidenceBadge.svelte';

  export let items: ReceiptItem[];
  export let editable: boolean = false;

  const dispatch = createEventDispatcher<{ change: ReceiptItem[] }>();

  // Local editable copy
  let editedItems: ReceiptItem[] = items.map((i) => ({ ...i }));

  function fmt(val: string | null): string {
    return val != null ? val : 'No disponible';
  }

  function fmtEur(val: string | null): string {
    if (val == null) return 'No disponible';
    const n = parseFloat(val);
    return isNaN(n) ? val : `${n.toFixed(2)} €`;
  }

  function onFieldChange() {
    dispatch('change', editedItems);
  }

  $: {
    editedItems = items.map((i) => ({ ...i }));
  }
</script>

<div class="table-wrapper">
  {#if items.length === 0}
    <p class="empty">Sin artículos extraídos.</p>
  {:else}
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Descripción</th>
          <th>Descripción normalizada</th>
          <th>Cant.</th>
          <th>Unidad</th>
          <th>P. unit.</th>
          <th>P./kg·l</th>
          <th>Descuento</th>
          <th>Total línea</th>
          <th>Válida</th>
          <th>Confianza</th>
        </tr>
      </thead>
      <tbody>
        {#each editedItems as item, idx (item.id)}
          <tr class:needs-review={item.needs_review} class:line-invalid={item.line_valid === false}>
            <td class="pos">{item.position + 1}</td>
            <td class="raw-desc">
              {#if editable}
                <input
                  type="text"
                  bind:value={editedItems[idx].raw_description}
                  on:change={onFieldChange}
                />
              {:else}
                <span class="mono">{item.raw_description}</span>
              {/if}
            </td>
            <td>
              {#if editable}
                <input
                  type="text"
                  bind:value={editedItems[idx].normalized_description}
                  on:change={onFieldChange}
                  placeholder="—"
                />
              {:else}
                {fmt(item.normalized_description)}
              {/if}
            </td>
            <td class="num">
              {#if editable}
                <input
                  type="number"
                  step="0.001"
                  bind:value={editedItems[idx].quantity}
                  on:change={onFieldChange}
                  style="width:5rem"
                />
              {:else}
                {fmt(item.quantity)}
              {/if}
            </td>
            <td>
              {#if editable}
                <select bind:value={editedItems[idx].unit} on:change={onFieldChange} style="width:5rem">
                  <option value={null}>—</option>
                  <option value="ud">ud</option>
                  <option value="kg">kg</option>
                  <option value="g">g</option>
                  <option value="l">l</option>
                  <option value="ml">ml</option>
                </select>
              {:else}
                {fmt(item.unit)}
              {/if}
            </td>
            <td class="num">{fmtEur(item.unit_price)}</td>
            <td class="num">{fmtEur(item.price_per_kg)}</td>
            <td class="num discount">
              {item.discount != null ? `-${fmtEur(item.discount)}` : '—'}
            </td>
            <td class="num total">
              {fmtEur(item.total_price)}
              {#if item.line_valid === false && item.line_difference != null}
                <span class="diff" title="Diferencia respecto al calculado">
                  (Δ {parseFloat(item.line_difference).toFixed(2)} €)
                </span>
              {/if}
            </td>
            <td class="validity">
              {#if item.line_valid === true}
                <span class="ok" title="Línea matemáticamente válida">✓</span>
              {:else if item.line_valid === false}
                <span class="fail" title="Discrepancia matemática">✗</span>
              {:else}
                <span class="na" title="No comprobable">—</span>
              {/if}
            </td>
            <td>
              <ConfidenceBadge confidence={item.confidence} needsReview={item.needs_review} />
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  {/if}
</div>

<style>
  .table-wrapper { overflow-x: auto; }
  .empty { color: var(--color-muted); text-align: center; padding: 2rem; }
  .mono { font-family: monospace; font-size: .82rem; }
  .num { text-align: right; white-space: nowrap; }
  .pos { color: var(--color-muted); font-size: .82rem; }
  .discount { color: var(--color-success); }
  .total { font-weight: 600; }
  .diff { color: var(--color-danger); font-size: .78rem; display: block; }
  .ok   { color: var(--color-success); font-weight: 700; }
  .fail { color: var(--color-danger); font-weight: 700; }
  .na   { color: var(--color-muted); }

  tr.needs-review td { background: #fff7ed; }
  tr.line-invalid td { border-left: 3px solid var(--color-danger); }
</style>
