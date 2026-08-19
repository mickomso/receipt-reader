<script lang="ts">
  import '../app.css';
</script>

<nav class="nav">
  <div class="container nav-inner">
    <a href="/" class="logo">🧾 Receipt Reader</a>
    <ul class="nav-links">
      <li><a href="/">Subir ticket</a></li>
      <li><a href="/receipts">Mis tickets</a></li>
    </ul>
  </div>
</nav>

<main class="container page-content">
  <slot />
</main>

<style>
  .nav {
    background: #1e293b;
    color: #f1f5f9;
    padding: .75rem 0;
    position: sticky;
    top: 0;
    z-index: 10;
    box-shadow: 0 1px 4px rgba(0,0,0,.2);
  }
  .nav-inner {
    display: flex;
    align-items: center;
    gap: 2rem;
  }
  .logo {
    font-weight: 700;
    font-size: 1.1rem;
    color: #f1f5f9;
    text-decoration: none;
    white-space: nowrap;
  }
  .logo:hover { text-decoration: none; opacity: .85; }
  .nav-links {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    gap: 1.5rem;
  }
  .nav-links a {
    color: #94a3b8;
    font-size: .9rem;
    transition: color .15s;
  }
  .nav-links a:hover {
    color: #f1f5f9;
    text-decoration: none;
  }
  .page-content {
    padding-top: 2rem;
    padding-bottom: 4rem;
  }
</style>
