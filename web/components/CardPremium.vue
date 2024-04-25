<template>
  <Card header-classes="card-premium-header pt-3 pb-0">
    <template v-if="popular" #header>
      <span class="card-premium-recommended text-uppercase font-weight-bolder">Recommended</span>
    </template>
    <p class="card-title h3 mb-4 pb-2">{{ name }}</p>
    <p class="card-subtitle h6 mb-3">Premium for {{ server }} server{{ server > 1 ? 's' : '' }}</p>
    <div
      class="d-inline-block border rounded-pill font-weight-500 pl-1 pr-2 mb-4 small"
      :style="`border-color: ${color} !important`"
    >
      <div
        class="d-inline-block align-middle card-premium-role"
        :style="{ 'background-color': color }"
      />
      {{ role }}
    </div>
    <p class="h1 text-info">${{ price }}</p>
    <p class="text-muted mb-4">${{ pricePerServer }} per server</p>
    <BaseButton
      :type="popular ? 'success' : 'gray'"
      class="btn-block btn-sm mb-2"
      v-on="$listeners"
    >
      Purchase Now
    </BaseButton>
    <small class="text-muted">One-time Purchase</small>
  </Card>
</template>

<script>
export default {
  name: 'CardPremium',
  props: {
    name: {
      type: String,
      default: '',
    },
    role: {
      type: String,
      default: '',
    },
    color: {
      type: String,
      default: '#000',
    },
    price: {
      type: Number,
      default: 0,
    },
    server: {
      type: Number,
      default: 0,
    },
    popular: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    pricePerServer() {
      return this.price / this.server
    },
  },
}
</script>

<style scoped lang="scss">
.card-premium-role {
  height: 0.8rem;
  width: 0.8rem;
  margin: 1px 0 3px 0;
  border-radius: 50%;
}

.card-premium-recommended {
  color: #ffd700 !important;
}
</style>
