import { error } from '@sveltejs/kit';

export async function load({ params, fetch }) {
    const sessionId = params.id;
    const API_BASE_URL = import.meta.env.PUBLIC_API_URL;

    try {
        const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`);

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
