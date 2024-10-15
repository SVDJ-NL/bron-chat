import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		watch: {
		  usePolling: true,
		  interval: 1000,
		},
		host: true, // This allows the server to be accessible externally
		port: 5173,
	},
	css: {
	  postcss: true
	}
});
