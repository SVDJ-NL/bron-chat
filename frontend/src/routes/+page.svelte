<script>
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';

    const API_BASE_URL = import.meta.env.PUBLIC_API_URL;

    onMount(async () => {
        const response = await fetch(`${API_BASE_URL}/new_session`, { method: 'POST' });
        const data = await response.json();
        goto(`/s/${data.id}`);
    }); 
</script>

<div class="flex items-center justify-center h-screen bg-gray-100">
    <div class="text-2xl font-semibold text-gray-700 flex flex-col items-center">
        <img src="/bron-logo.svg" alt="Bron Logo" class="w-48 h-auto mb-4" />
        <span class="inline-block animate-pulse">Nieuwe chat...</span>
    </div>
</div>
