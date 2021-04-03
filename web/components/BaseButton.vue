<template>
  <component
    :is="tag"
    :type="tag === 'button' ? nativeType : ''"
    class="btn"
    :class="[
      { 'btn-block': block },
      { 'rounded-circle': rounded },
      { 'btn-icon-only': iconOnly },
      { 'btn-icon': icon },
      { [`text-${textColor}`]: textColor },
      { [`btn-${type}`]: type && !outline },
      { [`btn-outline-${type}`]: outline },
      { [`btn-${size}`]: size },
    ]"
    @click="handleClick"
  >
    <span v-if="icon && $slots.default" class="btn-inner--icon">
      <slot name="icon">
        <i :class="icon"></i>
      </slot>
    </span>
    <i v-if="!$slots.default" :class="icon"></i>
    <span v-if="icon && $slots.default" class="btn-inner--text">
      <slot>
        {{ text }}
      </slot>
    </span>
    <slot v-if="!icon"></slot>
  </component>
</template>

<script>
export default {
  name: 'BaseButton',
  props: {
    tag: {
      type: String,
      default: 'button',
    },
    type: {
      type: String,
      default: 'default',
    },
    size: {
      type: String,
      default: '',
    },
    textColor: {
      type: String,
      default: '',
    },
    nativeType: {
      type: String,
      default: 'button',
    },
    icon: {
      type: String,
      default: '',
    },
    text: {
      type: String,
      default: '',
    },
    outline: {
      type: Boolean,
      default: false,
    },
    rounded: {
      type: Boolean,
      default: false,
    },
    iconOnly: {
      type: Boolean,
      default: false,
    },
    block: {
      type: Boolean,
      default: false,
    },
  },
  methods: {
    handleClick(event) {
      this.$emit('click', event)
    },
  },
}
</script>
