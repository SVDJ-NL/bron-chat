<script>
    export let messages = [];
    export let currentMessage = null;
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

        // Use a regex to find and replace spans with citation links
        const citationRegex = /<span class="citation-link" data-document-ids="([^"]+)">(.*?)<\/span>/g;
        const formattedText = text_formatted.replace(citationRegex, (match, documentIds, citationText) => {
            return `<a class="citation-link" onclick="handleCitationClick(${documentIds}, '${citationText.replace(/'/g, "\\'")}')">${citationText}</a>`;
        });

        return formattedText;
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

<div class="chat-container md:py-2 md:px-2">
    <div bind:this={chatContainer} class="messages-container">
        {#if messages && messages.length > 0}
            {#each messages.filter(message => message.role !== 'system') as message}
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
        {/if}
        
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
                placeholder="Chat met Bron..." 
                class="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
            <button 
                type="submit" 
                class="px-1 py-1 bg-blue-500 text-white rounded-full hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
                <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" class="icon-2xl"><path fill-rule="evenodd" clip-rule="evenodd" d="M15.1918 8.90615C15.6381 8.45983 16.3618 8.45983 16.8081 8.90615L21.9509 14.049C22.3972 14.4953 22.3972 15.2189 21.9509 15.6652C21.5046 16.1116 20.781 16.1116 20.3347 15.6652L17.1428 12.4734V22.2857C17.1428 22.9169 16.6311 23.4286 15.9999 23.4286C15.3688 23.4286 14.8571 22.9169 14.8571 22.2857V12.4734L11.6652 15.6652C11.2189 16.1116 10.4953 16.1116 10.049 15.6652C9.60265 15.2189 9.60265 14.4953 10.049 14.049L15.1918 8.90615Z" fill="currentColor"></path></svg>
            </button>
        </form>
    </div>
</div>
