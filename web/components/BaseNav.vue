<template>
  <nav class="navbar navbar-dark navbar-expand-lg" :class="[{ [`bg-${type}`]: type }]">
    <div class="container">
      <slot name="brand"></slot>
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
        v-click-outside="closeMenu"
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
