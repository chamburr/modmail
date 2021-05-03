<template>
  <div class="card bg-dark shadow">
    <div v-if="$slots.header" class="card-header bg-transparent p-0" :class="headerClasses">
      <slot name="header"></slot>
    </div>
    <div class="card-body" :class="bodyClasses">
      <slot></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Card',
  props: {
    bodyClasses: {
      type: String,
      default: '',
    },
    headerClasses: {
      type: String,
      default: '',
    },
  },
}
</script>
