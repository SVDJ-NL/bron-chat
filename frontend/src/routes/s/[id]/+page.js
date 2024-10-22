import { error } from '@sveltejs/kit';

export async function load({ params, fetch }) {
    const sessionId = params.id;
    try {
        const response = await fetch(`/api/sessions/${sessionId}`);

        if (response.ok) {
            const sessionData = await response.json();
            return {
                sessionId,
                messages: sessionData.messages || [],
                documents: sessionData.documents || [],
                sessionName: sessionData.name || ''
            };
        } else {
            console.error('Failed to fetch session data');
            return {
                sessionId,
                messages: [],
                documents: [],
                sessionName: ''
            };
        }
    } catch (err) {
        console.error('Error fetching session data:', err);
        return {
            sessionId,
            messages: [],
            documents: [],
            sessionName: ''
        };
    }
}
