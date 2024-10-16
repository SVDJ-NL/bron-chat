<script>
    import { createEventDispatcher } from 'svelte';
    import Document from './Document.svelte';

    export let documents = [];
    export let selectedDocuments = null;

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

<div class="bg-white rounded-lg shadow p-4 flex flex-col h-full">
    <div class="flex justify-between items-center mb-4 align-middle">
        <h2 class="text-xl font-bold">Documenten</h2>
        <div class="flex items-center">
            <button
                class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded flex items-center"
                on:click={handleShowAllDocuments}
            >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd" />
                </svg>
                <span class="md:hidden">Alle docs</span>
                <span class="hidden md:inline">Alle documenten</span>
            </button>
        </div>
    </div>
    
    <div class="overflow-y-auto flex-grow">
        <div class="space-y-6">
            {#if sortedSelectedDocuments && sortedSelectedDocuments.length > 0}
                {#each sortedSelectedDocuments as doc}
                    <Document {doc} />
                {/each}
            {:else}
                {#if sortedDocuments.length > 0}
                    {#each sortedDocuments as doc}
                        <Document {doc} />
                    {/each}      
                {/if}
            {/if}
        </div>
    </div>
</div>
