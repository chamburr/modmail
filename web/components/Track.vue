<template>
  <Card
    class="track-container mt-4"
    body-classes="track-card overflow-scroll-x d-flex px-0 mx-4 py-3"
    :class="{ 'bg-dark': !playing, 'track-playing': playing }"
  >
    <img class="track-icon mr-3 d-md-block rounded" :src="$track.getIcon(track)" alt="Icon" />
    <div class="flex-grow-1">
      <div class="d-flex justify-content-between text-nowrap">
        <p class="font-weight-bold mb-1 mr-3">
          <span v-if="index != null" :class="{ 'text-light': !playing }">{{ index + 1 }}.</span>
          {{ track.title }}
        </p>
        <p class="mb-1" :class="{ 'text-light': !playing }">{{ $track.getDuration(track) }}</p>
      </div>
      <div class="d-flex justify-content-between">
        <p
          v-if="!userIsNull"
          class="small mb-0 text-nowrap mr-3"
          :class="{ 'text-light': !playing }"
        >
          Added by: {{ $discord.getName(user) }}
        </p>
        <p v-else class="text-light small mb-0 text-nowrap mr-3">
          {{ track.uri }}
        </p>
        <BaseDropdown position="right" menu-classes="ml-3 mt-2 border border-light">
          <div slot="title" class="dropdown-toggle font-weight-bold small">Options</div>
          <template v-if="playerOptions && !playing">
            <BaseButton class="dropdown-item font-weight-bold track-action" @click="$emit('jump')">
              Jump to Track
            </BaseButton>
            <BaseButton
              v-if="index !== 0"
              class="dropdown-item font-weight-bold track-action"
              @click="$emit('move')"
            >
              Move Track Up
            </BaseButton>
            <BaseButton
              class="dropdown-item font-weight-bold track-action"
              @click="$emit('remove')"
            >
              Remove Track
            </BaseButton>
          </template>
          <a class="dropdown-item font-weight-bold" target="_blank" :href="track.uri">
            Open Original
          </a>
        </BaseDropdown>
      </div>
    </div>
  </Card>
</template>

<script>
export default {
  name: 'Track',
  props: {
    index: {
      type: Number,
      default: null,
    },
    track: {
      type: Object,
      default: () => ({}),
    },
    user: {
      type: Object,
      default: () => ({}),
    },
    playing: {
      type: Boolean,
      default: false,
    },
    playerOptions: {
      type: Boolean,
      default: true,
    },
  },
  computed: {
    userIsNull() {
      return this.$api.isEmpty(this.user)
    },
  },
}
</script>

<style scoped lang="scss">
.track-icon {
  width: 50px;
  height: 50px;
  object-fit: cover;
}

.track-playing {
  background-color: darken($success, 10%) !important;
}

.track-action {
  border-radius: 0;
}

.track-action:hover {
  transform: none;
}

.track-container {
  /deep/ .track-card {
    margin-bottom: calc(1rem - 200px) !important;
    padding-bottom: 200px !important;
  }

  /deep/ .track-card::-webkit-scrollbar {
    display: none;
  }
}
</style>
