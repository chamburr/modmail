<template>
  <SlideYUpTransition :duration="animationDuration">
    <div
      v-show="show"
      class="modal fade"
      :class="[{ 'show d-block': show }, { 'd-none': !show }, { 'modal-mini': type === 'mini' }]"
      tabindex="-1"
      role="dialog"
      :aria-hidden="!show"
      @click.self="closeModal"
    >
      <div
        class="modal-dialog modal-dialog-centered"
        :class="[{ 'modal-notice': type === 'notice' }, modalClasses]"
      >
        <div class="modal-content" :class="modalContentClasses">
          <div v-if="$slots.header" class="modal-header" :class="[headerClasses]">
            <slot name="header"></slot>
            <slot name="close-button">
              <button
                v-if="showClose"
                type="button"
                class="close"
                data-dismiss="modal"
                aria-label="Close"
                @click="closeModal"
              >
                <span :aria-hidden="!show">×</span>
              </button>
            </slot>
          </div>
          <div class="modal-body" :class="bodyClasses">
            <slot></slot>
          </div>
          <div v-if="$slots.footer" class="modal-footer" :class="footerClasses">
            <slot name="footer"></slot>
          </div>
        </div>
      </div>
    </div>
  </SlideYUpTransition>
</template>

<script>
import { SlideYUpTransition } from 'vue2-transitions'

export default {
  name: 'Modal',
  components: [SlideYUpTransition],
  props: {
    show: {
      type: Boolean,
      default: true,
    },
    showClose: {
      type: Boolean,
      default: true,
    },
    type: {
      type: String,
      default: '',
      validator(value) {
        return ['', 'notice', 'mini'].includes(value)
      },
    },
    modalClasses: {
      type: [Object, String],
      default: '',
    },
    modalContentClasses: {
      type: [Object, String],
      default: '',
    },
    headerClasses: {
      type: [Object, String],
      default: '',
    },
    bodyClasses: {
      type: [Object, String],
      default: '',
    },
    footerClasses: {
      type: [Object, String],
      default: '',
    },
    animationDuration: {
      type: Number,
      default: 500,
    },
  },
  watch: {
    show(value) {
      const documentClasses = document.body.classList
      if (value) {
        documentClasses.add('modal-open')
      } else {
        documentClasses.remove('modal-open')
      }
    },
  },
  methods: {
    closeModal() {
      this.$emit('update:show', false)
      this.$emit('close')
    },
  },
}
</script>

<style scoped>
.modal.show {
  background-color: rgba(0, 0, 0, 0.3);
}
</style>
