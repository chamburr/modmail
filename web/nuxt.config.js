require('dotenv').config()

function isDevelopment() {
  return process.env.ENVIRONMENT !== 'production'
}

export default {
  server: {
    host: process.env.HTTP_HOST,
    port: process.env.HTTP_PORT,
  },

  head: {
    htmlAttrs: {
      lang: 'en',
    },
    title: 'Wyvor - The Discord Music Bot',
    titleTemplate(titleChunk) {
      return titleChunk === 'Wyvor - The Discord Music Bot' ? titleChunk : `${titleChunk} - Wyvor`
    },
    meta: [
      { charset: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1.0' },
      {
        hid: 'description',
        name: 'description',
        content:
          'The best feature-rich Discord music bot. Take control over your music with an intuitive dashboard, custom effects and more!',
      },
      { name: 'theme-color', content: '#ff4500' },
      { name: 'og:title', content: 'Wyvor - The Discord Music Bot' },
      { name: 'og:type', content: 'website' },
      { name: 'og:url', content: process.env.BASE_URI },
      { name: 'og:image', content: `${process.env.BASE_URI}/icon.png` },
      { name: 'og:site_name', content: 'Wyvor' },
      {
        name: 'og:description',
        content:
          'The best feature-rich Discord music bot. Take control over your music with an intuitive dashboard, custom effects and more!',
      },
      { name: 'twitter:card', content: 'summary' },
      { name: 'twitter:title', content: 'Wyvor - The Discord Music Bot' },
      { name: 'twitter:image', content: `${process.env.BASE_URI}/icon.png` },
      {
        name: 'twitter:description',
        content:
          'The best feature-rich Discord music bot. Take control over your music with an intuitive dashboard, custom effects and more!',
      },
    ],
    link: [
      { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' },
      { rel: 'icon', type: 'image/png', sizes: '32x32', href: 'favicon-32x32.png' },
      { rel: 'icon', type: 'image/png', sizes: '16x16', href: 'favicon-16x16.png' },
      { rel: 'apple-touch-icon', sizes: '180x180', href: '/apple-touch-icon.png' },
      { rel: 'mask-icon', href: '/safari-pinned-tab.svg', color: '#ff4500' },
      { rel: 'manifest', href: '/site.webmanifest' },
      { rel: 'canonical', href: process.env.BASE_URI },
    ],
  },

  build: {
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

  dev: isDevelopment(),

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
    '~/plugins/utils.js',
  ],

  modules: [
    '@nuxt/content',
    '@nuxtjs/axios',
    '@nuxtjs/dotenv',
    '@nuxtjs/proxy',
    '@nuxtjs/sentry',
    'bootstrap-vue/nuxt',
  ],

  buildModules: [
    '@nuxtjs/eslint-module',
    '@nuxtjs/fontawesome',
    '@nuxtjs/google-analytics',
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
    baseURL: `${process.env.BASE_URI}/api`,
    credentials: true,
    headers: {
      'Cache-Control': 'max-age=0',
    },
  },

  proxy: {
    '/api': `http://${process.env.API_HOST}:${process.env.API_PORT}`,
  },

  sentry: {
    disabled: isDevelopment(),
    dsn: process.env.SENTRY_DSN,
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
      solid: [
        'faCircle',
        'faClipboardList',
        'faCog',
        'faCompactDisc',
        'faGlobe',
        'faListUl',
        'faMagic',
        'faPause',
        'faPlay',
        'faSearch',
        'faServer',
        'faSignOutAlt',
        'faSlidersH',
        'faStepBackward',
        'faStepForward',
        'faStream',
        'faUserCircle',
      ],
      brands: ['faGithub', 'faLinkedin', 'faReddit', 'faTwitter'],
    },
  },

  googleAnalytics: {
    dev: isDevelopment(),
    id: process.env.GOOGLE_ANALYTICS,
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
    whitelist: ['arrow', 'big', 'collapsing', 'show', 'small'],
    whitelistPatterns: [
      /^[-_]*nuxt[-_]*/,
      /^(?:alert|badge|bg|btn|dropdown|icon|nav|shadow|slider|text)-*/,
      /^(?:b-tooltip|modal|popover|tooltip|bs-tooltip|b-toast|toast)-*/,
      /^(?:noUi|range-slider|input-slider)-*/,
      /^multiselect[-_]*/,
    ],
    whitelistPatternsChildren: [
      /^[-_]*nuxt[-_]*/,
      /^(?:alert|badge|bg|btn|dropdown|icon|nav|shadow|slider|text)-*/,
      /^(?:b-tooltip|modal|popover|tooltip|bs-tooltip|b-toast|toast)-*/,
      /^(?:noUi|range-slider|input-slider)-*/,
      /^multiselect[-_]*/,
    ],
  },
}
