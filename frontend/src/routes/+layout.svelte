<script>
  import "../app.css";
  import Header from '$lib/components/Header.svelte';
  import { page } from '$app/stores';

  $: showHeader = $page.url.pathname !== '/';
</script>

{#if showHeader}
  <Header />
{/if}

<main>
  <slot />
</main>

<style>
  main {
    min-height: 100vh;
  }
</style>