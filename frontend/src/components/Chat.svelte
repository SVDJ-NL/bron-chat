<script>
    export let messages = [];
    export let currentMessage = null;
    export let statusMessages = [];
    export let currentStatusMessage = null;

    import { createEventDispatcher, onMount, afterUpdate } from 'svelte';
    const dispatch = createEventDispatcher();

    let newMessageContent = '';
    let selectedCitation = null;
    let isLoading = false;
    let streamedContent = '';
    let streamedStatusContent = '';

    $: if (currentMessage && currentMessage.content !== streamedContent) {
        streamedContent = currentMessage.content;
    }

    $: if (currentStatusMessage && currentStatusMessage.content !== streamedStatusContent) {
        streamedStatusContent = currentStatusMessage.content;
    }

    function handleSubmit() {
        if (newMessageContent.trim() && !isLoading) {
            isLoading = true;
            dispatch('newMessage', {
                role: 'user',
                content: newMessageContent
            });
            newMessageContent = '';
            // Use setTimeout to wait for UI update
            setTimeout(() => {
                isLoading = false;
            }, 100);
        }
    }

    function resetAllCitations() {
        if (typeof document !== 'undefined') {
            const allCitations = document.querySelectorAll('.citation-link');
            allCitations.forEach(citation => {
                citation.classList.remove('selected');
            });
        }
        selectedCitation = null;
    }

    function resetSelectedCitation() {
        if (selectedCitation) {
            selectedCitation.classList.remove('selected');
            selectedCitation = null;
        }
    }

    function insertClickableCitations(text_formatted, messageType) {
        if (messageType === 'status') {
            return text_formatted.split('\n').map(line => `<p>${line}</p>`).join('');
        }
        const parser = new DOMParser();
        const doc = parser.parseFromString(text_formatted, 'text/html');
        const spans = doc.querySelectorAll('span[data-document-ids]');

        spans.forEach(span => {
            const documentIds = span.getAttribute('data-document-ids');
            const citationText = span.textContent;
            const link = doc.createElement('a');
            link.className = 'citation-link';
            link.textContent = citationText;
            link.setAttribute('onclick', `handleCitationClick(${documentIds}, "${citationText}")`);
            span.parentNode.replaceChild(link, span);
        });

        return doc.body.innerHTML;
    }

    function handleCitationClick(documentIds, citationText) {
        resetAllCitations();
        if (selectedCitation) {
            selectedCitation.classList.remove('selected');
        }
        dispatch('citationClick', { documentIds, citationText });
        selectedCitation = event.target;
        selectedCitation.classList.add('selected');
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
        window.resetSelectedCitation = resetSelectedCitation;
        window.resetAllCitations = resetAllCitations;
    }

    let chatContainer;

    onMount(() => {
        scrollToBottom();
    });

    afterUpdate(() => {
        scrollToBottom();
    });

    function scrollToBottom() {
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }
</script>

<style lang="postcss">
    :global(.citation-link) {
        @apply bg-gray-200 text-blue-900 px-0.5 py-0.5 -mx-0.5 inline rounded cursor-pointer transition-colors duration-200 whitespace-normal text-left relative;
    }

    :global(.citation-link:hover) {
        @apply bg-blue-200;
    }

    :global(.citation-link.selected) {
        @apply bg-yellow-200;
    }

    :global(.citation-link.selected:hover) {
        @apply bg-yellow-300;
    }

    :global(.message-content h1) {
        @apply text-xl font-bold mb-4 mt-6;
    }

    :global(.message-content h2) {
        @apply text-lg font-bold mb-3 mt-5;
    }

    :global(.message-content h3) {
        @apply text-base font-bold mb-2 mt-4;
    }

    :global(.message-content p) {
        @apply mb-4;
    }

    :global(.message-content ul, .message-content ol) {
        @apply mb-4 pl-8;
    }

    :global(.message-content ul) {
        @apply list-disc;
    }

    :global(.message-content ol) {
        @apply list-decimal;
    }

    :global(.message-content li) {
        @apply mb-2;
    }

    :global(.message-content blockquote) {
        @apply border-l-4 border-gray-300 pl-4 italic my-4;
    }

    :global(.message-content code) {
        @apply bg-gray-100 rounded px-1 py-0.5 font-mono text-sm;
    }

    :global(.message-content pre) {
        @apply bg-gray-100 rounded p-4 overflow-x-auto mb-4;
    }

    :global(.message-content pre code) {
        @apply bg-transparent p-0;
    }

    .chat-container {
        @apply flex flex-col h-full bg-white rounded-lg shadow-md overflow-hidden;
    }

    .messages-container {
        @apply flex-1 overflow-y-auto p-4 space-y-4;
    }

    .input-container {
        @apply p-4 bg-white border-t;
    }

    :global(.message-content.status) {
        @apply bg-gray-100 text-gray-600 border border-gray-300;
    }

    :global(.message-content.status p) {
        @apply mb-1 mb-0;
    }

    :global(.message-content.status p:last-child) {
        @apply mb-0;
    }
</style>

<div class="chat-container">
    <div bind:this={chatContainer} class="messages-container">
        <h2 class="text-lg font-bold mb-4">Chat with Bron</h2>
        {#each messages as message}
            <div class="flex {message.role === 'user' ? 'justify-end' : 'justify-start'}">
                <div class="message-content max-w-3/4 p-3 rounded-lg {message.role === 'user' ? 'bg-blue-500 text-white' : message.type === 'status' ? 'status' : 'bg-gray-200 text-gray-800'}">
                    {#if message.role === 'user'}
                        <p>{message.content}</p>
                    {:else if message.role === 'assistant'}
                        {@html insertClickableCitations(message.content, message.type)}
                    {/if}
                </div>
            </div>
        {/each}
        
        {#if currentStatusMessage }
            <div class="flex justify-start">
                <div class="message-content max-w-3/4 p-3 rounded-lg status">
                    <div class="flex items-start">
                        {@html (streamedStatusContent)}
                    </div>
                </div>
            </div>
        {/if}

        {#if currentMessage}
            <div class="flex justify-start">
                <div class="message-content max-w-3/4 p-3 rounded-lg bg-gray-100 text-gray-600">
                    {@html insertClickableCitations(streamedContent)}
                </div>
            </div>
        {/if}
    </div>

    <div class="input-container">
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
