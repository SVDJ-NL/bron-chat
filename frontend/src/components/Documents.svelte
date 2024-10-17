<script>
    import { createEventDispatcher } from 'svelte';
    import Document from './Document.svelte';

    export let documents = [];
    export let selectedDocuments = null;
    export let citationText = ''; // New prop for citation text
    export let citationWords = [];

    const dispatch = createEventDispatcher();

    function handleShowAllDocuments() {
        dispatch('showAllDocuments');
    }

    function sortDocuments(docs) {
        return [...docs].sort((a, b) => {
            const dateA = new Date(a.published);
            const dateB = new Date(b.published);
            return dateB - dateA; // Always sort descending
        });
    }

    $: sortedDocuments = sortDocuments(documents);
    $: sortedSelectedDocuments = selectedDocuments ? sortDocuments(selectedDocuments) : null;

</script>

<div class="bg-white rounded-lg shadow py-4 pl-4 flex flex-col h-full">
    <div class="flex justify-between items-center mb-4 align-middle">
        <h2 class="text-lg leading-tight">
            {#if citationText}
                <span class="font-bold">Documenten:</span> "{citationText}" 
            {:else}
                <span class="font-bold">Documenten</span>
            {/if}
        </h2>
        {#if citationText}
            <div class="flex items-center">
                <button
                    class="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded flex items-center"
                    on:click={handleShowAllDocuments}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd" />
                    </svg>
                    <span class="md:hidden">Alle docs</span>
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
                        <Document {doc} citationWords={citationWords} />
                    </div>
                {/each}
            {:else if sortedDocuments.length > 0}
                {#each sortedDocuments as doc, index}
                    <div in:fade={{delay: index * 300, duration: 300}}>
                        <Document {doc} citationWords={citationWords} />
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
