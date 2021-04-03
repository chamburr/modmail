<template>
  <div>
    <Heading title="Profile">
      This is your profile information. The page is currently under development.
    </Heading>
    <Card class="bg-dark mb-4" body-classes="d-md-flex">
      <div class="mr-0 mr-md-4 text-center text-md-left">
        <img id="user-icon" class="rounded" :src="$discord.getAvatar(user)" alt="Icon" />
      </div>
      <div class="d-flex flex-column justify-content-center text-center text-md-left mt-3 mt-md-0">
        <p class="h4 font-weight-bold mb-2">{{ $discord.getName(user) }}</p>
        <p class="h6 font-weight-bold mb-0">ID: {{ user.id }}</p>
      </div>
    </Card>
    <p class="text-center mt-5 h4">Nothing to see here... yet!</p>
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

<style scoped>
#user-icon {
  width: 120px;
  height: 120px;
}
</style>
