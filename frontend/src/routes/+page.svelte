<script>
    import { removeStopwords, nld } from 'stopword'
    import { onMount } from 'svelte';
    import Chat from '../components/Chat.svelte';
    import Documents from '../components/Documents.svelte';

    let messages = [];
    let documents = [];
    let selectedDocuments = null;
    let currentMessage = null;
    let citationText = '';
    let citationWords = [];
    let streamedContent = '';

    function handleNewMessage(event) {
        addMessage(event.detail);
        if (event.detail.role === 'user') {
            sendMessage(event.detail);
        }
    }

    function handleNewDocuments(event) {
        documents = event.detail;
    }

    function handleCitationClick(event) {
        const documentIds = event.detail.documentIds;
        selectedDocuments = documents.filter(doc => documentIds.includes(doc.id));
        citationText = event.detail.citationText;
        
        citationWords = removeStopwords(event.detail.citationText.split(' '), nld);
    }

    function addMessage(message) {
        messages = [...messages, message];
    }

    function updateCurrentMessage(message) {
        currentMessage = message;
    }

    export const API_BASE_URL = import.meta.env.VITE_PUBLIC_API_URL;

    async function sendMessage(message) {
        try {
            streamedContent = '';
            
            const response = await fetch(`${API_BASE_URL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: message.content }),
            });
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.trim()) {
                        const data = JSON.parse(line);
                        handleStreamedResponse(data);
                    }
                }
            }

            if (buffer) {
                const data = JSON.parse(buffer);
                handleStreamedResponse(data);
            }

            currentMessage = null;
        } catch (error) {
            console.error('Error sending message:', error);
            updateCurrentMessage({ role: 'assistant', content: 'An error occurred while processing your request.' });
        }
    }

    function handleStreamedResponse(data) {
        switch (data.type) {
            case 'initial':
                if (data.documents) {
                    handleNewDocuments({ detail: data.documents });
                }
                addMessage({
                    role: 'assistant',
                    content: data.content,
                });                
                break;
            case 'partial':
                streamedContent += data.content;
                updateCurrentMessage({
                    role: 'assistant',
                    content: streamedContent
                });
                break;
            case 'citation':
                console.log('Citation:', data);
                updateCurrentMessage({
                    role: 'assistant',
                    content: data.content,
                    content_original: data.content_original,
                    citations: data.citations
                });
                break;
            case 'full':
                // Add this case to handle the final message

                // Strip the loading message from the content
                let content_original = data.content_original || '';
                let content = data.content || '';

                // Strip the loading message from the content
                if (content_original) {
                    content_original = content_original.replace("<p><em>De bronnen om deze tekst te onderbouwen worden er nu bij gezocht.</em></p>", "");
                }

                // Also update the original content if it exists
                if (content) {
                    content = content.replace("<p><em>De bronnen om deze tekst te onderbouwen worden er nu bij gezocht.</em></p>", "");
                }

                addMessage({
                    role: 'assistant',
                    content: content,
                    content_original: content_original,
                    citations: data.citations
                });
                currentMessage = null;
                break;
        }
    }

    function addCitationToText(text, citation) {
        const { start, end, document_ids } = citation;
        
        // Ensure start and end are valid numbers
        const safeStart = Math.max(0, Math.min(start, text.length));
        const safeEnd = Math.max(safeStart, Math.min(end, text.length));
        
        const beforeCitation = text.slice(0, safeStart);
        const citationText = text.slice(safeStart, safeEnd);
        const afterCitation = text.slice(safeEnd);
        
        // Ensure document_ids is an array and stringify it properly
        const safeDocumentIds = Array.isArray(document_ids) ? document_ids : [];
        const documentIdListString = JSON.stringify(safeDocumentIds);
        
        const citationSpan = `<span class="citation-link" data-document-ids='${documentIdListString}'>${citationText}</span>`;
        
        return beforeCitation + citationSpan + afterCitation;
    }

    function handleShowAllDocuments() {
        selectedDocuments = null;
        citationText = '';
        citationWords = [];
        window.resetAllCitations();
    }

    onMount(async () => {
        // Commented out auto-message on mount
    });
</script>

<main class="flex flex-col md:flex-row h-screen bg-gray-100">
    <div class="order-1 md:order-2 {documents.length > 0 ? 'h-1/2 md:w-3/5' : 'h-1/12 md:w-1/5'} md:h-screen px-4 py-2 md:py-4 flex flex-col overflow-hidden transition-all duration-300">
        <Documents 
            {documents} 
            {selectedDocuments} 
            {citationText} 
            {citationWords}
            on:showAllDocuments={handleShowAllDocuments} 
        />
    </div>
    <div class="order-2 md:order-1 {documents.length > 0 ? 'h-1/2 md:w-2/5' : 'h-full md:w-4/5'} md:h-screen px-4 py-2 md:py-4 flex flex-col overflow-hidden mb-14 md:mb-0 transition-all duration-300">
        <Chat {messages} {currentMessage} on:newMessage={handleNewMessage} on:citationClick={handleCitationClick} />
    </div>
</main>

<style lang="postcss">    
    @tailwind base;
    @tailwind components;
    @tailwind utilities;

    :global(html, body) {
        @apply h-full;
    }

    /* Make both panels scrollable */
    main > div {
        @apply overflow-y-auto;
    }
</style>
