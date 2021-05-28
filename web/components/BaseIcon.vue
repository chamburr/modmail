<template>
  <div class="icon icon-shape" :class="[{ [`text-${color}`]: color }]" v-on="$listeners">
    <slot>
      <FontAwesomeIcon v-if="name !== ''" :icon="realName" class="icon-fa" />
    </slot>
  </div>
</template>

<script>
export default {
  name: 'BaseIcon',
  props: {
    name: {
      type: String,
      default: '',
    },
    color: {
      type: String,
      default: 'white',
    },
  },
  computed: {
    realName() {
      return this.name.split(' ')
    },
  },
}
</script>

<style scoped>
.icon {
  display: inline-block !important;
  height: 100%;
  width: 2rem;
  vertical-align: text-bottom;
}

.icon-fa {
  height: 1em;
  width: 1em;
  vertical-align: middle;
}

.small .icon-fa {
  height: 0.8em;
  width: 0.8em;
}

.big .icon-fa {
  height: 1.2em;
  width: 1.2em;
}
</style>
