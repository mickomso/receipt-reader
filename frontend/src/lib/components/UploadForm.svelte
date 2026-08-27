<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { uploadReceipt } from '$lib/api';

  const dispatch = createEventDispatcher<{ uploaded: string }>();

  const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
  const MAX_BYTES = 10 * 1024 * 1024;

  let fileInput: HTMLInputElement | null = null;
  let dragOver = false;
  let error = '';
  let loading = false;
  let selectedFile: File | null = null;
  let preview: string | null = null;

  function validateFile(file: File): string {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return `Tipo no permitido: ${file.type}. Se aceptan JPEG, PNG y WebP.`;
    }
    if (file.size > MAX_BYTES) {
      return 'El fichero supera el límite de 10 MB.';
    }
    return '';
  }

  function selectFile(file: File) {
    error = validateFile(file);
    if (error) {
      selectedFile = null;
      preview = null;
      return;
    }

    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (event) => {
      preview = event.target?.result as string;
    };
    reader.readAsDataURL(file);
  }

  function clearSelection() {
    selectedFile = null;
    preview = null;
    error = '';
    if (fileInput) fileInput.value = '';
  }

  function onInputChange(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files?.[0]) selectFile(input.files[0]);
  }

  function onDrop(event: DragEvent) {
    event.preventDefault();
    dragOver = false;
    const file = event.dataTransfer?.files[0];
    if (file) selectFile(file);
  }

  async function submit() {
    if (!selectedFile) return;

    loading = true;
    error = '';

    try {
      const receipt = await uploadReceipt(selectedFile);
      dispatch('uploaded', receipt.id);
      clearSelection();
    } catch (err: unknown) {
      error = err instanceof Error ? err.message : 'Error al subir el fichero.';
    } finally {
      loading = false;
    }
  }
</script>

