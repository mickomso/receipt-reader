<script lang="ts">
  import type { ReceiptTotals } from '$lib/types';

  export let totals: ReceiptTotals | null;
  export let currency: string = 'EUR';

  function fmt(val: string | null): string {
    if (val == null) return 'No disponible';
    const n = parseFloat(val);
    return isNaN(n) ? val : `${n.toFixed(2)} ${currency}`;
  }

  $: diff = totals?.difference != null ? parseFloat(totals.difference) : null;
  $: hasMismatch = diff != null && Math.abs(diff) > 0.02;
</script>

{#if totals}
  <div class="totals-card card">
    <h3>Totales</h3>

    {#if hasMismatch}
      <div class="alert alert-warning mismatch">
        <strong>Discrepancia:</strong> El total declarado y el calculado difieren en
        <strong>{diff != null ? Math.abs(diff).toFixed(2) : '?'} {currency}</strong>.
        Revisar antes de confirmar.
      </div>
    {:else if totals.totals_valid === true}
      <div class="alert alert-success">
        Los totales cuadran correctamente.
      </div>
    {:else if totals.totals_valid === false}
      <div class="alert alert-error">
        Los totales no cuadran.
      </div>
    {/if}

    <table class="totals-table">
      <tbody>
        {#if totals.subtotal != null}
          <tr>
            <td>Subtotal</td>
            <td class="num">{fmt(totals.subtotal)}</td>
          </tr>
        {/if}
        {#each totals.taxes as tax}
          <tr>
            <td>{tax.name ?? 'Impuesto'} {tax.rate != null ? `(${(parseFloat(tax.rate)*100).toFixed(0)}%)` : ''}</td>
            <td class="num">{fmt(tax.amount)}</td>
          </tr>
        {/each}
        <tr class="total-row">
          <td><strong>Total declarado</strong></td>
          <td class="num"><strong>{fmt(totals.total)}</strong></td>
        </tr>
        {#if totals.calculated_total != null}
          <tr class:mismatch-row={hasMismatch}>
            <td>Total calculado</td>
            <td class="num">{fmt(totals.calculated_total)}</td>
          </tr>
          {#if diff != null}
            <tr>
              <td class="diff-label">Diferencia</td>
              <td class="num" class:diff-warn={hasMismatch}>{diff.toFixed(2)} {currency}</td>
            </tr>
          {/if}
        {/if}
      </tbody>
    </table>
  </div>
{/if}

<style>
  h3 { margin: 0 0 1rem; font-size: 1rem; }
  .totals-table { width: auto; min-width: 280px; }
  .totals-table td { padding: .35rem .75rem; }
  .num { text-align: right; }
  .total-row td { border-top: 2px solid var(--color-border); padding-top: .6rem; }
  .diff-warn { color: var(--color-danger); font-weight: 700; }
  .mismatch-row td { background: #fff7ed; }
  .mismatch { margin-bottom: 1rem; }
  .diff-label { color: var(--color-muted); font-size: .85rem; }
</style>
