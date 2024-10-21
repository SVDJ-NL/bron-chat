<script>
    import { goto } from '$app/navigation';
    import Chat from '$lib/components/Chat.svelte';
    import Documents from '$lib/components/Documents.svelte';
    import ShareModal from '$lib/components/ShareModal.svelte';

    export let data;

    let messages = data.messages || [];
    let documents = data.documents || [];
    let selectedDocuments = null;
    let currentMessage = null;
    let citationText = '';
    let citationWords = [];
    let streamedContent = '';
    let showShareModal = false;
    let sessionName = data.sessionName || 'Nieuwe Chatsessie';

    $: if (typeof window !== 'undefined' && sessionName) {
        document.title = sessionName;
    }

    onMount(async () => {
        await loadSession(sessionId);
    });

    async function handleNewMessage(event) {
        addMessage(event.detail);
        if (event.detail.role === 'user') {
            await sendMessage(event.detail);
        }
    }

    async function loadSession(id) {
        const response = await fetch(`${data.API_BASE_URL}/sessions/${id}`);
        if (response.ok) {
            const session = await response.json();
            messages = session.messages;
            documents = session.documents;
            sessionName = session.name || 'Naamloze Sessie';
        } else {
            console.error('Sessie laden mislukt');
        }
    }

    async function sendMessage(message) {
        // ... existing sendMessage logic ...

        // After processing the message, update the URL if it's a new session
        if (!data.sessionId) {
            goto(`/s/${sessionId}`);
        }
    }
</script>

<svelte:head>
    <title>{sessionName}</title>
</svelte:head>

<main class="flex flex-col md:flex-row h-screen bg-gray-100">
    <!-- ... existing layout ... -->
    <div class="order-2 md:order-1 {documents.length > 0 ? 'h-1/2 md:w-2/5' : 'h-full md:w-4/5'} md:h-screen px-4 py-2 md:py-4 flex flex-col overflow-hidden mb-14 md:mb-0 transition-all duration-300">
        <Chat {messages} {currentMessage} on:newMessage={handleNewMessage} on:citationClick={handleCitationClick} />
        <button class="mt-4 bg-blue-500 text-white px-4 py-2 rounded" on:click={openShareModal}>Deel Chat</button>
    </div>
</main>

{#if showShareModal}
    <ShareModal 
        sessionId={data.sessionId} 
        initialSessionName={sessionName} 
        on:close={close} 
    />
{/if}