<section id="cargar" class="upload-panel" data-od-id="panel-carga">
  <div class="panel-head">
    <h2 data-od-id="titulo-carga">Añadir ticket</h2>
  </div>

  <div class="panel-body">
    <input
      bind:this={fileInput}
      class="file-input"
      id="receipt-file"
      type="file"
      accept="image/jpeg,image/png,image/webp"
      aria-describedby="file-rules file-error"
      aria-invalid="false"
      on:change={onInputChange}
    />

    <label
      class="drop-zone"
      class:is-dragging={dragOver}
      class:is-processing={loading}
      class:is-complete={Boolean(selectedFile) && !error && !loading}
      for="receipt-file"
      data-od-id="zona-arrastre"
      on:dragenter|preventDefault={() => (dragOver = true)}
      on:dragover|preventDefault={() => (dragOver = true)}
      on:dragleave|preventDefault={() => (dragOver = false)}
      on:drop={onDrop}
    >
      {#if preview}
        <img class="preview" src={preview} alt="Vista previa del ticket" />
      {:else}
        <div class="drop-content" id="drop-content">
          <div class="file-glyph" aria-hidden="true">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">
              <path d="M6 2.75h8.5L19 7.25v14H6z" />
              <path d="M14 2.75v4.5h5M9 12h6M9 16h6" />
            </svg>
          </div>
          <strong>Selecciona o arrastra tu imagen</strong>
          <span id="file-rules">JPEG, PNG o WebP · máximo 10 MB</span>
        </div>
      {/if}
    </label>

    {#if selectedFile}
      <div class="file-meta" id="file-meta" data-od-id="archivo-seleccionado">
        <span class="file-meta-copy">
          <strong>{selectedFile.name}</strong> · {(selectedFile.size / 1024).toFixed(0)} KB
        </span>
        <button class="clear-file" type="button" on:click={clearSelection}>Descartar</button>
      </div>
    {/if}

    {#if error}
      <p class="error" id="file-error" role="alert" aria-live="assertive">{error}</p>
    {/if}

    {#if loading}
      <p class="status" aria-live="polite" aria-atomic="true">
        <span class="loader" aria-hidden="true"></span>Subiendo y analizando tu ticket…
      </p>
    {:else if selectedFile && !error}
      <p class="status" aria-live="polite" aria-atomic="true">Imagen preparada para analizar.</p>
    {/if}

    <button class="submit" type="button" disabled={!selectedFile || loading} on:click={submit} data-od-id="cta-procesar-ticket">
      {loading ? 'Procesando ticket...' : 'Procesar ticket'}
    </button>

    <p class="privacy">Solo usaremos la imagen para extraer los datos de tu compra.</p>
  </div>
</section>

<style>
  .upload-panel {
    overflow: hidden;
    border: 1px solid var(--border);
    border-radius: 18px;
    background: var(--surface);
    box-shadow: var(--shadow);
    max-width: 510px;
  }

  .panel-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 16px;
    padding: 25px 28px 21px;
    border-bottom: 1px solid var(--border);
  }

  h2 {
    margin: 0;
    font-family: var(--font-display);
    font-size: 19px;
    font-weight: 700;
    letter-spacing: -0.025em;
  }

  .panel-body {
    padding: 28px;
  }

  .file-input {
    position: absolute;
    width: 1px;
    height: 1px;
    margin: -1px;
    padding: 0;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
    border: 0;
  }

  .drop-zone {
    display: flex;
    min-height: 250px;
    align-items: center;
    justify-content: center;
    border: 1px dashed #50647d;
    border-radius: 12px;
    background: var(--surface-soft);
    color: var(--muted);
    text-align: center;
    cursor: pointer;
    transition: border-color 180ms ease, background 180ms ease;
  }

  .drop-zone:hover,
  .drop-zone.is-dragging {
    border-color: var(--accent);
    background: #15263b;
  }

  .drop-zone.is-processing {
    cursor: progress;
    opacity: 0.72;
    pointer-events: none;
  }

  .drop-zone.is-complete {
    opacity: 0.58;
    pointer-events: none;
  }

  .drop-content {
    display: grid;
    justify-items: center;
    gap: 12px;
    padding: 28px;
  }

  .file-glyph {
    display: grid;
    width: 46px;
    height: 46px;
    place-items: center;
    border: 1px solid var(--border);
    border-radius: 12px;
    color: var(--accent);
  }

  .drop-content strong {
    color: var(--fg);
    font-size: 15px;
    font-weight: 600;
  }

  .drop-content span {
    font-size: 13px;
  }

  .preview {
    width: 100%;
    height: 248px;
    object-fit: contain;
    padding: 14px;
  }

  .file-meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-top: 15px;
    color: var(--muted);
    font-size: 13px;
  }

  .file-meta-copy {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .file-meta-copy strong {
    color: var(--fg);
    font-weight: 600;
  }

  .clear-file {
    flex: 0 0 auto;
    min-height: 44px;
    padding: 0 8px;
    border: 0;
    border-radius: 7px;
    background: transparent;
    color: var(--fg);
    font-size: 12px;
    font-weight: 600;
    text-decoration: underline;
    text-underline-offset: 3px;
  }

  .clear-file:hover {
    background: var(--surface-raised);
  }

  .error {
    display: block;
    margin: 16px 0 0;
    color: var(--danger);
    font-size: 13px;
  }

  .status {
    min-height: 20px;
    margin: 14px 0 0;
    color: var(--muted);
    font-size: 13px;
  }

  .loader {
    display: inline-block;
    width: 10px;
    height: 10px;
    margin-right: 8px;
    border: 2px solid var(--muted);
    border-right-color: transparent;
    border-radius: 50%;
    animation: spin 700ms linear infinite;
    vertical-align: -1px;
  }

  .submit {
    width: 100%;
    min-height: 50px;
    margin-top: 24px;
    border: 1px solid var(--accent);
    border-radius: 12px;
    background: var(--accent);
    color: #072039;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.01em;
    transition: background 180ms ease, border-color 180ms ease, transform 180ms ease;
  }

  .submit:hover:not(:disabled) {
    border-color: #7dd3fc;
    background: #7dd3fc;
    transform: translateY(-1px);
  }

  .submit:active:not(:disabled) {
    transform: translateY(0);
  }

  .submit:disabled {
    border-color: #294058;
    background: #294058;
    color: #7890aa;
    cursor: not-allowed;
  }

  .privacy {
    margin: 17px 0 0;
    color: var(--muted);
    font-size: 12px;
    text-align: center;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  @media (max-width: 520px) {
    .panel-head,
    .panel-body {
      padding-left: 20px;
      padding-right: 20px;
    }

    .drop-zone {
      min-height: 214px;
    }
  }
</style>
