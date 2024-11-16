<script>
    export let messages = [];
    export let currentMessage = null;
    export let currentStatusMessage = null;
    export let autoScroll = true; 
    export let isFlowActive = false;

    import { createEventDispatcher, onMount, afterUpdate } from 'svelte';
    import Typed from 'typed.js';
    const dispatch = createEventDispatcher();

    let newMessageContent = '';
    let selectedCitation = null;
    let isLoading = false;
    let streamedContent = '';
    let streamedStatusContent = '';
    let copiedMessage = false;
    let sharedMessage = false;

    $: if (currentMessage && currentMessage.content !== streamedContent) {
        streamedContent = currentMessage.content;
    }

    $: if (currentStatusMessage && currentStatusMessage.content !== streamedStatusContent) {
        streamedStatusContent = currentStatusMessage.content;
    }

    function handleSubmit() {
        if (newMessageContent.trim() && !isLoading) {
            isLoading = true;
            isFlowActive = true;
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

    function handleStop() {
        isFlowActive = false;
        dispatch('stopMessageFlow');
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
        initTyped();
    });

    afterUpdate(() => {
        if (autoScroll) {
            scrollToBottom();
        }
    });

    function scrollToBottom() {
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }

    function copyToClipboard(text) {
        if (navigator.clipboard) {
            // Strip HTML tags from text
            const strippedText = text.replace(/<[^>]*>/g, '');
            navigator.clipboard.writeText(strippedText).then(() => {
                copiedMessage = true;
                setTimeout(() => copiedMessage = false, 2000);
                console.log(`Text ${strippedText} copied to clipboard`);
            }).catch(err => {
                console.error('Could not copy text: ', err);
            });
        }
    }

    function shareLinkToClipboard() {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(window.location.href).then(() => {
                sharedMessage = true;
                setTimeout(() => sharedMessage = false, 2000);
                console.log(`Shared link ${window.location.href} copied to clipboard`);
            }).catch(err => {
                console.error('Could not copy text: ', err);
            });
        }
    }

    function initTyped() {
        // Start of Selection`
        let typedSubtitle;

        if (document.querySelector('#typed-title')) {
            typedSubtitle = null;

            const typedTitle = new Typed('#typed-title', {
                strings: ["Vraag alles over 3.5 miljoen openbare overheidsdocumenten"],
                typeSpeed: 50,
                showCursor: false,
            });

            return () => {
                typedTitle.destroy();
                if (typedSubtitle) {
                    typedSubtitle.destroy();
                }
            };
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
        @apply flex flex-col h-full;
    }

    .messages-container {
        @apply flex-1 overflow-y-auto p-4 space-y-4;
    }

    :global(.message-content.status),
    :global(.message-content.current-message) {
        @apply bg-gray-100 text-gray-600 border border-gray-300;
    }

    :global(.message-content.status p) {
        @apply mb-1 mb-0;
    }

    :global(.message-content.status p:last-child) {
        @apply mb-0;
    }

    :global(.chat-wrapper) {
        @apply flex flex-col h-full transition-all duration-300 ease-in-out;
    }
</style>

<div class="chat-wrapper">
    {#if messages.length === 0 }
        <div class="p-4 lg:p-6 h-20 lg:h-24 w-full">
            <h2 id="typed-title" class="text-gray-600 text-center font-semibold text-lg lg:text-xl pb-0.5"></h2>
        </div>
    {/if}
    <div class="chat-container">
        {#if messages && messages.length > 0}
            <div bind:this={chatContainer} class="messages-container">
                {#each messages.filter(message => message.role !== 'system') as message}
                    <div class="flex {message.role === 'user' ? 'justify-end' : 'justify-start'}">
                        <div class="message-content p-3 rounded-lg {message.role === 'user' ? 'bg-blue-500 text-white' : message.type === 'status' ? 'status' : 'bg-gray-200 text-gray-800'}">
                            {#if message.role === 'user'}
                                <p>{message.content}</p>
                            {:else if message.role === 'assistant'}
                                {@html insertClickableCitations(message.content, message.type)}
                                <button on:click={() => copyToClipboard(message.content)} class="ml-0 text-sm text-blue-800 hover:text-blue-900" >
                                    {#if copiedMessage}
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                                            <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                                        </svg>
                                    {:else}
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                                            <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 7.5V6.108c0-1.135.845-2.098 1.976-2.192.373-.03.748-.057 1.123-.08M15.75 18H18a2.25 2.25 0 0 0 2.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 0 0-1.123-.08M15.75 18.75v-1.875a3.375 3.375 0 0 0-3.375-3.375h-1.5a1.125 1.125 0 0 1-1.125-1.125v-1.5A3.375 3.375 0 0 0 6.375 7.5H5.25m11.9-3.664A2.251 2.251 0 0 0 15 2.25h-1.5a2.251 2.251 0 0 0-2.15 1.586m5.8 0c.065.21.1.433.1.664v.75h-6V4.5c0-.231.035-.454.1-.664M6.75 7.5H4.875c-.621 0-1.125.504-1.125 1.125v12c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V16.5a9 9 0 0 0-9-9Z" />
                                        </svg>
                                    {/if}
                                </button>
                                <button on:click={() => shareLinkToClipboard()} class="ml-2 text-sm text-blue-800 hover:text-blue-900">
                                    {#if sharedMessage}
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                                            <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                                        </svg>
                                    {:else}
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-5 h-5">
                                            <path stroke-linecap="round" stroke-linejoin="round" d="M7.217 10.907a2.25 2.25 0 1 0 0 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186 9.566-5.314m-9.566 7.5 9.566 5.314m0 0a2.25 2.25 0 1 0 3.935 2.186 2.25 2.25 0 0 0-3.935-2.186Zm0-12.814a2.25 2.25 0 1 0 3.933-2.185 2.25 2.25 0 0 0-3.933 2.185Z" />
                                        </svg>
                                    {/if}
                                </button>
                            {/if}
                        </div>
                    </div>
                {/each}
                
                {#if currentStatusMessage }
                    <div class="flex justify-start">
                        <div class="message-content p-3 rounded-lg status">
                            <div class="flex items-start">
                                {@html (streamedStatusContent)}
                            </div>
                        </div>
                    </div>
                {/if}

                {#if currentMessage}
                    <div class="flex justify-start">
                        <div class="message-content current-message p-3 rounded-lg bg-gray-200 text-gray-800">
                            {@html insertClickableCitations(streamedContent)}
                        </div>
                    </div>
                {/if}
            </div>
        {/if}
        <div class="input-container p-4 ml-4 mr-4 lg:mr-8 mb-3 lg:ml-4 lg:mx-0 rounded-lg border border-gray-300">
            <form on:submit|preventDefault={handleSubmit} class="flex space-x-2">
                <textarea
                    bind:value={newMessageContent} 
                    placeholder="Chat met Bron..." 
                    class="flex-1 p-2 bg-gray-100 text-gray-900 focus:outline-none focus:ring-0"
                    autofocus
                    rows="1"
                    on:keydown={e => {
                        if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleSubmit(e);
                        }
                    }}
                ></textarea>
                {#if currentMessage != null}
                    <button 
                        type="button" 
                        on:click={handleStop}
                        class="px-1 py-1 bg-blue-800 text-white rounded-full hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-700"
                    >
                        <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" class="icon-2xl">
                            <rect x="8" y="8" width="16" height="16" fill="currentColor"></rect>
                        </svg>
                    </button>
                {:else}
                    <button 
                        type="submit" 
                        class="px-1 py-1 bg-blue-500 text-white rounded-full hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" class="icon-2xl">
                            <path fill-rule="evenodd" clip-rule="evenodd" d="M15.1918 8.90615C15.6381 8.45983 16.3618 8.45983 16.8081 8.90615L21.9509 14.049C22.3972 14.4953 22.3972 15.2189 21.9509 15.6652C21.5046 16.1116 20.781 16.1116 20.3347 15.6652L17.1428 12.4734V22.2857C17.1428 22.9169 16.6311 23.4286 15.9999 23.4286C15.3688 23.4286 14.8571 22.9169 14.8571 22.2857V12.4734L11.6652 15.6652C11.2189 16.1116 10.4953 16.1116 10.049 15.6652C9.60265 15.2189 9.60265 14.4953 10.049 14.049L15.1918 8.90615Z" fill="currentColor"></path>
                        </svg>
                    </button>
                {/if}
            </form>
        </div>
    </div>
</div>
