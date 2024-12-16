<script>
    import RangeSlider from 'svelte-range-slider-pips';
    import { createEventDispatcher } from 'svelte';

    const dispatch = createEventDispatcher();
    
    export let yearRange = [2010, new Date().getFullYear()];

    function formatYear(value) {
        return value.toString();
    }

    function handleYearChange(event) {
        yearRange = event.detail.values;
        dispatch('yearUpdate', yearRange);
    }

    function handleClose() {
        dispatch('close');
    }
</script>

<div class="bg-white rounded-lg shadow-lg p-4 w-[500px] max-w-[calc(100vw-2rem)]">
    <div class="flex justify-between items-center mb-4">
        <h3 class="text-sm font-medium text-gray-700">Jaar filter</h3>
        <button 
            on:click={handleClose}
            class="text-gray-400 hover:text-gray-600 transition-colors"
        >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
        </button>
    </div>
    <div class="px-2">
        <RangeSlider
            min={2010}
            max={new Date().getFullYear()}
            values={yearRange}
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
            on:change={handleYearChange}
        />
    </div>
</div>

<style>
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