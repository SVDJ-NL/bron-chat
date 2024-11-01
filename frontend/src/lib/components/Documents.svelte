<script>
    import { createEventDispatcher } from 'svelte';
    import { fade } from 'svelte/transition';
    import Document from './Document.svelte';

    export let documents = [];
    export let selectedDocuments = null;
    export let citationText = '';
    export let citationWords = [];

    const dispatch = createEventDispatcher();

    function handleShowAllDocuments() {
        dispatch('showAllDocuments');
    }

    function sortDocuments(docs) {
        if (!docs) return [];
        return [...docs].sort((a, b) => {
            const dateA = new Date(a.data.published || 0);
            const dateB = new Date(b.data.published || 0);
            return dateB - dateA; // Sort descending
        });
    }

    $: sortedDocuments = documents ? sortDocuments(documents) : [];
    $: sortedSelectedDocuments = selectedDocuments ? sortDocuments(selectedDocuments) : null;

</script>

<div class="bg-white rounded-lg shadow py-4 md:py-6 pl-4 md:pl-6 md:pr-2 flex flex-col h-full">
    <div class="flex justify-between items-center mb-4 align-middle md:px-2">
        <h2 class="text-lg leading-tight">
            {#if citationText}
                <span class="font-bold">Documenten:</span> "{citationText}" 
            {:else}
                <span class="font-bold">Documenten</span>
            {/if}
        </h2>
        {#if citationText}
            <div class="flex items-center pr-2">
                <button
                    class="bg-blue-500 hover:bg-blue-600 text-white py-2 pr-4 pl-3 rounded flex items-center"
                    on:click={handleShowAllDocuments}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 mr-2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 15 3 9m0 0 6-6M3 9h12a6 6 0 0 1 0 12h-3" />
                    </svg>
                 
                    <span class="md:hidden">Alle docus</span>
                    <span class="hidden md:inline">Alle documenten</span>
                </button>
            </div>
        {/if}
    </div>
    
    <div class="overflow-y-auto flex-grow pr-4">
        <div class="space-y-6">
            {#if sortedSelectedDocuments && sortedSelectedDocuments.length > 0}
                {#each sortedSelectedDocuments as doc, index}
                    <div in:fade={{delay: index * 300, duration: 300}}>
                        <Document {doc} {citationWords} />
                    </div>
                {/each}
            {:else if sortedDocuments.length > 0}
                {#each sortedDocuments as doc, index}
                    <div in:fade={{delay: index * 300, duration: 300}}>
                        <Document {doc} {citationWords} />
                    </div>
                {/each}      
            {:else}
                <div class="space-y-6 hidden md:block">
                    {#each Array(3) as _, i}
                        <div class="shadow rounded-lg p-4 border border-gray-400 border-dashed bg-gray-50 h-8 flex items-center justify-center opacity-50">
                        </div>
                    {/each}
                </div>
            {/if}
        </div>
    </div>
</div>
