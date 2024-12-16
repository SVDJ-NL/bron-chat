<script>
    import { createEventDispatcher, onMount } from 'svelte';
    import { computePosition, flip, shift, offset } from '@floating-ui/dom';
    import LocationFilter from './LocationFilter.svelte';
    import YearFilter from './YearFilter.svelte';
    
    export let isLoading = false;
    export let value = '';
    export let placeholder = 'Chat met Bron...';
    
    const dispatch = createEventDispatcher();
    
    let rewriteQuery = true;
    let selectedLocations = [];
    let yearRange = [2010, new Date().getFullYear()];
    
    let showLocationFilter = false;
    let showYearFilter = false;
    let locationButton;
    let yearButton;
    let locationPopup;
    let yearPopup;

    let popupsReady = {
        location: false,
        year: false
    };

    function handleSubmit(event) {
        console.log('base input handleSubmit', event);
        
        if (event?.preventDefault) {
            event.preventDefault();
        }
        
        if (!value.trim()) return;
        
        const urlSearchParams = new URLSearchParams({
            query: value.trim(),
        });

        if (rewriteQuery) {
            urlSearchParams.append('rewrite_query', 'true');
        }

        if (selectedLocations.length > 0) {
            selectedLocations.forEach(loc => {
                if (loc && loc.value) {
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

    function handleLocationsUpdate(event) {
        selectedLocations = event.detail.detail;
    }

    function handleYearUpdate(event) {
        yearRange = event.detail;
    }

    async function updatePopupPosition(button, popup, placement = 'top-start') {
        if (!button || !popup) return;
        
        const searchPanel = button.closest('.search-panel');
        if (!searchPanel) return;
        
        const searchPanelRect = searchPanel.getBoundingClientRect();
        
        const { x, y } = await computePosition(button, popup, {
            placement: 'top-start',
            middleware: [
                offset({ mainAxis: 8 }),
                flip(),
                {
                    name: 'alignPanel',
                    fn: ({ x, y }) => {
                        return {
                            x: window.scrollX + searchPanelRect.left,
                            y: window.scrollY + searchPanelRect.top - popup.offsetHeight - 8
                        };
                    }
                }
            ],
        });

        Object.assign(popup.style, {
            left: `${x}px`,
            top: `${y}px`,
            position: 'fixed',
            zIndex: '50'
        });

        if (popup === locationPopup) {
            popupsReady.location = true;
        } else if (popup === yearPopup) {
            popupsReady.year = true;
        }
    }

    function toggleLocationFilter() {
        showLocationFilter = !showLocationFilter;
        showYearFilter = false;
        popupsReady.location = false;
        if (showLocationFilter) {
            setTimeout(() => updatePopupPosition(locationButton, locationPopup), 0);
        }
    }

    function toggleYearFilter() {
        showYearFilter = !showYearFilter;
        showLocationFilter = false;
        popupsReady.year = false;
        if (showYearFilter) {
            setTimeout(() => updatePopupPosition(yearButton, yearPopup), 0);
        }
    }

    function handleClickOutside(event) {
        if (!locationButton?.contains(event.target) && !locationPopup?.contains(event.target)) {
            showLocationFilter = false;
        }
        if (!yearButton?.contains(event.target) && !yearPopup?.contains(event.target)) {
            showYearFilter = false;
        }
    }

    onMount(() => {
        document.addEventListener('click', handleClickOutside);
        return () => document.removeEventListener('click', handleClickOutside);
    });
</script>

<form on:submit={handleSubmit} class="relative">
    <div class="search-panel rounded-lg border border-gray-300 overflow-hidden">
        <div class="p-3 pb-1">
            <div class="">
                <textarea
                    bind:value
                    {placeholder}
                    class="w-full text-base p-2 bg-gray-100 rounded text-gray-900 focus:outline-none focus:ring-0"
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
            </div>

            <div class="flex justify-between items-center">
                <!-- Filter Buttons -->
                <div class="flex space-x-2">
                    <button
                        bind:this={locationButton}
                        class="flex items-center space-x-1 px-1 text-sm text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100"
                        on:click={toggleLocationFilter}
                        type="button"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5" >
                            <path stroke-linecap="round" stroke-linejoin="round" d="M15 10.5a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1 1 15 0Z" />
                        </svg>
                      
                        <span class="sr-only">Locatie</span>
                    </button>

                    <button
                        bind:this={yearButton}
                        class="flex items-center space-x-1 px-1 text-sm text-gray-500 hover:text-gray-700 rounded-md hover:bg-gray-100"
                        on:click={toggleYearFilter}
                        type="button"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5" >
                            <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5m-9-6h.008v.008H12v-.008ZM12 15h.008v.008H12V15Zm0 2.25h.008v.008H12v-.008ZM9.75 15h.008v.008H9.75V15Zm0 2.25h.008v.008H9.75v-.008ZM7.5 15h.008v.008H7.5V15Zm0 2.25h.008v.008H7.5v-.008Zm6.75-4.5h.008v.008h-.008v-.008Zm0 2.25h.008v.008h-.008V15Zm0 2.25h.008v.008h-.008v-.008Zm2.25-4.5h.008v.008H16.5v-.008Zm0 2.25h.008v.008H16.5V15Z" />
                        </svg>                 
                        <span class="sr-only">Jaar</span>
                    </button>

                    <div class="pl-2 flex items-center space-x-1 text-sm text-gray-400"><span>Filter op locatie of jaar</span></div>
                </div>
                
                <!-- Search Button -->
                <div>
                    <slot name="button" {isLoading} {handleSubmit} {handleStop}></slot>
                </div>
            </div>
        </div>
    </div>

    {#if showLocationFilter}
        <div 
            bind:this={locationPopup} 
            class="fixed" 
            class:invisible={!popupsReady.location}
        >
            <LocationFilter
                bind:selectedLocations
                on:locationsUpdate={handleLocationsUpdate}
                on:close={() => showLocationFilter = false}
            />
        </div>
    {/if}

    {#if showYearFilter}
        <div 
            bind:this={yearPopup} 
            class="fixed"
            class:invisible={!popupsReady.year}
        >
            <YearFilter
                bind:yearRange
                on:yearUpdate={handleYearUpdate}
                on:close={() => showYearFilter = false}
            />
        </div>
    {/if}
</form> 