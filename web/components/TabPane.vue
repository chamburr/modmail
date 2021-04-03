<template>
  <div v-show="active" :id="title" class="tab-pane" :class="{ active: active }">
    <slot></slot>
  </div>
</template>

<script>
export default {
  name: 'TabPane',
  inject: ['addTab', 'removeTab'],
  props: {
    title: {
      type: String,
      default: '',
    },
  },
  data() {
    return {
      active: false,
    }
  },
  mounted() {
    this.addTab(this)
  },
  destroyed() {
    if (this.$el && this.$el.parentNode) {
      this.$el.parentNode.removeChild(this.$el)
    }
    this.removeTab(this)
  },
}
</script>
