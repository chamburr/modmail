<template>
  <FadeTransition>
    <div
      v-if="visible"
      class="alert"
      :class="[`alert-${type}`, { 'alert-dismissible': dismissible }]"
      role="alert"
    >
      <slot v-if="!dismissible">
        <span v-if="icon" class="alert-inner--icon">
          <i :class="icon"></i>
        </span>
        <span v-if="$slots.text" class="alert-inner--text">
          <slot name="text"></slot>
        </span>
      </slot>
      <template v-else>
        <slot>
          <span v-if="icon" class="alert-inner--icon">
            <i :class="icon"></i>
          </span>
          <span v-if="$slots.text" class="alert-inner--text">
            <slot name="text"></slot>
          </span>
        </slot>
        <button
          type="button"
          data-dismiss="alert"
          aria-label="Close"
          class="close"
          @click="dismissAlert"
        >
          <span aria-hidden="true">×</span>
        </button>
      </template>
    </div>
  </FadeTransition>
</template>

<script>
import { FadeTransition } from 'vue2-transitions'

export default {
  name: 'BaseAlert',
  components: [FadeTransition],
  props: {
    type: {
      type: String,
      default: 'default',
    },
    icon: {
      type: String,
      default: '',
    },
    dismissible: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      visible: true,
    }
  },
  methods: {
    dismissAlert() {
      this.visible = false
    },
  },
}
</script>
