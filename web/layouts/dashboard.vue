<template>
  <div>
    <TheHeader :dashboard="true" />
    <div
      id="dashboard-container"
      class="d-md-flex flex-nowrap justify-content-center container-fluid px-4 px-md-0"
    >
      <div id="dashboard-sidebar" class="d-none d-md-inline-block px-5">
        <TheSidebar />
      </div>
      <div id="dashboard-content" class="d-md-block py-5 pr-0 pr-md-5 w-100">
        <div v-if="!isOverview" class="d-md-none mb-5">
          <NuxtLink :to="`/dashboard/${$route.params.id}`">
            <BaseButton id="dashboard-back" class="w-100" type="success" size="sm">
              Back to Overview
            </BaseButton>
          </NuxtLink>
        </div>
        <div class="d-flex flex-column h-100">
          <Heading :title="module.name">
            {{ module.description }}
          </Heading>
          <Nuxt v-if="hasPlayer" />
          <div
            v-else
            class="mb-md-5 flex-grow-1 d-flex flex-column align-items-center justify-content-center"
          >
            <p class="h5 mt-4 text-center">The bot is not connected to any channel.</p>
            <BaseButton type="success" size="lg" class="mt-4 mb-md-5" @click="connect">
              <span class="h6 font-weight-bold">Connect</span>
            </BaseButton>
          </div>
        </div>
      </div>
    </div>
    <TheFooter />
  </div>
</template>

<script>
import { mapGetters } from 'vuex'

export default {
  middleware: ['auth', 'module', 'guild'],
  data() {
    return {
      interval: '',
      timeout: '',
    }
  },
  head() {
    return {
      title: this.guild ? this.guild.name : 'Dashboard',
    }
  },
  computed: {
    isOverview() {
      return /^\/dashboard\/\d+\/?$/.test(this.$route.path)
    },
    playing() {
      return this.queue[this.player.playing]
    },
    module() {
      return this.modules.find(element => element.link === this.$route.path)
    },
    hasPlayer() {
      return (
        this.module == null ||
        this.module.player !== 'true' ||
        !this.$store.getters['guild/isPlayerNull']
      )
    },
    ...mapGetters('guild', ['guild', 'player', 'queue']),
    ...mapGetters('user', ['guilds']),
    ...mapGetters(['modules']),
  },
  mounted() {
    const guilds = this.guilds.filter(element => (element.permissions & 20) === 20)
    const joinedGuilds = guilds.filter(element => element.has_bot)

    if (joinedGuilds.length < 5 && joinedGuilds.length * 2 < guilds.length) {
      this.timeout = setTimeout(async () => {
        await this.$modal(
          'Add Wyvor to all of your servers and enjoy the best music experience everywhere!',
          {
            title: 'Enjoying Wyvor?',
            okTitle: 'Invite Now',
            cancelTitle: 'Later',
          }
        ).then(res => {
          if (!res) return
          window.open(this.$router.resolve('/invite').href, '_blank')
        })
      }, 600000)
    } else if (this.guilds.find(element => element.id === process.env.MAIN_GUILD)) {
      this.timeout = setTimeout(async () => {
        await this.$modal(
          'You should check out our official Wyvor server! You will definitely love it too!',
          {
            title: 'Enjoying Wyvor?',
            okTitle: 'Join Now',
            cancelTitle: 'Later',
          }
        ).then(res => {
          if (!res) return
          window.open(this.$router.resolve('/support').href, '_blank')
        })
      }, 600000)
    }

    this.pollUpdates().then()
    this.interval = setInterval(() => {
      if (
        this.player &&
        this.playing &&
        !this.player.paused &&
        this.player.position < this.playing.length
      ) {
        this.$store.commit('guild/incPosition', 500 * this.player.filters.timescale.speed)
      }
    }, 500)
  },
  beforeDestroy() {
    clearInterval(this.interval)
    clearTimeout(this.timeout)
  },
  methods: {
    async pollUpdates() {
      await this.$axios
        .$get(`/guilds/${this.$route.params.id}/polling`, { progress: false })
        .catch(async () => {
          this.$error({ message: 'Failed to retrieve player update.' })
          await new Promise(resolve => setTimeout(resolve, 2000))
        })

      if (!this.$route.params.id) return

      this.pollUpdates().then()

      const player = await this.$axios
        .$get(`/guilds/${this.$route.params.id}/player`)
        .catch(err => {
          if (err.response.status !== 400) this.$error(err)
          else this.$nuxt.refresh()
        })

      this.$store.commit('guild/setPlayer', player || {})

      const queue = await this.$axios.$get(`/guilds/${this.$route.params.id}/queue`).catch(err => {
        if (err.response.status !== 400) this.$error(err)
        else this.$nuxt.refresh()
      })

      this.$store.commit('guild/setQueue', queue || [])
    },
    async connect() {
      await this.$axios
        .$post(`/guilds/${this.$route.params.id}/player`)
        .then(() => this.$toast.success('Connected to your channel.'))
        .catch(this.$error)
    },
  },
}
</script>

<style scoped lang="scss">
#dashboard-back {
  font-size: 0.9em;
}

#dashboard-content {
  min-width: 0;
  flex-shrink: 2;
}

#dashboard-container {
  max-width: map-get($container-max-widths, 'sm');
}

@include media-breakpoint-up(md) {
  #dashboard-container {
    max-width: map-get($container-max-widths, 'xl') + 100px;
  }
}

#dashboard-sidebar {
  min-width: 300px;
}

@include media-breakpoint-up(lg) {
  #dashboard-sidebar {
    min-width: 30%;
  }
}
</style>
