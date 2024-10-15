<script>
    import { onMount } from 'svelte';
    import Chat from '../components/Chat.svelte';
    import Documents from '../components/Documents.svelte';

    let messages = [];
    let documents = [];
    let selectedDocuments = null;
    let currentMessage = null;

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
        console.log('All documents:', documents);
        console.log('Citation clicked:', event.detail);
        const documentIds = event.detail;
        // Update selectedDocuments to be an array of documents
        selectedDocuments = documents.filter(doc => documentIds.includes(doc.id));
        console.log('Selected documents:', selectedDocuments);
    }

    function addMessage(message) {
        messages = [...messages, message];
        // console.log('Adding message:', message);
    }

    function updateCurrentMessage(message) {
        currentMessage = message;
    }

    async function sendMessage(message) {
        try {
            updateCurrentMessage({ role: 'assistant', content: 'Bron zoekt nu de relevante documenten...' });
            
            const response = await fetch('http://localhost:8000/chat', {
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

<main class="flex h-screen bg-gray-100">
    <div class="w-1/2 p-4 flex flex-col">
        <Chat {messages} {currentMessage} on:newMessage={handleNewMessage} on:citationClick={handleCitationClick} />
    </div>
    <div class="w-1/2 p-4 flex flex-col">
        <Documents 
            {documents} 
            {selectedDocuments} 
            on:showAllDocuments={handleShowAllDocuments} 
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
</style>
