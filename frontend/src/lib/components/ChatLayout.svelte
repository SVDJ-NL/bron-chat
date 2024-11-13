<script>
    import { removeStopwords, nld } from 'stopword'
    import { onMount } from 'svelte';
    import Chat from './Chat.svelte';
    import Documents from './Documents.svelte';
    import { goto } from '$app/navigation';
    import { API_BASE_URL } from '$lib/config';

    export let sessionId = null;
    export let sessionName = '';
    export let initialMessages = [];
    export let initialDocuments = [];

    let messages = initialMessages || [];  // Ensure messages is always an array
    let currentStatusMessage = null;
    let documents = Array.isArray(initialDocuments) ? initialDocuments : [];
    let selectedDocuments = null;
    let currentMessage = null;
    let citationText = '';
    let citationWords = [];
    let streamedContent = '';
    let eventSource = null; // Store the EventSource instance  
    let autoScroll = true;
    let isFlowActive = false;
    function handleNewMessage(event) {
        addMessage(event.detail);
        if (event.detail.role === 'user') {
            autoScroll = true;
            sendMessage(event.detail);
        }
    }

    function handleNewDocuments(event) {
        const newDocs = Array.isArray(event.detail) ? event.detail : [];
        documents = [...documents, ...newDocs];
        // Sort documents by publication date (newest first)
        documents = documents.sort((a, b) => {
            const dateA = new Date(a.published);
            const dateB = new Date(b.published);
            return dateB - dateA;
        });
    }

    function handleCitationClick(event) {
        const documentIds = event.detail.documentIds;
        selectedDocuments = documents.filter(doc => documentIds.includes(doc.id));
        citationText = event.detail.citationText;        
        citationWords = removeStopwords(event.detail.citationText.split(' '), nld);
        autoScroll = false;
    }

    function addStatusMessage(statusMessage) {
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
        console.debug('Session ID set to:', sessionId);
        if (typeof window !== 'undefined') {
            try {
                goto(`/s/${sessionId}`, { replaceState: true });
                console.debug('URL updated successfully');
            } catch (error) {
                console.error('Error updating URL:', error);
            }
        } else {
            console.debug('Window object not available, skipping URL update');
        }
    }

    function handleStopMessageFlow() {
        if (eventSource) {
            eventSource.close();
            console.debug('EventSource connection closed by user');
            if (streamedContent) {
                updateCurrentMessage({
                    role: 'assistant',
                    content: streamedContent
                });
            }
            currentMessage = null;
            currentStatusMessage = null;
            autoScroll = false;
        }
    }

    async function sendMessage(message) {
        try {
            streamedContent = '';
            
            let params;
            if (sessionId === null || sessionId === undefined || sessionId === '') {                
                params = new URLSearchParams({ 
                    query: message.content
                });
                console.debug('Sending message without session ID');
            } else {
                params = new URLSearchParams({ 
                    query: message.content,
                    session_id: sessionId
                });
                console.debug('Sending message with session ID:', sessionId);
            }

            const url = `${API_BASE_URL}/chat?${params}`;
            console.debug('Connecting to EventSource URL:', url);
            
            eventSource = new EventSource(url);
            
            eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleStreamedResponse(data);
                } catch (error) {
                    console.error('Error parsing event data:', error);
                    isFlowActive = false;
                }
            };
            
            eventSource.onerror = (error) => {
                console.error('EventSource error:', error);
                if (eventSource.readyState === EventSource.CLOSED) {
                    console.debug('EventSource connection closed');
                } else {
                    console.error('Unexpected EventSource error:', error);
                    updateCurrentMessage({ role: 'assistant', content: 'An unexpected error occurred while processing your request.' });
                }
                eventSource.close();
                isFlowActive = false;
            };
            
            eventSource.onopen = () => {
                console.debug('EventSource connection opened');
            };
            
            eventSource.addEventListener('close', () => {
                console.debug('EventSource connection closed by server');
                eventSource.close();
                isFlowActive = false;
                // currentMessage = null;
                // currentStatusMessage = null;
            });
        } catch (error) {
            console.error('Error sending message:', error);
            updateCurrentMessage({ role: 'assistant', content: 'An error occurred while processing your request.' });
            isFlowActive = false;
        }
    }

    function handleStreamedResponse(data) {
        switch (data.type) {
            case 'session':
                console.debug('Received session event:', data);
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
                autoScroll = false;
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
                // autoScroll = true;
                break;
            case 'session_name':
                sessionName = data.content;
                break;
            case 'end':   
                console.debug('Received end event');
                isFlowActive = false;
                break;
            case 'error':
                console.error('Received error event:', data.content);
                updateCurrentMessage({ role: 'assistant', content: `An error occurred: ${data.content}` });
                isFlowActive = false;
                break;
        }
    }

    function handleShowAllDocuments() {
        selectedDocuments = null;
        citationText = '';
        citationWords = [];
        window.resetAllCitations();
        autoScroll = true;
    }

    async function createNewSession() {
        try {
            const response = await fetch(`${API_BASE_URL}/new_session`, {
                method: 'POST',
            });
            const session = await response.json();
            console.debug('New session created:', session);
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

<main class="flex flex-col md:flex-row min-h-screen pt-16 bg-gray-100 justify-center items-center">
    <!-- Chat Panel Container -->
    <div class="w-full max-w-[768px] {messages.length === 0 ? '' : 'h-[80vh]'} px-4 transition-all duration-300 ease-in-out">
        <div class="order-2 md:order-1 h-full flex flex-col overflow-hidden transition-all duration-300">
            <Chat 
                messages={messages} 
                currentMessage={currentMessage} 
                currentStatusMessage={currentStatusMessage} 
                autoScroll={autoScroll}
                isFlowActive={isFlowActive}
                on:newMessage={handleNewMessage} 
                on:citationClick={handleCitationClick} 
                on:stopMessageFlow={handleStopMessageFlow}
            />
        </div>
    </div>

    <!-- Documents Panel -->
    {#if documents.length > 0}
        <div class="fixed right-0 top-16 bottom-0 w-1/3 bg-white shadow-lg transform transition-transform duration-300 overflow-hidden">
            <div class="h-full px-4 md:py-2">
                <Documents 
                    documents={documents}
                    selectedDocuments={selectedDocuments}
                    citationText={citationText}
                    citationWords={citationWords}
                    on:showAllDocuments={handleShowAllDocuments} 
                />
            </div>
        </div>
    {/if}
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
