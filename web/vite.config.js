import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	// The vendored partner label map (src/lib/displayLabels.js) lives at the repo root.
	server: { fs: { allow: ['../reference'] } }
});
