<script>
    import { removeStopwords, nld } from 'stopword'
    import { onMount } from 'svelte';
    import Chat from './Chat.svelte';
    import Documents from './Documents.svelte';
    import { goto } from '$app/navigation';
    import { API_BASE_URL } from '$lib/config';
    import ChatInput from './ChatInput.svelte';
    import { sessionStore } from '$lib/stores/sessionStore';

    $: messages = $sessionStore.messages || [];
    $: documents = Array.isArray($sessionStore.documents) ? $sessionStore.documents : [];
    $: sessionId = $sessionStore.sessionId;
    $: sessionName = $sessionStore.sessionName;

    let currentStatusMessage = null;
    let selectedDocuments = null;
    let currentMessage = null;
    let citationText = '';
    let citationWords = [];
    let streamedContent = '';
    let eventSource = null; // Store the EventSource instance  
    let autoScroll = true;
    let isLoading = false;
    let isDocumentsPanelOpen = false;
    let initialQuery = null;

    function handleNewMessage(event) {
        addMessage(event.detail);
        if (event.detail.role === 'user') {
            autoScroll = true;
            sendMessage(event.detail);
        }
    }

    function handleNewDocuments(event) {
        const newDocs = Array.isArray(event.detail) ? event.detail : [];
        sessionStore.update(store => ({
            ...store,
            documents: [...store.documents, ...newDocs].sort((a, b) => {
                const dateA = new Date(a.published);
                const dateB = new Date(b.published);
                return dateB - dateA;
            })
        }));
    }

    function handleCitationClick(event) {
        const documentIds = event.detail.documentIds;
        selectedDocuments = documents.filter(doc => documentIds.includes(doc.chunk_id));
        citationText = event.detail.citationText;        
        citationWords = removeStopwords(event.detail.citationText.split(' '), nld);
        autoScroll = false;
        isDocumentsPanelOpen = true;
    }

    function closeDocumentsPanel(event) {
        // Check if the click target is a citation link
        // Start of Selection
        if (
            window.matchMedia('(min-width: 1024px)').matches ||
            event.target.classList.contains('citation-link') || 
            event.target.parentElement.classList.contains('show-all-documents-btn')
        ) {
            return; // Don't close the panel if clicking on a citation
        }

        const documentsPanel = document.querySelector('.documents-panel');
        if (documentsPanel && !documentsPanel.contains(event.target)) {
            isDocumentsPanelOpen = false;
        }
    }

    function addStatusMessage(statusMessage) {
        currentStatusMessage = statusMessage;
    }
  
    function addMessage(message) {
        console.debug('Adding message:', message);
        sessionStore.update(store => ({
            ...store,
            messages: [...store.messages, message]
        }));
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
                addMessage({
                    role: 'assistant',
                    content: streamedContent
                });
            }
            currentMessage = null;
            currentStatusMessage = null;
            streamedContent = '';
            autoScroll = false;
            isLoading = false;
        }
    }

    function handleNewQuestion({ detail }) {
        isLoading = true;
        addMessage({
            role: 'user',
            content: detail.query
        });

        try {
            const params = new URLSearchParams({ 
                query: detail.query,
                session_id: sessionId
            });

            const url = `${API_BASE_URL}/chat?${params}`;
            console.debug('Connecting to EventSource URL:', url);
            
            eventSource = new EventSource(url);
            
            eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleStreamedResponse(data);
                } catch (error) {
                    console.error('Error parsing event data:', error);
                    isLoading = false;
                }
            };
            
            eventSource.onerror = (error) => {
                if (error.currentTarget.readyState === EventSource.CLOSED) {
                    console.debug('EventSource connection closed');
                } else if (error.currentTarget.readyState === EventSource.CONNECTING) {
                    console.debug('EventSource connection connecting');
                } else {
                    console.error('Unexpected EventSource error:', error, eventSource);
                    updateCurrentMessage({ 
                        role: 'assistant', 
                        content: 'An unexpected error occurred while processing your request.' 
                    });

                }
                isLoading = false;
                eventSource.close();
            };
            
            eventSource.onopen = () => {
                console.debug('EventSource connection opened');
            };
            
            eventSource.addEventListener('close', () => {
                console.debug('EventSource connection closed by server');
                eventSource.close();
                isLoading = false;
            });
        } catch (error) {
            console.error('Error sending message:', error);
            updateCurrentMessage({ 
                role: 'assistant', 
                content: 'An error occurred while processing your request.' 
            });
            isLoading = false;
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
                    role: data.role,
                    content: data.content,
                    type: 'status'
                });
                break;
            case 'documents':
                if (Array.isArray(data.documents)) {
                    handleNewDocuments({ detail: data.documents });
                    if (window.matchMedia('(min-width: 1024px)').matches) {
                        isDocumentsPanelOpen = true;
                    }
                } 
                break;
            case 'partial':
                streamedContent += data.content;
                currentMessage = {
                    role: data.role,
                    content: streamedContent
                };
                break;
            case 'citation':
                autoScroll = false;
                currentMessage = {
                    role: data.role,
                    content: data.content,
                    content_original: data.content_original,
                    citations: data.citations
                };
                break;
            case 'full':
                // Get last message from session
                const lastMessage = data.session?.messages?.length > 0 ? 
                    data.session.messages[data.session.messages.length - 1] : 
                    null;

                if (lastMessage) {                
                    addMessage({
                        id: lastMessage.id,
                        role: lastMessage.role,
                        content: lastMessage.formatted_content,
                        content_original: lastMessage.content,
                        feedback: lastMessage.feedback
                    });
                }
                
                currentMessage = null;
                streamedContent = '';
                isLoading = false;

                const session = data.session;
                if (session) {
                    sessionName = session.name;
                    updateDocumentsFromFullSession(session.messages)
                } else {
                    console.error('Received full_session event but no session data:', data);
                }

                break;
            case 'end':   
                console.debug('Received end event');
                isLoading = false;
                currentMessage = null;
                break;
            case 'error':
                console.error('Received error event:', data.content);
                addStatusMessage({ 
                    role: 'assistant', 
                    content: `Er ging iets mis bij het versturen van je vraag. Probeer het opnieuw.` 
                });
                isLoading = false;
                currentMessage = null;
                break;
        }
    }

    function updateDocumentsFromFullSession(messages) {
        if (messages?.length > 0) {
            const lastMessage = messages[messages.length - 1];
            if (lastMessage.documents) {
                addDatabaseIdsToDocuments(lastMessage.documents);
            }
        }
    }

    function addDatabaseIdsToDocuments(newDocuments) {
        // Match documents by chunk_id and update ids
        documents = documents.map(existingDoc => {
            const matchingNewDoc = newDocuments.find(newDoc => newDoc.chunk_id === existingDoc.chunk_id);
            if (matchingNewDoc && matchingNewDoc.id) {
                return {
                    ...existingDoc,
                    id: matchingNewDoc.id
                };
            }
            return existingDoc;
        });
    }

    function handleShowAllDocuments() {
        selectedDocuments = null;
        citationText = '';
        citationWords = [];
        window.resetAllCitations();
        autoScroll = true;
    }

    function openDocumentsPanel() {
        if (document.visibilityState === 'visible' && 
            documents.length > 0 && 
            window.matchMedia('(min-width: 1024px)').matches) {
            isDocumentsPanelOpen = true;
        }
    }

    onMount(() => {
        if (sessionId) {
            openDocumentsPanel();
        }
        
        // Listen for initial query from the home page
        const handleInitialQuery = (event) => {
            const query = event.detail.query;
            if (query) {
                handleNewQuestion({
                    detail: { query }
                });
            }
        };

        window.addEventListener('initialQuery', handleInitialQuery);
        document.addEventListener('click', closeDocumentsPanel);
        document.addEventListener('visibilitychange', openDocumentsPanel);

        return () => {
            window.removeEventListener('initialQuery', handleInitialQuery);
            document.removeEventListener('click', closeDocumentsPanel);
            document.removeEventListener('visibilitychange', openDocumentsPanel);
        };
    });
