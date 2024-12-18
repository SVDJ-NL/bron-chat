<script>
    import ChatLayout from '$lib/components/ChatLayout.svelte';
    import { sessionStore } from '$lib/stores/sessionStore';

    export let data;

    $: sessionStore.set({
        sessionId: data.sessionId,
        messages: data.messages || [],
        documents: data.documents || [],
        sessionName: data.sessionName || 'Bron chat',
        locations: data.locations || []
    });
</script>

<ChatLayout />

