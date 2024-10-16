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
		proxy: {
			'/api': {
			  target: 'http://backend:8000',
			  changeOrigin: true,
			  secure: false,
			  // Rewrite the URL if necessary
			  // rewrite: (path) => path.replace(/^\/api/, '')
			},
		},
	},
	css: {
	  postcss: true
	}
});
