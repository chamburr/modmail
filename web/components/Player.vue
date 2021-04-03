<template>
  <Card class="bg-dark" body-classes="d-flex flex-wrap align-items-center px-0 mx-4 py-3">
    <div
      class="d-flex flex-wrap flex-lg-nowrap justify-content-center justify-content-lg-between w-100"
    >
      <div class="d-flex flex-nowrap overflow-auto mr-3 scrollbar-none">
        <img
          id="player-icon"
          class="mr-3 d-md-block rounded"
          :src="$track.getIcon(track)"
          alt="Icon"
        />
        <div class="d-flex flex-column flex-grow-1 justify-content-between text-nowrap">
          <p class="font-weight-bold mb-1">
            {{ track ? track.title : 'Nothing is playing!' }}
          </p>
          <p class="text-light small mb-0">Added by: {{ $discord.getName(user) }}</p>
        </div>
      </div>
      <div class="d-flex mt-2 mt-lg-0 align-items-center">
        <div class="d-flex align-items-center">
          <BaseIcon class="player-control" path="shuffle" @click="$emit('shuffle')" />
          <BaseIcon class="player-control" name="fas step-backward" @click="backward" />
          <BaseIcon class="player-control" :name="playIcon" @click="changePaused" />
          <BaseIcon class="player-control" name="fas step-forward" @click="forward" />
          <BaseIcon class="player-control" :path="repeatIcon" @click="changeLooping" />
        </div>
        <div id="player-volume" class="d-none d-md-flex flex-column text-center ml-4 mr-2">
          <BaseSlider
            v-model.number="realVolume"
            :range="{ min: 0, max: 200 }"
            @change="changeVolume($event)"
          />
          <span class="small text-light">volume</span>
        </div>
      </div>
    </div>
    <div id="player-time" class="d-flex align-items-center pt-0 pt-lg-2">
      <span class="small text-light mr-3">{{ $track.getDuration({ length: position }) }}</span>
      <BaseSlider
        v-model.number="realPosition"
        :range="{ min: 0, max: track ? track.length : 1 }"
        @change="changePosition($event)"
        @slide="startSliding"
        @end="stopSliding"
      />
      <span class="small text-light ml-3">{{ $track.getDuration(track) }}</span>
    </div>
  </Card>
</template>

<script>
export default {
  name: 'Player',
  props: {
    position: {
      type: Number,
      default: 0,
    },
    volume: {
      type: Number,
      default: 100,
    },
    paused: {
      type: Boolean,
      default: false,
    },
    looping: {
      type: String,
      default: '',
    },
    track: {
      type: Object,
      default: null,
    },
    user: {
      type: Object,
      default: null,
    },
  },
  data() {
    return {
      realVolume: this.volume,
      realPosition: this.position,
      sliding: false,
    }
  },
  computed: {
    playIcon() {
      if (this.paused) return 'fas play'
      else return 'fas pause'
    },
    repeatIcon() {
      if (this.looping === 'queue') return 'repeat'
      else if (this.looping === 'track') return 'repeat-once'
      else return 'repeat-off'
    },
  },
  watch: {
    volume(newValue) {
      if (newValue === -1) return
      this.realVolume = newValue
    },
    position(newValue) {
      if (newValue === -1 || this.sliding) return
      this.realPosition = newValue
    },
  },
  methods: {
    startSliding() {
      this.sliding = true
    },
    stopSliding() {
      this.sliding = false
    },
    backward() {
      if (!this.track) return
      this.$emit('backward')
    },
    forward() {
      if (!this.track) return
      this.$emit('forward')
    },
    changePaused() {
      this.$emit('paused', !this.paused)
    },
    changeLooping() {
      this.$emit(
        'looping',
        this.looping === 'queue' ? 'track' : this.looping === 'track' ? 'none' : 'queue'
      )
    },
    changeVolume(volume) {
      this.$emit('volume', Math.round(volume))
    },
    changePosition(position) {
      if (!this.track) return
      this.$emit('position', Math.round(position))
    },
  },
}
</script>

<style lang="scss" scoped>
#player-icon {
  width: 50px;
  height: 50px;
  object-fit: cover;
}

#player-time {
  flex-basis: 100%;
}

#player-time div {
  flex-grow: 1;
}

#player-volume {
  width: 80px;
}

#player-volume .input-slider-container {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  margin-bottom: -10px;
  margin-top: 0;
}

.player-control {
  width: 2.5em;
  height: initial;
}

.player-control:hover {
  cursor: pointer;
}
</style>
