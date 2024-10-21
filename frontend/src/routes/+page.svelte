<script>
    import { removeStopwords, nld } from 'stopword'
    import { onMount } from 'svelte';
    import Chat from '../components/Chat.svelte';
    import Documents from '../components/Documents.svelte';

    let messages = [];
    let statusMessages = [];
    let currentStatusMessage = null;
    let documents = [];
    let selectedDocuments = null;
    let currentMessage = null;
    let citationText = '';
    let citationWords = [];
    let streamedContent = '';
    let sessionId = null;

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

    function addStatusMessage(statusMessage) {
        statusMessages = [...statusMessages, statusMessage];
    }

    function addMessage(message) {
        messages = [...messages, message];
    }

    function updateCurrentMessage(message) {
        currentMessage = message;
    }
    
    function updateCurrentStatusMessage(statusMessage) {
        currentStatusMessage = statusMessage + '\n';
    }

    function setSessionId(id) {
        sessionId = id;
        console.log('Session ID set to:', sessionId);
    }

    export const API_BASE_URL = import.meta.env.VITE_PUBLIC_API_URL;

    async function sendMessage(message) {
        try {
            streamedContent = '';
            
            const params = new URLSearchParams({ 
                content: message.content,
                session_id: sessionId
            });
            const eventSource = new EventSource(`${API_BASE_URL}/chat?${params}`);
            
            eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.session_id && !sessionId) {
                        sessionId = data.session_id;
                        // Optionally, you can update the URL here to include the session ID
                        // window.history.pushState({}, '', `/chat/${sessionId}`);
                    }
                    handleStreamedResponse(data);
                } catch (error) {
                    console.error('Error parsing event data:', error);
                }
            };
            
            eventSource.onerror = (error) => {
                console.log('EventSource error:', error);
                if (eventSource.readyState === EventSource.CLOSED) {
                    console.log('EventSource connection closed');
                } else {
                    console.error('Unexpected EventSource error:', error);
                    updateCurrentMessage({ role: 'assistant', content: 'An unexpected error occurred while processing your request.' });
                }
                eventSource.close();
            };
            
            eventSource.onopen = () => {
                console.log('EventSource connection opened');
            };
            
            eventSource.addEventListener('close', () => {
                console.log('EventSource connection closed by server');
                eventSource.close();
                currentMessage = null;
                currentStatusMessage = null;
            });
        } catch (error) {
            console.error('Error sending message:', error);
            updateCurrentMessage({ role: 'assistant', content: 'An error occurred while processing your request.' });
        }
    }

    function handleStreamedResponse(data) {
        switch (data.type) {
            case 'session':
                setSessionId(data.session_id);
                break;
            case 'status':
                updateCurrentStatusMessage({
                    role: 'assistant',
                    content: data.content,
                    type: 'status'
                });
                break;
            case 'documents':
                if (data.documents) {
                    handleNewDocuments({ detail: data.documents });
                } 
                break;
            case 'partial':
                streamedContent += data.content;
                updateCurrentMessage({
                    role: 'assistant',
                    content: streamedContent
                });
                break;
            case 'citation':
                updateCurrentMessage({
                    role: 'assistant',
                    content: data.content,
                    content_original: data.content_original,
                    citations: data.citations
                });
                break;
            case 'full':
                addMessage({
                    role: 'assistant',
                    content: data.content,
                    content_original: data.content_original,
                    citations: data.citations
                });
                currentMessage = null;
                break;
            case 'end':   
                console.log('Received end event');
                break;
            case 'error':
                console.error('Received error event:', data.content);
                updateCurrentMessage({ role: 'assistant', content: `An error occurred: ${data.content}` });
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
        <Chat {messages} {currentMessage} {statusMessages} {currentStatusMessage} on:newMessage={handleNewMessage} on:citationClick={handleCitationClick} />
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
