<script>
    export let messages = [];
    export let currentMessage = null;

    import { createEventDispatcher } from 'svelte';
    const dispatch = createEventDispatcher();

    let newMessageContent = '';

    function handleSubmit() {
        if (newMessageContent.trim()) {
            dispatch('newMessage', {
                role: 'user',
                content: newMessageContent
            });
            newMessageContent = '';
        }
    }

    function handleCitationClick(documentIds) {
        dispatch('citationClick', documentIds);
    }

    function insertClickableCitations(text_formatted) {
        const parser = new DOMParser();
        const doc = parser.parseFromString(text_formatted, 'text/html');
        const spans = doc.querySelectorAll('span[data-document-ids]');

        spans.forEach(span => {
            const documentIds = span.getAttribute('data-document-ids');
            const citationText = span.textContent;
            const link = doc.createElement('a');
            link.className = 'bg-gray-200 hover:bg-blue-300 text-blue-900 px-1 inline rounded cursor-pointer transition-colors duration-200 whitespace-normal text-left';
            link.textContent = citationText;
            link.setAttribute('onclick', `handleCitationClick(${documentIds})`);
            span.parentNode.replaceChild(link, span);
        });

        return doc.body.innerHTML;
    }

    function getWaitingIcon() {
        return `
            <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-500 inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
        `;
    }

    if (typeof window !== 'undefined') {
        window.handleCitationClick = handleCitationClick;
    }
</script>

<div class="flex flex-col h-full bg-white rounded-lg shadow-md overflow-hidden">
    <div class="flex-1 overflow-y-auto p-4 space-y-4">
        <h2 class="text-xl font-bold mb-4 mt-2">Chat with Bron</h2>
        {#each messages as message}
            <div class="flex {message.role === 'user' ? 'justify-end' : 'justify-start'}">
                <div class="max-w-3/4 p-3 rounded-lg {message.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'}">
                    {#if message.role === 'user'}
                        <p>{message.content}</p>
                    {:else if message.role === 'assistant'}
                        {#if message.content}
                            {@html insertClickableCitations(message.content)}
                        {:else}
                            <p>{message.content}</p>
                        {/if}
                    {/if}
                </div>
            </div>
        {/each}
        
        {#if currentMessage}
            <div class="flex justify-start">
                <div class="max-w-3/4 p-3 rounded-lg bg-gray-100 text-gray-600">
                    {#if currentMessage.content === "Rechts vast de relevante documenten. Bron genereert nu een antwoord op uw vraag..." || currentMessage.content === "Bron zoekt nu de relevante documenten..."}
                        <div class="flex items-start">
                          <div class="flex-shrink-0 mr-2 mt-1"> {@html getWaitingIcon()} </div>
                          <p class="flex-grow">{currentMessage.content}</p>
                        </div>
                    {:else}
                        <p>{@html insertClickableCitations(currentMessage.content)}</p>
                    {/if}
                </div>
            </div>
        {/if}
    </div>

    <div class="p-4 bg-white border-t">
        <form on:submit|preventDefault={handleSubmit} class="flex space-x-2">
            <input 
                bind:value={newMessageContent} 
                placeholder="Type your message..." 
                class="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
            <button 
                type="submit" 
                class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
                Send
            </button>
        </form>
    </div>
</div>
