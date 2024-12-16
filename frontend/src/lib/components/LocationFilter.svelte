<script>
    import Select from 'svelte-select';
    import 'svelte-select/tailwind.css';
    import { onMount } from 'svelte';
    import { API_BASE_URL } from '$lib/config';
    import { createEventDispatcher } from 'svelte';

    const dispatch = createEventDispatcher();

    export let selectedLocations = [];
    let locations = [];
    let placeholder = 'Gemeentes, provincies of ministeries...';

    let floatingConfig = {
        strategy: 'fixed'
    }

    const groupBy = (item) => item.group;

    let ariaValues = (values) => {
        return `Optie ${values}, geselecteerd.`;
    }

    let ariaListOpen = (label, count) => {
        return `Je bent momenteel gefocused op optie ${label}. Er zijn ${count} resultaten beschikbaar.`;
    }

    let ariaFocused = () => {
        return `Select is gefocused, typ om de lijst te verfijnen, druk op de pijl omlaag om het menu te openen.`;
    }
    
    function handleLocationChange(event) {
        console.debug('handleLocationChange', event);
        selectedLocations = event;
        dispatch('locationsUpdate', selectedLocations);
    }

    function handleClose() {
        dispatch('close');
    }

    onMount(async () => {
        selectedLocations = Array.isArray(selectedLocations) ? selectedLocations : [];
        
        try {
            const response = await fetch(`${API_BASE_URL}/locations`);
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.status}`);
            }
            locations = await response.json();
        } catch (error) {
            console.error('Error fetching locations:', error);
        }
    });
</script>

<div class="bg-white rounded-lg shadow-lg p-4 w-[500px] max-w-[calc(100vw-2rem)]">
    <div class="flex justify-between items-center mb-4">
        <h3 class="text-sm font-medium text-gray-700">Locatie filter</h3>
        <button 
            on:click={handleClose}
            class="text-gray-400 hover:text-gray-600 transition-colors"
        >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
        </button>
    </div>
    <Select
        items={locations}
        multiple={true}
        bind:value={selectedLocations}
        on:change={handleLocationChange}
        floatingConfig={floatingConfig}
        groupBy={groupBy}
        ariaValues={ariaValues}
        ariaListOpen={ariaListOpen}
        ariaFocused={ariaFocused}
        class="location-select"
        {placeholder}
    />
</div>

<style>
    :global(.location-select .selectContainer) {
        @apply border border-gray-300 rounded-md;
    }

    :global(.location-select .multiSelect) {
        @apply bg-blue-50 px-2 py-0.5 rounded text-sm;
    }

    :global(.location-select .selectContainer input) {
        @apply text-sm leading-5;
    }

    :global(.location-select .list) {
        @apply shadow-lg rounded-md border border-gray-200;
    }

    :global(.location-select .item) {
        @apply text-sm py-2 px-4;
    }

    :global(.location-select .item.active) {
        @apply bg-blue-50;
    }

    :global(.location-select .clearSelect) {
        @apply text-gray-400;
    }
</style> 