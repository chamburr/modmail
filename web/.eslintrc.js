module.exports = {
  root: true,
  env: {
    browser: true,
    node: true,
  },
  parserOptions: {
    parser: '@babel/eslint-parser',
    requireConfigFile: false,
    ecmaVersion: 2020,
  },
  extends: ['@nuxtjs', 'prettier', 'plugin:prettier/recommended', 'plugin:nuxt/recommended'],
  plugins: ['prettier'],
  rules: {
    'vue/require-prop-types': 0,
    'vue/multi-word-component-names': 0,
  },
}
