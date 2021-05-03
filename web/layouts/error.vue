<template>
  <div class="text-center">
    <div class="display-1 mb-4">:(</div>
    <Heading :title="errorName">
      {{ errorDescription }}
    </Heading>
    <div class="d-flex justify-content-center mt-4">
      <BaseButton
        v-if="error.statusCode < 500"
        type="primary"
        size="lg"
        class="mx-3"
        @click="goBack"
      >
        <span class="h6 font-weight-bold">Back</span>
      </BaseButton>
      <BaseButton v-else type="primary" size="lg" class="mx-3" @click="refresh">
        <span class="h6 font-weight-bold">Refresh</span>
      </BaseButton>
      <a class="d-block" target="_blank" href="/support">
        <BaseButton type="primary" size="lg" class="mx-3">
          <span class="h6 font-weight-bold">Support Server</span>
        </BaseButton>
      </a>
    </div>
  </div>
</template>

<script>
export default {
  props: ['error'],
  computed: {
    errorName() {
      if (this.$nuxt.isOffline) {
        return 'Unable to Connect'
      } else if (this.error.statusCode === 400) {
        return 'Bad Request'
      } else if (this.error.statusCode === 401) {
        return 'Unauthorized'
      } else if (this.error.statusCode === 403) {
        return 'Forbidden'
      } else if (this.error.statusCode === 404) {
        return 'Page Not Found'
      } else if (this.error.statusCode === 500) {
        return 'Internal Server Error'
      } else if (this.error.statusCode === 503) {
        return 'Service Unavailable'
      } else {
        return 'An Error Occurred'
      }
    },
    errorDescription() {
      if (this.$nuxt.isOffline) {
        return 'You are not connected to the internet.'
      } else if (this.error.statusCode === 400) {
        return 'The request you made is invalid.'
      } else if (this.error.statusCode === 401) {
        return 'You are not authorised to access this page.'
      } else if (this.error.statusCode === 403) {
        return 'You do not have permission to access this page.'
      } else if (this.error.statusCode === 404) {
        return 'The page you are looking for does not exist.'
      } else if (this.error.statusCode === 500) {
        return 'The server encountered an internal error.'
      } else if (this.error.statusCode === 503) {
        return 'The server cannot handle your request at this time.'
      } else if (this.error.message) {
        return this.error.message
      } else {
        return 'An unknown error occurred.'
      }
    },
  },
  methods: {
    goBack() {
      this.$router.go(-1)
    },
    refresh() {
      window.location.reload(true)
    },
  },
}
</script>
