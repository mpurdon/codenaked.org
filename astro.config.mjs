import { defineConfig } from 'astro/config';

// https://astro.build/config
export default defineConfig({
  site: 'https://codenaked.org',
  outDir: './dist', // wrangler pages deploy dist
  srcDir: './src',
  // Inline the small stylesheet into each page's <head> so first paint needs
  // only the HTML document — same approach as matthewpurdon.me.
  build: {
    inlineStylesheets: 'always',
  },
});
