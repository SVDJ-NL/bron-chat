<script>
    import { page } from '$app/stores';
    import { API_BASE_URL } from '$lib/config';
    import { onMount } from 'svelte';

    let showModal = false;
    let formData = {
        question: '',
        name: '',
        email: '',
        session_id: $page.params.id
    };
    let showThankYou = false;
    let isSubmitting = false;
    let modalContent;

    function handleClickOutside(event) {
        if (modalContent && !modalContent.contains(event.target)) {
            closeModal();
        }
    }

    function closeModal() {
        showModal = false;
        showThankYou = false;
        formData = { question: '', name: '', email: '', session_id: $page.params.id };
    }

    async function handleSubmit() {
        isSubmitting = true;
        try {
            // Convert form data to URL search params
            const params = new URLSearchParams({
                question: formData.question,
                name: formData.name || '',
                email: formData.email || '',
                session_id: formData.session_id || ''
            });

            const response = await fetch(`${API_BASE_URL}/feedback?${params.toString()}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (response.ok) {
                showThankYou = true;
            }
        } catch (error) {
            console.error('Error submitting feedback:', error);
        } finally {
            isSubmitting = false;
        }
    }
</script>

<header class="fixed w-full top-0 z-10">
    <div class="px-4 sm:px-6 lg:px-8">
        <div class="flex h-16">
            <div class="flex-shrink-0 flex items-center relative">
                <a href="https://chat.bron.live">
                    <img class="hidden sm:block h-8 w-auto ml-1" src="/bron-logo.svg" alt="Bron Logo" />
                    <img class="block sm:hidden h-6 w-auto ml-0.5" src="/bron-logo-small.svg" alt="Bron Logo" />
                </a>
                <img
                    class="absolute top-5 -right-14 lg:top-4 lg:-right-16 h-4 w-auto sm:h-5"
                    src="/beta-badge.svg" 
                    alt="Beta"
                />
                <a href="https://chat.bron.live" target="_blank" class="ml-2 lg:ml-0 lg:mt-1">
                    <span class="text-black text-2xl lg:text-3xl font-semibold uppercase">Chat</span>
                    <!-- <svg xmlns="http://www.w3.org/2000/svg" class="inline-block h-4 w-4 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg> -->
                </a>
            </div>
            <div class="hidden lg:flex items-center ml-auto pr-4">
                <button
                    on:click={() => showModal = true}
                    class="text-blue-600 hover:underline font-medium"
                >
                    Hebben wij vandaag je vraag kunnen beantwoorden?
                </button>
            </div>
            <div class="flex-shrink-0 flex items-center">
                <a href="https://svdj.nl" target="_blank">
                    <img class="hidden sm:block h-7 lg:h-12 w-auto" src="/incubator.png" alt="SvdJ Incubator Logo" />
                    <img class="block sm:hidden h-6 lg:h-10 w-auto" src="/incubator.png" alt="SvdJ Incubator Logo" />
                </a>
                <a href="https://openstate.eu" target="_blank">
                    <img class="hidden sm:block h-7 lg:h-11 w-auto" src="/open-state-foundation-logo.svg" alt="Open State Foundation Logo" />
                    <img class="block sm:hidden h-6 lg:h-9 w-auto ml-1" src="/open-state-foundation-logo-small.svg" alt="Open State Foundation Logo" />
                </a>
            </div>
        </div>
    </div>
</header>

{#if showModal}
    <div 
        class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center"
        on:click={handleClickOutside}
    >
        <div 
            bind:this={modalContent}
            class="bg-white rounded-lg p-8 max-w-md w-full mx-4"
        >
            {#if showThankYou}
                <div class="text-center relative">
                    <button 
                        on:click={closeModal}
                        class="absolute -top-4 -right-4 text-gray-500 hover:text-gray-700"
                    >
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                    <h2 class="text-2xl font-bold mb-4">Bedankt voor je feedback!</h2>
                    <p>We waarderen je input.</p>

                    <h3 class="text-lg font-bold mt-4">Contact</h3>
                    <p>Joost van de Loo</p>
                    <p>tel: 06-50733904</p>
                    <p><a href="mailto:joostvandeloo@svdjincubator.nl">joostvandeloo@svdjincubator.nl</a></p>
                </div>
            {:else}
                <div class="flex justify-between items-start mb-4">
                    <h2 class="text-xl font-bold">Feedback</h2>
                    <button 
                        on:click={closeModal}
                        class="text-gray-500 hover:text-gray-700"
                    >
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>
                <form on:submit|preventDefault={handleSubmit} class="space-y-4">
                    <div>
                        <label for="question" class="block text-sm font-medium text-gray-700 mb-1">
                            Wat was je vraag/opmerking? *
                        </label>
                        <textarea
                            id="question"
                            name="question"
                            bind:value={formData.question}
                            required
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                            rows="3"
                        ></textarea>
                    </div>
                    <div>
                        <label for="name" class="block text-sm font-medium text-gray-700 mb-1">
                            Naam
                        </label>
                        <input
                            type="text"
                            id="name"
                            name="name"
                            bind:value={formData.name}
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        />
                    </div>
                    <div>
                        <label for="email" class="block text-sm font-medium text-gray-700 mb-1">
                            E-mail
                        </label>
                        <input
                            type="email"
                            id="email"
                            name="email"
                            bind:value={formData.email}
                            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        />
                    </div>
                    <input 
                        type="hidden"
                        id="session_id" 
                        name="session_id" 
                        bind:value={formData.session_id}
                    />
                    <button
                        type="submit"
                        disabled={isSubmitting}
                        class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
                    >
                        {isSubmitting ? 'Verzenden...' : 'Verstuur feedback'}
                    </button>
                </form>
            {/if}
        </div>
    </div>
{/if} 