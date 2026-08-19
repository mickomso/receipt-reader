<script lang="ts">
  import type { ReceiptStatus } from '$lib/types';

  export let status: ReceiptStatus;

  const labels: Record<ReceiptStatus, string> = {
    uploaded: 'Subido',
    processing: 'Procesando',
    extracted: 'Extraído',
    needs_review: 'Revisar',
    confirmed: 'Confirmado',
    failed: 'Error',
  };
</script>

<span class="badge badge-{status}">{labels[status] ?? status}</span>
