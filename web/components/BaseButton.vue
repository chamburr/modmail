<template>
  <button
    class="btn"
    :class="[{ [`btn-${type}`]: type }, { [`btn-${size}`]: size }]"
    @click="handleClick"
  >
    <slot></slot>
  </button>
</template>

<script>
export default {
  name: 'BaseButton',
  props: {
    type: {
      type: String,
      default: 'default',
    },
    size: {
      type: String,
      default: '',
    },
  },
  methods: {
    handleClick(event) {
      this.$emit('click', event)
    },
  },
}
</script>
