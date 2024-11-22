<script>
    import { createEventDispatcher } from 'svelte';
    
    export let isLoading = false;
    export let value = '';
    export let placeholder = 'Chat met Bron...';
    
    const dispatch = createEventDispatcher();
    
    function handleSubmit(event) {
        event.preventDefault();
        if (!value.trim()) return;
        
        dispatch('submit', { query: value.trim() });
        value = '';
    }

    function handleStop() {
        dispatch('stop');
    }
</script>

<div class="input-container p-4 mb-3 lg:mx-0 rounded-lg border border-gray-300">
    <form on:submit|preventDefault={handleSubmit} class="flex space-x-2">
        <textarea
            bind:value
            {placeholder}
            class="flex-1 text-base p-2 bg-gray-100 text-gray-900 focus:outline-none focus:ring-0"
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
    </form>
</div> 