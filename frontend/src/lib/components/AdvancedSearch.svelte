<script>
    import Select from 'svelte-select';
    import 'svelte-select/tailwind.css';
    import RangeSlider from 'svelte-range-slider-pips';
    import { slide } from 'svelte/transition';
    import { onMount } from 'svelte';
    import { API_BASE_URL } from '$lib/config';
    import { createEventDispatcher } from 'svelte';

    const dispatch = createEventDispatcher();

    export let isOpen;
    export let rewriteQuery = true;
    export let selectedLocations = [];
    export let yearRange = [2010, new Date().getFullYear()];
    
    let locations = [];
    let placeholder = 'Gemeentes, provincies of ministeries...';

    let floatingConfig = {
        strategy: 'fixed'
    }

    const groupBy = (item) => item.group;

    function formatYear(value) {
        return value.toString();
    }

    let ariaValues = (values) => {
        return `Optie ${values}, geselecteerd.`;
    }

    let ariaListOpen = (label, count) => {
        return `Je bent momenteel gefocused op optie ${label}. Er zijn ${count} resultaten beschikbaar.`;
    }

    let ariaFocused = () => {
        return `Select is gefocused, typ om de lijst te verfijnen, druk op de pijl omlaag om het menu te openen.`;
    }

    // Handle location selection changes
    function handleLocationChange(event) {
        console.debug('handleLocationChange', event);
        selectedLocations = event;
        dispatch('locationsUpdate', selectedLocations);
    }

    onMount(async () => {
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

{#if isOpen}
    <div 
        transition:slide={{ duration: 100 }}
        class="bg-white px-4 py-4 border-b border-gray-300"
    >
        <div class="space-y-4">
            <div class="flex items-center">
    
                <!-- Year Range Slider -->
                <div class="flex-1">
                    <label class="text-sm font-medium text-gray-700 block mb-1">
                        Jaren
                    </label>
                    <div class="mt-4 px-2">
                        <RangeSlider
                            min={2010}
                            max={new Date().getFullYear()}
                            bind:values={yearRange}
                            range
                            pushy
                            float
                            step={1}
                            pips
                            pipstep={2}
                            formatter={formatYear}
                            handleFormatter={formatYear}
                            first="label"
                            last="label"
                            all={false}
                            hoverable
                        />
                    </div>
                </div>

                <!-- Query Rewrite Toggle -->
                <!-- <div class="flex flex-col items-center self-start">
                    <label for="query-rewrite" class="ml-3 text-sm font-medium text-gray-700 mb-2">
                        Zoekopdracht herschrijven
                    </label>
                    <button
                        type="button"
                        class={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                            ${rewriteQuery ? 'bg-blue-600' : 'bg-gray-200'}`}
                        on:click={() => rewriteQuery = !rewriteQuery}
                    >
                        <span
                            class={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                                ${rewriteQuery ? 'translate-x-6' : 'translate-x-1'}`}
                        />
                    </button>
                </div> -->
            </div>
            <!-- Location Filter -->
            <div class="w-full">
                <label class="text-sm font-medium text-gray-700 block mb-1">
                    Locatie
                </label>
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
                    placeholder={placeholder}
                />
            </div>

        </div>
    </div>
{/if}

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

    /* Range slider styles */
    :global(.rangeSlider) {
        --range-handle-inactive: theme(colors.gray.200);
        --range-handle: theme(colors.blue.600);
        --range-handle-focus: theme(colors.blue.700);
        --range-handle-border: theme(colors.white);
        --range-float-text: theme(colors.white);
        --range-float-bg: theme(colors.blue.600);
        --range-float-border: theme(colors.blue.600);
        --range-track-inactive: theme(colors.gray.200);
        --range-track: theme(colors.blue.600);
        --range-pip-text-active: theme(colors.gray.700);
        --range-pip-text: theme(colors.gray.400);
    }
</style> 