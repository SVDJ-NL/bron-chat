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
        // console.log('Citation clicked:', event.detail);
        const documentIds = event.detail.documentIds;
        selectedDocuments = documents.filter(doc => documentIds.includes(doc.id));
        citationText = event.detail.citationText;
        
        citationWords = removeStopwords(event.detail.citationText.split(' '), nld);
        // console.log('Citation words:', citationWords);
    }

    function addMessage(message) {
        messages = [...messages, message];
        // console.log('Adding message:', message);
    }

    function updateCurrentMessage(message) {
        currentMessage = message;
    }

    export const API_BASE_URL = import.meta.env.PUBLIC_API_URL;

    async function sendMessage(message) {
        try {
            updateCurrentMessage({ role: 'assistant', content: 'Bron zoekt nu de relevante documenten...' });
            
            const response = await fetch(`https://bron.ngrok.app/api/chat`, {
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
                updateCurrentMessage({
                    role: 'assistant',
                    content: data.content
                });
                break;
            case 'full':
                addMessage({
                    role: 'assistant',
                    content: data.content,
                    content_original: data.content_original
                });
                currentMessage = null;
                break;
        }
    }

    function handleShowAllDocuments() {
        selectedDocuments = null;
        citationText = '';
        citationWords = [];
        window.resetAllCitations();
    }

    onMount(async () => {
        // try {
        //     handleNewMessage({
        //         detail: {
        //             role: 'user',
        //             content: 'Klimaat Almelo'
        //         }
        //     });
        // } catch (error) {
        //     console.error('Error in onMount:', error);
        // }
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
