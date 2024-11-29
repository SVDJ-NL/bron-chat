import { writable } from 'svelte/store';

function createSessionStore() {
    const { subscribe, set, update } = writable({
        sessionId: null,
        messages: [],
        documents: [],
        sessionName: ''
    });

    return {
        subscribe,
        set,
        update,
        reset: () => set({
            sessionId: null,
            messages: [],
            documents: [],
            sessionName: ''
        })
    };
}

export const sessionStore = createSessionStore(); 