<script lang="ts">
  export let confidence: number | null;
  export let needsReview: boolean = false;

  $: pct = confidence != null ? Math.round(confidence * 100) : null;
  $: colorClass =
    needsReview
      ? 'conf-review'
      : pct == null
      ? 'conf-unknown'
      : pct >= 90
      ? 'conf-high'
      : pct >= 70
      ? 'conf-mid'
      : 'conf-low';
</script>

<span class="confidence {colorClass}" title={pct != null ? `Confianza: ${pct}%` : 'Sin confianza'}>
  {#if pct != null}
    {pct}%
  {:else}
    —
  {/if}
  {#if needsReview}
    <span class="review-flag" title="Requiere revisión">⚠</span>
  {/if}
</span>

<style>
  .confidence {
    font-size: .8rem;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    gap: .2rem;
  }
  .conf-high    { color: #166534; }
  .conf-mid     { color: #92400e; }
  .conf-low     { color: #b91c1c; }
  .conf-review  { color: #c2410c; }
  .conf-unknown { color: #64748b; }
  .review-flag  { font-size: .9rem; }
</style>
