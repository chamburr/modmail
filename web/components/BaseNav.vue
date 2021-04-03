<template>
  <nav
    class="navbar navbar-dark"
    :class="[
      { 'navbar-expand-lg': expand },
      { 'navbar-transparent': transparent },
      { [`bg-${type}`]: type },
      { rounded: round },
    ]"
  >
    <div class="container">
      <slot name="container-pre"></slot>
      <slot name="brand">
        <a class="navbar-brand" href="#" @click.prevent="onTitleClick">
          {{ title }}
        </a>
      </slot>
      <button
        class="navbar-toggler"
        type="button"
        data-toggle="collapse"
        :data-target="id"
        :aria-controls="id"
        :aria-expanded="toggled"
        aria-label="Toggle navigation"
        @click.stop="toggled = !toggled"
      >
        <span class="navbar-toggler-icon"></span>
      </button>
      <slot name="container-after"></slot>
      <div
        :id="id"
        v-click-outside-2="closeMenu"
        class="collapse navbar-collapse"
        :class="{ show: toggled }"
      >
        <slot :close-menu="closeMenu"></slot>
      </div>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'BaseNav',
  props: {
    type: {
      type: String,
      default: 'primary',
    },
    title: {
      type: String,
      default: '',
    },
    round: {
      type: Boolean,
      default: false,
    },
    transparent: {
      type: Boolean,
      default: false,
    },
    expand: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      id: '',
      toggled: false,
    }
  },
  mounted() {
    this.id = Math.random().toString()
  },
  methods: {
    onTitleClick(event) {
      this.$emit('title-click', event)
    },
    closeMenu() {
      this.toggled = false
    },
  },
}
</script>
