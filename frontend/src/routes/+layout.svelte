<script lang="ts">
  import '../app.css';
</script>

<header class="topbar" data-od-id="navegacion-principal">
  <div class="container topbar-inner">
    <a class="brand" href="/" data-od-id="marca-receipt-reader">
      <span class="brand-mark" aria-hidden="true">R</span>
      Receipt Reader
    </a>
    <nav class="nav" aria-label="Navegación principal" data-od-id="enlaces-principales">
      <a href="/" aria-current="page" data-od-id="enlace-subir-ticket">Subir ticket</a>
      <a href="/receipts" data-od-id="enlace-mis-tickets">Mis tickets</a>
    </nav>
  </div>
</header>

<main class="container page-content" data-od-id="contenido-principal">
  <slot />
</main>

<style>
  .topbar {
    border-bottom: 1px solid var(--border);
    background: rgba(15, 23, 42, 0.78);
    backdrop-filter: blur(10px);
    position: sticky;
    top: 0;
    z-index: 20;
  }

  .topbar-inner {
    min-height: 74px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
  }

  .brand {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    color: var(--fg);
    font-family: var(--font-display);
    font-size: 15px;
    font-weight: 800;
    letter-spacing: -0.02em;
  }

  .brand-mark {
    display: grid;
    width: 28px;
    height: 28px;
    place-items: center;
    border: 1px solid var(--accent);
    border-radius: 8px;
    color: var(--accent);
    font-size: 16px;
  }

  .nav {
    display: flex;
    gap: 26px;
  }

  .nav a {
    color: var(--muted);
    font-size: 14px;
    font-weight: 500;
    transition: color 160ms ease;
  }

  .nav a:hover,
  .nav a[aria-current='page'] {
    color: var(--fg);
    text-decoration: none;
  }

  .page-content {
    padding: 75px 0 80px;
  }

  @media (max-width: 520px) {
    .topbar-inner {
      min-height: 64px;
    }

    .nav {
      gap: 14px;
    }

    .nav a {
      font-size: 13px;
    }
  }
</style>
