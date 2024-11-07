<script>
    import { page } from '$app/stores';
</script>

<header class="fixed w-full top-0 z-10">
    <div class="px-4 sm:px-6 lg:px-8">
        <div class="flex h-16">
            <div class="flex-shrink-0 flex items-center">
                <a href="https://chat.bron.live">
                    <img class="hidden sm:block h-8 w-auto ml-1" src="/bron-logo.svg" alt="Bron Logo" />
                    <img class="block sm:hidden h-6 w-auto ml-0.5" src="/bron-logo.svg" alt="Bron Logo" />
                </a>
                <a href="https://chat.bron.live" target="_blank" class="ml-2 mt-1">
                    <span class="text-[#2260FF] text-2xl md:text-3xl font-semibold uppercase">Chat</span>
                    <svg xmlns="http://www.w3.org/2000/svg" class="inline-block h-4 w-4 mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                </a>
            </div>
            <div class="flex-shrink-0 flex items-center ml-auto">
                <a href="https://svdj.nl" target="_blank">
                    <img class="hidden sm:block h-7 md:h-12 w-auto" src="/incubator.png" alt="SvdJ Incubator Logo" />
                    <img class="block sm:hidden h-6 md:h-10 w-auto" src="/incubator.png" alt="SvdJ Incubator Logo" />
                </a>
                <a href="https://openstate.eu" target="_blank">
                    <img class="hidden sm:block h-7 md:h-11 w-auto" src="/open-state-foundation-logo.svg" alt="Open State Foundation Logo" />
                    <img class="block sm:hidden h-6 md:h-9 w-auto" src="/open-state-foundation-logo.svg" alt="Open State Foundation Logo" />
                </a>
            </div>
        </div>
    </div>
</header> 