import adapter from '@sveltejs/adapter-node';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: adapter({
			out: 'build',
			precompress: false,
			env: {
				prefix: 'APP_'
			}
		})
	}
};

export default config;
