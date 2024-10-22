<script>
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';

    onMount(async () => {
        const response = await fetch('/api/new_session', { method: 'POST' });
        const data = await response.json();
        goto(`/s/${data.id}`);
    });
</script>

<div class="flex items-center justify-center h-screen bg-gray-100">
    <div class="text-2xl font-semibold text-gray-700">
        <span class="inline-block animate-pulse">Start nieuwe sessie...</span>
    </div>
</div>
