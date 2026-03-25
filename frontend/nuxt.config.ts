export default defineNuxtConfig({
  compatibilityDate: "2025-07-15",
  devtools: { enabled: true },
  ssr: false,
  app: {
    head: {
      title: "서초구청 AI 계약서류 검토시스템",
      link: [
        { rel: "stylesheet", href: "/css/reset.css" },
        { rel: "stylesheet", href: "/css/common.css" },
        { rel: "stylesheet", href: "/css/layout.css" },
        { rel: "stylesheet", href: "/css/login.css" },
        { rel: "stylesheet", href: "/font/pretendard.css" },
      ],
    },
  },
  vite: {
    optimizeDeps: {
      include: ["@vue/devtools-core", "@vue/devtools-kit"],
    },
  },
});
