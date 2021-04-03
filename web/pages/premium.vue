<template>
  <div>
    <Heading title="Redirecting..." />
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  layout: 'auth',
  head: {
    title: 'Profile',
  },
  computed: {
    ...mapGetters('user', ['user']),
  },
}
</script>
