<template>
  <div class="alert" :class="[`alert-${type}`]" role="alert">
    <span class="alert-inner--text">
      <slot></slot>
    </span>
  </div>
</template>

<script>
export default {
  name: 'BaseAlert',
  props: {
    type: {
      type: String,
      default: 'default',
    },
  },
}
</script>