</script>

<svelte:head>
    <title>{sessionName}</title>
</svelte:head>

<div class="flex flex-col lg:flex-row min-h-screen {messages.length === 0 ? '' : 'pt-16' } bg-gray-100 justify-center items-center overflow-x-hidden">
    <!-- Chat Panel Container -->
    <div class="max-w-[768px] {messages.length === 0 ? '' : 'h-[93vh]'} lg:px-4 transition-all duration-300 ease-in-out w-full
            {isDocumentsPanelOpen ? 'lg:-translate-x-[calc(50%)] lg:w-1/2' : 'translate-x-0'}">
        <div class="order-2 lg:order-1 h-full flex flex-col transition-all duration-300 pt-4 sm:pt-8 md:pt-5">
            <Chat 
                {currentMessage} 
                {currentStatusMessage} 
                {autoScroll}
                isLoading={isLoading}
                on:citationClick={handleCitationClick} 
            />
            <div class="mt-4 px-4">
                <ChatInput
                    {isLoading}
                    on:submit={handleNewQuestion}
                    on:stop={handleStopMessageFlow}
                />
            </div>
        </div>
    </div>

    <!-- Documents Panel -->
    {#if documents.length > 0}
        <div class="documents-panel fixed lg:block bottom-[71px] lg:right-0 lg:top-16 lg:bottom-0 h-[calc(100vh-8rem)] lg:h-[90vh] w-full lg:w-1/2 bg-gray-100 transform transition-transform duration-300
            {isDocumentsPanelOpen ? 'translate-x-0' : 'translate-x-full'}">
            <div class="h-full">
                <Documents 
                    {selectedDocuments}
                    {citationText}
                    {citationWords}
                    {isDocumentsPanelOpen}
                    on:showAllDocuments={handleShowAllDocuments}
                    on:togglePanel={() => isDocumentsPanelOpen = !isDocumentsPanelOpen}
                />
            </div>
        </div>
    {/if}
</div>

<style lang="postcss">    
    @tailwind base;
    @tailwind components;
    @tailwind utilities;

    :global(html, body) {
        @apply h-full;
    }

    /* Make both panels scrollable */
    /* main > div {
        @apply overflow-y-auto;
    } */
</style>
