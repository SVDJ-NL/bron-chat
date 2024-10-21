<script>
    import { page } from '$app/stores';
    import Chat from '$lib/components/Chat.svelte';
    import Documents from '$lib/components/Documents.svelte';
    import ShareModal from '$lib/components/ShareModal.svelte';

    export let data;

    $: ({ sessionId, messages, documents, sessionName } = data);

    // ... rest of the script logic from the main page ...
</script>

<!-- Use the same template as the main page -->
<svelte:head>
    <title>{sessionName}</title>
</svelte:head>

<main class="flex flex-col md:flex-row h-screen bg-gray-100">
    <!-- ... existing layout ... -->
</main>

{#if showShareModal}
    <ShareModal 
        {sessionId}
        initialSessionName={sessionName} 
        on:close={close} 
    />
{/if}

<style lang="postcss">
    /* ... existing styles ... */
</style>
