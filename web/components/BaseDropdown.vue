<template>
  <component
    :is="tag"
    v-click-outside="closeDropDown"
    class="dropdown"
    :class="[{ show: isOpen }, { dropdown: direction === 'down' }, { dropup: direction === 'up' }]"
    aria-haspopup="true"
    :aria-expanded="isOpen"
    @click="toggleDropDown"
  >
    <slot name="title">
      <a class="dropdown-toggle nav-link" data-toggle="dropdown">
        <i :class="icon"></i>
        <span class="no-icon">{{ title }}</span>
      </a>
    </slot>
    <ul
      class="dropdown-menu"
      :class="[{ 'dropdown-menu-right': position === 'right' }, { show: isOpen }, menuClasses]"
    >
      <slot></slot>
    </ul>
  </component>
</template>

<script>
export default {
  name: 'BaseDropdown',
  props: {
    direction: {
      type: String,
      default: 'down',
    },
    title: {
      type: String,
      default: '',
    },
    icon: {
      type: String,
      default: '',
    },
    position: {
      type: String,
      default: '',
    },
    menuClasses: {
      type: [String, Object],
      default: '',
    },
    tag: {
      type: String,
      default: 'li',
    },
  },
  data() {
    return {
      isOpen: false,
    }
  },
  methods: {
    toggleDropDown() {
      this.isOpen = !this.isOpen
      this.$emit('change', this.isOpen)
    },
    closeDropDown() {
      this.isOpen = false
      this.$emit('change', this.isOpen)
    },
  },
}
</script>

<style scoped>
.dropdown {
  list-style-type: none;
}

.dropdown .dropdown-toggle {
  cursor: pointer;
}
</style>
