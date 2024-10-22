<script>
    import { removeStopwords, nld } from 'stopword'
    import { onMount } from 'svelte';
    import Chat from './Chat.svelte';
    import Documents from './Documents.svelte';
    import { goto } from '$app/navigation';

    export let sessionId = null;
    export let sessionName = '';
    export let initialMessages = [];
    export let initialDocuments = [];

    let messages = initialMessages || [];  // Ensure messages is always an array
    let statusMessages = [];
    let currentStatusMessage = null;
    let documents = Array.isArray(initialDocuments) ? initialDocuments : [];
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
        documents = Array.isArray(event.detail) ? event.detail : [];
    }

    function handleCitationClick(event) {
        const documentIds = event.detail.documentIds;
        selectedDocuments = documents.filter(doc => documentIds.includes(doc.id));
        citationText = event.detail.citationText;        
        citationWords = removeStopwords(event.detail.citationText.split(' '), nld);
    }

    function addStatusMessage(statusMessage) {
        statusMessages = [...statusMessages, statusMessage];
        currentStatusMessage = statusMessage;
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
        if (typeof window !== 'undefined') {
            try {
                goto(`/s/${sessionId}`, { replaceState: true });
                console.log('URL updated successfully');
            } catch (error) {
                console.error('Error updating URL:', error);
            }
        } else {
            console.log('Window object not available, skipping URL update');
        }
    }

    export const API_BASE_URL = import.meta.env.VITE_PUBLIC_API_URL;

    async function sendMessage(message) {
        try {
            streamedContent = '';
            
            let params;
            if (sessionId === null || sessionId === undefined || sessionId === '') {                
                params = new URLSearchParams({ 
                    content: message.content
                });
                console.log('Sending message without session ID');
            } else {
                params = new URLSearchParams({ 
                    content: message.content,
                    session_id: sessionId
                });
                console.log('Sending message with session ID:', sessionId);
            }
            
            const url = `${API_BASE_URL}/chat?${params}`;
            console.log('Connecting to EventSource URL:', url);
            
            const eventSource = new EventSource(url);
            
            eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
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
                console.log('Received session event:', data);
                setSessionId(data.session_id);
                break;
            case 'status':
                addStatusMessage({
                    role: 'assistant',
                    content: data.content,
                    type: 'status'
                });
                break;
            case 'documents':
                if (Array.isArray(data.documents)) {
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

    function handleShowAllDocuments() {
        selectedDocuments = null;
        citationText = '';
        citationWords = [];
        window.resetAllCitations();
    }

    async function createNewSession() {
        try {
            const response = await fetch(`${API_BASE_URL}/new_session`, {
                method: 'POST',
            });
            const session = await response.json();
            console.log('New session created:', session);
            if (session.id) {
                setSessionId(session.id);
                sessionName = session.name;
            } else {
                console.error('Failed to create a new session');
            }
        } catch (error) {
            console.error('Error creating new session:', error);
        }
    }

    onMount(async () => {
        if (!sessionId) {
            await createNewSession();
        }
    });
</script>

<svelte:head>
    <title>{sessionName}</title>
</svelte:head>

<main class="flex flex-col md:flex-row h-screen bg-gray-100">
    <div class="order-1 md:order-2 {documents.length > 0 ? 'h-1/2 md:w-3/5' : 'h-1/12 md:w-1/5'} md:h-screen px-4 py-2 md:py-4 flex flex-col overflow-hidden transition-all duration-300">
        <Documents 
            documents={documents}
            selectedDocuments={selectedDocuments}
            citationText={citationText}
            citationWords={citationWords}
            on:showAllDocuments={handleShowAllDocuments} 
        />
    </div>
    <div class="order-2 md:order-1 {documents.length > 0 ? 'h-1/2 md:w-2/5' : 'h-full md:w-4/5'} md:h-screen px-4 py-2 md:py-4 flex flex-col overflow-hidden mb-14 md:mb-0 transition-all duration-300">
        <Chat 
            messages={messages} 
            currentMessage={currentMessage} 
            statusMessages={statusMessages} 
            currentStatusMessage={currentStatusMessage} 
            on:newMessage={handleNewMessage} 
            on:citationClick={handleCitationClick} 
        />
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
