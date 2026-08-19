<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { uploadReceipt } from '$lib/api';

  const dispatch = createEventDispatcher<{ uploaded: string }>();

  const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
  const MAX_BYTES = 10 * 1024 * 1024;

  let fileInput: HTMLInputElement;
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
      return `El fichero supera el límite de 10 MB.`;
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
    reader.onload = (e) => {
      preview = e.target?.result as string;
    };
    reader.readAsDataURL(file);
  }

  function onInputChange(e: Event) {
    const input = e.target as HTMLInputElement;
    if (input.files?.[0]) selectFile(input.files[0]);
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    dragOver = false;
    const file = e.dataTransfer?.files[0];
    if (file) selectFile(file);
  }

  async function submit() {
    if (!selectedFile) return;
    loading = true;
    error = '';
    try {
      const receipt = await uploadReceipt(selectedFile);
      dispatch('uploaded', receipt.id);
      selectedFile = null;
      preview = null;
      if (fileInput) fileInput.value = '';
    } catch (err: unknown) {
      error = err instanceof Error ? err.message : 'Error al subir el fichero.';
    } finally {
      loading = false;
    }
  }
</script>

<div class="upload-card card">
  <h2>Subir ticket</h2>
  <p class="hint">Arrastra o selecciona una imagen de tu ticket (JPEG, PNG, WebP · máx. 10 MB).</p>

  <!-- Drop zone -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div
    class="drop-zone"
    class:drag-over={dragOver}
    on:dragover|preventDefault={() => (dragOver = true)}
    on:dragleave={() => (dragOver = false)}
    on:drop={onDrop}
    on:click={() => fileInput.click()}
    role="button"
    tabindex="0"
    on:keydown={(e) => e.key === 'Enter' && fileInput.click()}
    aria-label="Zona de arrastre para subir ticket"
  >
    {#if preview}
      <img src={preview} alt="Vista previa del ticket" class="preview-img" />
    {:else}
      <div class="drop-placeholder">
        <span class="icon">🧾</span>
        <span>Haz clic o arrastra aquí</span>
      </div>
    {/if}
  </div>

  <input
    bind:this={fileInput}
    type="file"
    accept="image/jpeg,image/png,image/webp"
    style="display:none"
    on:change={onInputChange}
  />

  {#if selectedFile}
    <p class="file-name">📄 {selectedFile.name} ({(selectedFile.size / 1024).toFixed(0)} KB)</p>
  {/if}

  {#if error}
    <div class="alert alert-error">{error}</div>
  {/if}

  <button
    class="btn btn-primary submit-btn"
    disabled={!selectedFile || loading}
    on:click={submit}
  >
    {loading ? 'Subiendo…' : 'Subir y procesar'}
  </button>
</div>

<style>
  .upload-card { max-width: 520px; margin: 0 auto; }
  h2 { margin: 0 0 .4rem; }
  .hint { color: var(--color-muted); font-size: .875rem; margin: 0 0 1rem; }
  .drop-zone {
    border: 2px dashed var(--color-border);
    border-radius: var(--radius);
    padding: 2rem;
    text-align: center;
    cursor: pointer;
    transition: border-color .15s, background .15s;
    min-height: 140px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .drop-zone:hover, .drag-over {
    border-color: var(--color-primary);
    background: #eff6ff;
  }
  .drop-placeholder { display: flex; flex-direction: column; align-items: center; gap: .5rem; color: var(--color-muted); }
  .icon { font-size: 2.5rem; }
  .preview-img { max-height: 200px; max-width: 100%; border-radius: 4px; object-fit: contain; }
  .file-name { font-size: .875rem; color: var(--color-muted); margin: .5rem 0; }
  .submit-btn { margin-top: 1rem; width: 100%; justify-content: center; }
</style>
