// https://nuxt.com/docs/api/configuration/nuxt-config
import tailwindcss from "@tailwindcss/vite";

export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  modules: ['@nuxt/ui'],
  vite: {
    plugins: [
      tailwindcss(),
    ],
  },
  devServer: {
    host: '192.168.80.101',
    port: 3000
  }
})
