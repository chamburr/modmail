<template>
  <div>
    <Heading title="Status">
      The bot status information. This page automatically refreshes every 30 seconds.
    </Heading>
    <BaseAlert v-if="connectedPercent === 100" type="success" class="status-alert">
      <span class="font-weight-bold h6">All services are fully operational.</span>
    </BaseAlert>
    <BaseAlert v-else-if="connectedPercent >= 50" type="warning" class="status-alert">
      <span class="font-weight-bold h6">Some services are experiencing issues.</span>
    </BaseAlert>
    <BaseAlert v-else type="danger" class="status-alert">
      <span class="font-weight-bold h6">Some services are experiencing major issues.</span>
    </BaseAlert>
    <p class="mt-5 h4">Overview</p>
    <p>
      Shards: {{ stats.shards }}
      <br />
      Servers: {{ stats.guilds }}
      <br />
      Uptime: {{ durationSince(stats.started) }}
    </p>
    <p class="mt-4 h4">Legend</p>
    <div class="status-legend d-flex align-items-center">
      <BaseIcon name="fas circle" color="success" class="small" />
      <span class="text-success ml-2 pl-1 mr-3">Connected</span>
      <BaseIcon name="fas circle" color="warning" class="small" />
      <span class="text-warning ml-2 pl-1 mr-3">Connecting</span>
      <BaseIcon name="fas circle" color="danger" class="small" />
      <span class="text-danger ml-2 pl-1">Disconnected</span>
    </div>
    <div class="mt-4">
      <div v-for="element in status" :key="element.shard" class="d-inline mr-2">
        <BaseButton v-b-popover.hover.top="popoverContent(element)" class="status-shard p-0 mb-2">
          <span
            class="h6 font-weight-bold"
            :class="{
              'text-success': element.status === 'Connected',
              'text-warning': element.status !== 'Connected' && element.status !== 'Disconnected',
              'text-danger': element.status === 'Disconnected',
            }"
          >
            {{ element.shard }}
          </span>
        </BaseButton>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  async asyncData({ $axios, $fatal }) {
    return {
      status: await $axios.$get('/status').catch($fatal),
      stats: await $axios.$get('/stats').catch($fatal),
    }
  },
  data() {
    return {
      interval: '',
    }
  },
  head: {
    title: 'Status',
  },
  computed: {
    connectedShards() {
      return this.status.filter(element => element.status === 'Connected').length
    },
    connectedPercent() {
      return Math.floor((this.connectedShards / this.status.length) * 100)
    },
  },
  mounted() {
    this.interval = setInterval(() => this.$nuxt.refresh(), 30000)
  },
  beforeDestroy() {
    clearInterval(this.interval)
  },
  methods: {
    durationSince(timestamp) {
      if (timestamp === '0001-01-01T00:00:00') {
        return 'Never'
      }

      const diff = new Date() - new Date(timestamp + 'Z')
      const result = []

      const seconds = Math.floor((diff / 1000) % 60)
      const minutes = Math.floor((diff / (1000 * 60)) % 60)
      const hours = Math.floor((diff / (1000 * 60 * 60)) % 24)
      const days = Math.floor(diff / (1000 * 60 * 60 * 24))

      if (days) result.push(`${days}d`)
      if (hours) result.push(`${hours}h`)
      if (minutes) result.push(`${minutes}m`)
      if (seconds) result.push(`${seconds}s`)

      return result.join(' ')
    },
    popoverContent(shard) {
      return {
        content: `
          <p class="h6 font-weight-bold mb-2">Shard ${shard.shard}</p>
          <p class="mb-0">Status: ${shard.status}</p>
          <p class="mb-0">Latency: ${shard.latency}ms</p>
          <p class="mb-0">Last heartbeat: ${this.durationSince(shard.last_ack)}</p>
        `,
        html: true,
      }
    },
  },
}
</script>

<style scoped lang="scss">
.status-shard {
  height: 3.5em;
  width: 3.5em;
  background-color: $dark !important;
  border: none !important;
}

.status-legend {
  ::v-deep .icon-shape {
    width: 1em;
    padding: 0.5em 0;
  }
}

.status-alert.alert-success {
  background-color: darken($success, 5%);
}
</style>
