<template>
  <div class="form-group" :class="[{ focused: focused }]">
    <slot v-bind="slotData">
      <input
        v-model="realValue"
        v-bind="$attrs"
        class="form-control"
        :class="inputClasses"
        :type="type"
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
  props: {
    required: {
      type: Boolean,
      default: false,
    },
    inputClasses: {
      type: String,
      default: 'bg-dark border-0 text-white',
    },
    type: {
      type: String,
      default: 'text',
    },
    value: {
      default: '',
    },
  },
  data() {
    return {
      focused: false,
      realValue: this.value,
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
      if (typeof newValue === 'string' || typeof newValue === 'number') {
        this.realValue = newValue
      }
    },
    realValue(newValue) {
      if (this.type === 'number') {
        if (typeof newValue === 'string' && newValue.startsWith('0')) {
          while (newValue.charAt(0) === '0') {
            newValue = newValue.substring(1)
          }
          newValue = parseInt(newValue, 10) || ''
        }
        if (this.required && newValue === '') {
          newValue = 0
        }
      }
      this.realValue = newValue
      this.$emit('input', this.realValue)
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
