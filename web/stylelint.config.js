module.exports = {
  customSyntax: 'postcss-html',
  extends: [
    'stylelint-config-standard',
    'stylelint-config-prettier',
    'stylelint-config-recommended-scss',
  ],
  ignoreFiles: ['**/node_modules/**', 'assets/scss/argon/**'],
  rules: {
    'scss/no-global-function-names': null,
    'shorthand-property-no-redundant-values': null,
    'selector-pseudo-element-no-unknown': [
      true,
      {
        ignorePseudoElements: ['v-deep'],
      },
    ],
  },
}
