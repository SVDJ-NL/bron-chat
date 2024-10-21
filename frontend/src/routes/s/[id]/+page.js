import { error } from '@sveltejs/kit';

export async function load({ params, fetch }) {
    const sessionId = params.id;
    const response = await fetch(`/api/sessions/${sessionId}`);

    if (response.ok) {
        const sessionData = await response.json();
        return {
            sessionId,
            messages: sessionData.messages,
            documents: sessionData.documents,
            sessionName: sessionData.name
        };
    }

    throw error(404, 'Session not found');
}

