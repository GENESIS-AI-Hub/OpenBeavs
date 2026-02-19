import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	// Consult https://kit.svelte.dev/docs/integrations#preprocessors
	// for more information about preprocessors
	preprocess: vitePreprocess(),
	kit: {
		// Using adapter-node for Cloud Run deployment
		adapter: adapter({
			out: 'build'
		})
	},
	vitePlugin: {
		// inspector: {
		// 	toggleKeyCombo: 'meta-shift', // Key combination to open the inspector
		// 	holdMode: false, // Enable or disable hold mode
		// 	showToggleButton: 'always', // Show toggle button ('always', 'active', 'never')
		// 	toggleButtonPos: 'bottom-right' // Position of the toggle button
		// }
	},
	onwarn: (warning, handler) => {
		const { code } = warning;
		if (code === 'css-unused-selector') return;

		handler(warning);
	}
};

export default config;
