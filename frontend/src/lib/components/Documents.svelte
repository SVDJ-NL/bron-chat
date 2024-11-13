<script>
    import { createEventDispatcher } from 'svelte';
    import { fade } from 'svelte/transition';
    import Document from './Document.svelte';

    export let documents = [];
    export let selectedDocuments = null;
    export let citationText = '';
    export let citationWords = [];
    export let isDocumentsPanelOpen = false;

    const dispatch = createEventDispatcher();

    function handleShowAllDocuments() {
        dispatch('showAllDocuments');
    }

    function togglePanel(event) {
        event.stopPropagation(); // Prevent click from bubbling to document
        dispatch('togglePanel');
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

<div class="pt-5 pb-6 lg:pt-6 lg:pb-0 pl-4 lg:pl-6 lg:pr-2 flex flex-col h-full relative">
    <button
        class="absolute -top-2 -left-16 bg-gray-50 border border-gray-300 rounded-l-xl p-2 lg:p-2 rounded-l-lg flex items-center justify-center transition-colors duration-200 {isDocumentsPanelOpen ? 'hidden' : ''}"
        on:click={togglePanel}
    >
        {#if !isDocumentsPanelOpen}
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
            </svg>
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 0 1-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 0 1 1.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 0 0-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 0 1-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 0 0-3.375-3.375h-1.5a1.125 1.125 0 0 1-1.125-1.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H9.75" />
            </svg>  
        {/if}
    </button>

    <div class="flex justify-between items-center mb-4 align-middle lg:px-2">
        <div class="flex items-center justify-center w-full">
            
            {#if citationText}
                <div class="flex items-center flex-wrap pr-2">
                    <button
                        class="py-2 lg:pr-2 lg:pl-0 flex items-center show-all-documents-btn"
                        on:click={handleShowAllDocuments}
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 mr-2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M9 15 3 9m0 0 6-6M3 9h12a6 6 0 0 1 0 12h-3" />
                        </svg>

                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 mr-2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 0 1-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 0 1 1.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 0 0-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 0 1-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 0 0-3.375-3.375h-1.5a1.125 1.125 0 0 1-1.125-1.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H9.75" />
                        </svg>  
                    
                    </button>
                </div>
            {:else}
                <div class="flex items-center justify-center ">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6 mr-2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 0 1-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 0 1 1.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 0 0-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 0 1-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 0 0-3.375-3.375h-1.5a1.125 1.125 0 0 1-1.125-1.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H9.75" />
                    </svg>  
                </div>
            {/if}  

            {#if citationText}
                <div class="text-sm lg:text-base leading-tight w-full mr-auto">"{citationText}"</div>
            {:else}
                <div class="text-lg font-semibold w-full mr-auto">Documenten</div>
            {/if}

            {#if isDocumentsPanelOpen}
                <div class="flex items-center justify-center mr-2">
                    <button
                        class="transition-colors duration-200"
                        on:click={togglePanel}
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-6 h-6">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                        </svg> 
                    </button>
                </div>
            {/if}
        </div>
    </div>
    
    <div class="flex-grow pr-4 overflow-y-auto overflow-x-hidden">
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
                <div class="space-y-6 hidden lg:block">
                    {#each Array(3) as _, i}
                        <div class="shadow rounded-lg p-4 border border-gray-400 border-dashed bg-gray-50 h-8 flex items-center justify-center opacity-50">
                        </div>
                    {/each}
                </div>
            {/if}
        </div>
    </div>
</div>

<style>
    button {
        transition: transform 0.3s ease;
    }
    
    button:hover {
        transform: scale(1.1);
    }
</style>
