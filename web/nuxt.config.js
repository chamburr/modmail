require('dotenv').config({ path: '../.env' })

export default {
  server: {
    host: process.env.HTTP_HOST,
    port: process.env.HTTP_PORT,
  },

  head: {
    htmlAttrs: {
      lang: 'en',
    },
    title: 'ModMail',
    titleTemplate(titleChunk) {
      return titleChunk === 'ModMail' ? titleChunk : `${titleChunk} - ModMail`
    },
    meta: [
      { charset: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1.0' },
      {
        hid: 'description',
        name: 'description',
        content:
          'A feature-rich Discord bot for easy communication between server staff and users.',
      },
      { name: 'theme-color', content: '#1e90ff' },
      { name: 'og:title', content: 'ModMail' },
      { name: 'og:type', content: 'website' },
      { name: 'og:url', content: 'https://modmail.xyz' },
      { name: 'og:image', content: 'https://modmail.xyz/icon.png' },
      { name: 'og:site_name', content: 'ModMail' },
      {
        name: 'og:description',
        content:
          'A feature-rich Discord bot for easy communication between server staff and users.',
      },
      { name: 'twitter:card', content: 'summary' },
      { name: 'twitter:title', content: 'ModMail' },
      { name: 'twitter:image', content: 'https://modmail.xyz/icon.png' },
      {
        name: 'twitter:description',
        content:
          'A feature-rich Discord bot for easy communication between server staff and users.',
      },
    ],
    link: [
      { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
      { rel: 'icon', type: 'image/png', sizes: '32x32', href: 'favicon-32x32.png' },
      { rel: 'icon', type: 'image/png', sizes: '16x16', href: 'favicon-16x16.png' },
      { rel: 'apple-touch-icon', sizes: '180x180', href: '/apple-touch-icon.png' },
      { rel: 'mask-icon', href: '/safari-pinned-tab.svg', color: '#ff4500' },
      { rel: 'manifest', href: '/site.webmanifest' },
      { rel: 'canonical', href: 'https://modmail.xyz' },
    ],
  },

  build: {
    postcss: process.env.NODE_ENV === 'production' ? {} : null,
    optimizeCSS: true,
    babel: {
      compact: true,
    },
    extend(config, { isClient }) {
      if (isClient) {
        config.devtool = 'source-map'
      }
    },
  },

  components: true,

  dev: process.env.NODE_ENV !== 'production',

  loading: {
    color: 'dodgerblue',
  },

  css: ['~/assets/scss/styles.scss'],

  plugins: [
    '~/plugins/toast.js',
    '~/plugins/error.js',
    '~/plugins/axios.js',
    '~/plugins/click-outside.js',
    '~/plugins/content.js',
    '~/plugins/modal.js',
  ],

  modules: ['@nuxt/content', '@nuxtjs/axios', '@nuxtjs/proxy', 'bootstrap-vue/nuxt'],

  buildModules: [
    '@nuxtjs/eslint-module',
    '@nuxtjs/fontawesome',
    '@nuxtjs/pwa',
    '@nuxtjs/stylelint-module',
    '@nuxtjs/style-resources',
    'nuxt-purgecss',
  ],

  content: {
    markdown: {
      remarkPlugins() {
        return []
      },
    },
  },

  axios: {
    baseURL: '/api',
    credentials: true,
    headers: {
      'Cache-Control': 'max-age=0',
    },
  },

  publicRuntimeConfig: {
    axios: {
      baseURL: `${process.env.BASE_URI}/api`,
    },
  },

  proxy: {
    '/api': `http://${process.env.API_HOST}:${process.env.API_PORT}`,
  },

  bootstrapVue: {
    css: false,
    componentPlugins: ['CollapsePlugin', 'ToastPlugin', 'ModalPlugin'],
    directivePlugins: ['VBPopoverPlugin', 'VBTooltipPlugin'],
  },

  eslint: {
    fix: true,
  },

  fontawesome: {
    useLayers: false,
    useLayersText: false,
    icons: {
      solid: ['faCircle', 'faGlobe'],
      brands: ['faGithub', 'faLinkedin', 'faReddit', 'faTwitter'],
    },
  },

  pwa: {
    icon: false,
    meta: false,
    manifest: false,
    workbox: {
      clientsClaim: false,
      preCaching: ['/'],
    },
  },

  styleResources: {
    scss: [
      '~/node_modules/bootstrap/scss/_functions.scss',
      '~/node_modules/bootstrap/scss/mixins/*.scss',
      '~/assets/scss/argon/_functions.scss',
      '~/assets/scss/argon/mixins/*.scss',
      '~/assets/scss/argon/_variables.scss',
    ],
  },

  purgeCSS: {
    mode: 'postcss',
    fontFace: true,
    keyframes: true,
    variables: true,
    whitelist: ['arrow', 'big', 'close', 'collapsing', 'show', 'small'],
    whitelistPatterns: [
      /^[-_]*nuxt[-_]*/,
      /^(?:alert|badge|bg|btn|dropdown|icon|nav|shadow|slider|text)-*/,
      /^(?:b-tooltip|modal|popover|tooltip|bs-tooltip|b-toast|toast)-*/,
      /^log-*/,
    ],
    whitelistPatternsChildren: [
      /^[-_]*nuxt[-_]*/,
      /^(?:alert|badge|bg|btn|dropdown|icon|nav|shadow|slider|text)-*/,
      /^(?:b-tooltip|modal|popover|tooltip|bs-tooltip|b-toast|toast)-*/,
    ],
  },
}
