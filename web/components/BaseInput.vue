<template>
  <div class="form-group" :class="[{ focused: focused }]">
    <slot v-bind="slotData">
      <input
        v-model="value"
        v-bind="$attrs"
        class="form-control bg-dark border-0 text-white"
        type="text"
        aria-describedby="addon-right addon-left"
        v-on="listeners"
      />
    </slot>
  </div>
</template>

<script>
export default {
  name: 'BaseInput',
  inheritAttrs: false,
  data() {
    return {
      focused: false,
      value: '',
    }
  },
  computed: {
    listeners() {
      return {
        ...this.$listeners,
        focus: this.onFocus,
        blur: this.onBlur,
      }
    },
    slotData() {
      return {
        ...this.listeners,
        focused: this.focused,
      }
    },
  },
  watch: {
    value(newValue) {
      this.$emit('input', this.value)
    },
  },
  methods: {
    onFocus(value) {
      this.focused = true
      this.$emit('focus', value)
    },
    onBlur(value) {
      this.focused = false
      this.$emit('blur', value)
    },
  },
}
</script>
