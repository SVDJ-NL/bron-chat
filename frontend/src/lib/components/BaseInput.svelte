<script>
    import { createEventDispatcher, onMount } from 'svelte';
    import AdvancedSearch from './AdvancedSearch.svelte';
    
    export let isLoading = false;
    export let value = '';
    export let placeholder = 'Chat met Bron...';
    
    const dispatch = createEventDispatcher();
    
    let isAdvancedSearchOpen = false;
    let rewriteQuery = true;
    let selectedLocations = [];
    let yearRange = [2010, new Date().getFullYear()];
    let locations = [];
    
    function handleSubmit(event) {
        if (!Array.isArray(selectedLocations)) {
            console.error('selectedLocations is not an array:', selectedLocations);
            selectedLocations = [];
        } else {
            console.log('handleSubmit selectedLocations', selectedLocations);
        }
        
        console.log('handleSubmit', event);
        event.preventDefault();

        if (!value.trim()) return;
        
        // Create search filters object
        const urlSearchParams = new URLSearchParams({
            query: value.trim(),
        });

        if (rewriteQuery) {
            urlSearchParams.append('rewrite_query', 'true');
        }

        // Add locations if any are selected
        if (selectedLocations.length > 0) {
            selectedLocations.forEach(loc => {
                if (loc && loc.value) {  // Check if location object is valid
                    urlSearchParams.append('locations', loc.value);
                }
            });
        }
       
        if (yearRange) {
            urlSearchParams.append('start_date', yearRange[0].toString() + '-01-01');
            urlSearchParams.append('end_date', yearRange[1].toString() + '-12-31');
        }

        dispatch('submit', {
            urlSearchParams
        });
    }

    function handleStop() {
        dispatch('stop');
    }
    
    function toggleAdvancedSearch() {
        isAdvancedSearchOpen = !isAdvancedSearchOpen;
    }
</script>

<div class="rounded-lg border border-gray-300 overflow-hidden">
    <!-- Advanced Search Toggle -->
    <div class="px-4 py-2 bg-gray-50 border-b border-gray-300">
        <button
            type="button"
            class="text-sm text-gray-600 hover:text-gray-900 flex items-center gap-1 w-full justify-between"
            on:click={toggleAdvancedSearch}
        >
            <span class="flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M3 3a1 1 0 011-1h12a1 1 0 011 1v3a1 1 0 01-.293.707L12 11.414V15a1 1 0 01-.293.707l-2 2A1 1 0 018 17v-5.586L3.293 6.707A1 1 0 013 6V3z" clip-rule="evenodd" />
                </svg>
                Geavanceerd zoeken
            </span>
            <svg 
                class="w-4 h-4 transform transition-transform duration-200 {isAdvancedSearchOpen ? 'rotate-180' : ''}" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
            >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
        </button>
    </div>

    <!-- Search Input -->
    <div class="{isAdvancedSearchOpen ? 'bg-white' : ''}">
        <form on:submit={handleSubmit} class="flex space-x-2 flex-col">

            <!-- Advanced Search Panel -->
            <AdvancedSearch
                isOpen={isAdvancedSearchOpen}
                bind:rewriteQuery
                bind:yearRange
                {locations}
            />

            <div class="flex p-4  space-x-2  flex-row">
                <textarea
                    bind:value
                    {placeholder}
                    class="flex-1 text-base p-2 bg-gray-100 rounded text-gray-900 focus:outline-none focus:ring-0  {isAdvancedSearchOpen ? 'bg-white' : ''}"
                    autofocus
                    rows="1"
                    disabled={isLoading}
                    on:keydown={e => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleSubmit(e);
                        }
                        if (e.key === 'Escape' && isLoading) {
                            e.preventDefault();
                            handleStop();
                        }
                    }}
                ></textarea>
                <slot name="button" {isLoading} {handleSubmit} {handleStop}></slot>
            </div>
        </form>
    </div>
</div> 