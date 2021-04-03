<template>
  <div
    class="card"
    :class="[
      { 'card-lift--hover': hover },
      { [`shadow-${shadowSize}`]: shadowSize },
      { [`bg-${type}`]: type },
      { shadow: shadow },
    ]"
  >
    <div v-if="$slots.header" class="card-header" :class="headerClasses">
      <slot name="header"></slot>
    </div>
    <div class="card-body" :class="bodyClasses">
      <slot></slot>
    </div>
    <div v-if="$slots.footer" class="card-footer" :class="footerClasses">
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Card',
  props: {
    type: {
      type: String,
      default: '',
    },
    hover: {
      type: Boolean,
      default: false,
    },
    shadow: {
      type: Boolean,
      default: true,
    },
    shadowSize: {
      type: String,
      default: '',
    },
    bodyClasses: {
      type: [String, Object],
      default: '',
    },
    headerClasses: {
      type: [String, Object],
      default: '',
    },
    footerClasses: {
      type: [String, Object],
      default: '',
    },
  },
}
</script>
