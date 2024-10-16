<script>
    import { createEventDispatcher } from 'svelte';

    export let documents = [];
    export let selectedDocuments = null;

    const dispatch = createEventDispatcher();

    function handleShowAllDocuments() {
        dispatch('showAllDocuments');
    }
</script>

<div class="bg-white rounded-lg shadow p-4 flex flex-col h-full">
    <div class="flex justify-between items-center mb-4 align-middle">
        <h2 class="text-xl font-bold">Geraadpleegde documenten</h2>
        <button
            class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded flex items-center"
            on:click={handleShowAllDocuments}
        >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd" />
            </svg>
            Alle documenten
        </button>
    </div>
    
    <div class="overflow-y-auto flex-grow">
        {#if selectedDocuments && selectedDocuments.length > 0}
            <div class="p-4">
                {#each selectedDocuments as doc}
                    <div class="mb-6 p-4 bg-blue-100 rounded-lg">
                        <h2 class="text-lg font-bold mb-2 leading-snug">
                            {doc.data.title || "< Naamloos document >"}
                        </h2>
                        <p class="text-sm text-gray-600 mb-4">ID: {doc.id}</p>
                        <div class="max-w-none prose-sm text-sm">
                            [...] {@html doc.data.snippet} [...]
                        </div>
                    </div>
                {/each}
            </div>
        {:else}
            <div class="p-4">
                {#if documents.length > 0}
                    <ul class="space-y-2">
                        {#each documents as doc}
                            <li class="p-2 bg-gray-100 rounded">
                                <h3 class="font-semibold">
                                    {doc.data.title || "< Naamloos document>"}</h3>
                                <p class="text-sm text-gray-600">ID: {doc.id}</p>
                            </li>
                        {/each}
                    </ul>
                {/if}
            </div>
        {/if}
    </div>
</div>
