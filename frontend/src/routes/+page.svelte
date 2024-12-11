<script>
    import { goto } from '$app/navigation';
    import { API_BASE_URL } from '$lib/config';
    import ChatInput from '$lib/components/ChatInput.svelte';
    import Typed from 'typed.js';
    import { onMount, onDestroy } from 'svelte';
	import SearchInput from '../lib/components/SearchInput.svelte';

    let query = '';
    let isLoading = false;
    let error = null;
    let showAboutDialog = false;

    let samplePrompts = [
        "Stikstofbeleid 2023",
        "Uitgaven klimaatbeleid",
        "Toeslagenaffaire",
        "Aanpak cybercriminaliteit",
        "Windenergie op zee",
        "Stand van zaken woningmarkt",
        "Coronasteun bedrijven",
        "Problemen jeugdzorg",
        "Rapport drugscriminaliteit",
        "Personeelstekort onderwijs"
    ];
    
    let displayedPrompts = [];
    
    function getRandomPrompts() {
        let shuffled = [...samplePrompts].sort(() => 0.5 - Math.random());
        displayedPrompts = shuffled.slice(0, 3);
    }
    
    function handlePromptClick(value) {
        const urlSearchParams = new URLSearchParams({
            query: value.trim(),
        });
        handleSearch({ detail: urlSearchParams });
    }
    
    async function handleSearch(event) {        
        console.debug('page handleSearch', event);
        isLoading = true;
        error = null;

        try {
            // First create a new session
            const sessionResponse = await fetch(`${API_BASE_URL}/new_session`, {
                method: 'POST',
            });

            if (!sessionResponse.ok) {
                console.error('Failed to create new session', sessionResponse);
                throw new Error('Failed to create new session');
            }

            const sessionData = await sessionResponse.json();
            const sessionId = sessionData.id;

            // Navigate to the session page
            await goto(`/s/${sessionId}`);

            event.detail.urlSearchParams.append('session_id', sessionId);

            // Get the URLSearchParams from the event detail
            const urlSearchParams = event.detail.urlSearchParams;

            // Dispatch the event with the search parameters
            window.dispatchEvent(new CustomEvent('initialQuery', {
                detail: urlSearchParams
            }));

        } catch (err) {
            console.error('Error:', err);
            isLoading = false;
            error = 'Er is een fout opgetreden bij het verwerken van uw vraag.';
        }
    }

    function handleEscape(event) {
        if (event.key === 'Escape' && showAboutDialog) {
            showAboutDialog = false;
        }
    }

    onMount(() => {
        window.addEventListener('keydown', handleEscape);
        const typedTitle = new Typed('#typed-title', {
            strings: ["Vraag alles over 3.5 miljoen open overheidsdocumenten"],
            typeSpeed: 50,
            showCursor: false,
        });

        getRandomPrompts();

        return () => {
            typedTitle.destroy();
        };
    });

    onDestroy(() => {
        window.removeEventListener('keydown', handleEscape);
    });


    function handleClickOutside(event) {
        if (event.target === event.currentTarget) {
            closeModal();
        }
    }

    function closeModal() {
        showAboutDialog = false;
    }

</script>

<div class="min-h-screen flex flex-col items-center justify-center bg-gray-100">
    <div class="w-full max-w-2xl text-center mb-4">
        <h1 class="text-xl sm:text-3xl font-bold mb-2 sm:mb-4">
            Welkom bij Bron chat            
        </h1>
        <h2 id="typed-title" class="text-gray-600 text-lg lg:text-xl"></h2>
    </div>

    <div class="w-full max-w-2xl">
        <SearchInput
            bind:value={query}
            {isLoading}
            on:submit={handleSearch}
        />
    </div>

    <div class="w-full max-w-2xl mt-4 flex flex-wrap gap-2 justify-center">
        {#each displayedPrompts as prompt}
            <button
                on:click={() => handlePromptClick(prompt)}
                class="text-sm text-gray-600 bg-white px-3 py-1.5 rounded-full border border-gray-300 hover:bg-gray-50 hover:border-gray-400 transition-colors"
            >
                {prompt}
            </button>
        {/each}
    </div>

    <div class="w-full max-w-2xl text-center mt-4 md:mt-6">
        <button
                on:click={() => showAboutDialog = true}
                class="ml-2 text-sm font-normal text-blue-600 hover:underline flex items-center w-full justify-center flex-wrap flex-col"
            >           
            <span>
                Over Bron chat
            </span>
        </button>
    </div>

    {#if error}
        <div class="mt-4 text-red-500">
            {error}
        </div>
    {/if}

    {#if showAboutDialog}
        <div 
            class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
            on:click={handleClickOutside}
        >
            <div class="bg-white rounded-lg p-6 max-w-2xl max-h-[90vh] overflow-y-auto">
                <div class="flex justify-between items-start mb-4">
                    <h2 class="text-xl font-bold">Over Bron chat</h2>
                    <button
                        on:click={() => showAboutDialog = false}
                        class="text-gray-500 hover:text-gray-700"
                    >
                        ✕
                    </button>
                </div>
                
                <div class="space-y-4">
                    <p>Bron chat is een tool voor journalisten en onderzoekers, ontwikkeld door SVDJ Incubator in samenwerking met Open State Foundation. Onze missie: alle openbare overheidsinformatie makkelijk en snel doorzoekbaar maken doormiddel van een AI chat. Dagelijks werken wij aan het uitbreiden en verbeteren van Bron chat.</p>
                    
                    <div>
                        <h3 class="font-bold mb-2">Wat Bron chat biedt:</h3>
                        <ul class="list-disc pl-5 space-y-1">
                            <li><strong>Toegang tot miljoenen documenten:</strong> Doorzoek 3,5 miljoen overheidsdocumenten op één centrale plek.</li>
                            <li><strong>Gebruiksvriendelijke bronverwijzingen:</strong> Directe links naar originele documenten en downloadbare pdf's.</li>
                            <li><strong>Samenwerking:</strong> Deel jouw zoekresultaten eenvoudig met collega's via doorstuurbare links.</li>
                            <li><strong>Nieuwe inzichten dankzij AI:</strong> Ontdek verbanden en patronen in overheidsdata.</li>
                            <li><strong>Transparante data:</strong> Ontsloten door Open State Foundation, een onafhankelijke stichting zonder winstoogmerk.</li>
                            <li><strong>Speciaal voor journalisten en onderzoekers:</strong> Een betrouwbare, flexibele tool ontwikkeld door SVDJ Incubator, onderdeel van het Stimuleringsfonds voor de Journalistiek.</li>
                        </ul>
                    </div>

                    <div class="mt-4 text-center">
                        <p class="font-bold">
                            Wil je een verhaal maken met behulp van Bron chat, <br>   
                            of heb je meer vragen over deze tool?
                        </p>
                        <p>Neem dan contact met ons op. Alle feedback is welkom!</p>
                        <p class="mt-2">Joost van de Loo<br>
                        tel: 06-50733904<br>
                        <a href="mailto:joostvandeloo@svdjincubator.nl" class="text-blue-600 hover:underline">joostvandeloo@svdjincubator.nl</a></p>
                    </div>
                </div>
            </div>
        </div>
    {/if}
</div>
