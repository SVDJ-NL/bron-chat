<script>
    import ChatLayout from '$lib/components/ChatLayout.svelte';
    import { page } from '$app/stores';
    import { API_BASE_URL } from '$lib/config';

    export let data;

    $: ({ sessionId, messages, documents, sessionName } = data);
</script>

<ChatLayout 
    sessionId={sessionId}
    sessionName={sessionName || ''}
    initialMessages={messages || []}
    initialDocuments={documents || []}
/>

