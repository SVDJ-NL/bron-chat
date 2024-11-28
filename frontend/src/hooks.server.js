/** @type {import('@sveltejs/kit').Handle} */
export async function handle({ event, resolve }) {
    const response = await resolve(event);
    
    if (response.headers.get('content-type')?.includes('text/html')) {
        let html = await response.text();
        
        if (process.env.NODE_ENV === 'production') {
            const host = event.url.host;
            
            html = html.replace(
                '</head>',
                `<script defer data-domain="${host}" src="https://plausible.io/js/script.js"></script></head>`
            );
        }
        
        return new Response(html, {
            status: response.status,
            headers: response.headers
        });
    }
    
    return response;
} 