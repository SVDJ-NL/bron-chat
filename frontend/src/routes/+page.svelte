<script>
    import { goto } from '$app/navigation';
    import { API_BASE_URL } from '$lib/config';
    import ChatInput from '$lib/components/ChatInput.svelte';
    import Typed from 'typed.js';
    import { onMount } from 'svelte';
	import SearchInput from '../lib/components/SearchInput.svelte';

    let query = '';
    let isLoading = false;
    let error = null;

    async function handleSearch({ detail }) {
        isLoading = true;
        error = null;

        try {
            // First create a new session
            const sessionResponse = await fetch(`${API_BASE_URL}/new_session`, {
                method: 'POST',
            });

            if (!sessionResponse.ok) {
                throw new Error('Failed to create new session');
            }

            const sessionData = await sessionResponse.json();
            const sessionId = sessionData.id;

            // Navigate to the session page
            await goto(`/s/${sessionId}`);

            // The chat page will automatically handle the query once loaded
            const searchEvent = new CustomEvent('initialQuery', {
                detail: { query: detail.query }
            });
            window.dispatchEvent(searchEvent);

        } catch (err) {
            console.error('Error:', err);
            isLoading = false;
            error = 'Er is een fout opgetreden bij het verwerken van uw vraag.';
        }
    }

    onMount(() => {
        const typedTitle = new Typed('#typed-title', {
            strings: ["Vraag alles over 3.5 miljoen open overheidsdocumenten"],
            typeSpeed: 50,
            showCursor: false,
        });

        return () => {
            typedTitle.destroy();
        };
    });
</script>

<div class="min-h-screen flex flex-col items-center justify-center bg-gray-100">
    <div class="w-full max-w-2xl text-center mb-4">
        <h1 class="text-xl sm:text-3xl font-bold mb-2 sm:mb-4">Welkom bij BRON Chat</h1>
        <h2 id="typed-title" class="text-gray-600 text-lg lg:text-xl"></h2>
    </div>

    <div class="w-full max-w-2xl">
        <SearchInput
            bind:value={query}
            {isLoading}
            on:submit={handleSearch}
        />
    </div>

    {#if error}
        <div class="mt-4 text-red-500">
            {error}
        </div>
    {/if}
</div>
