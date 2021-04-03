<template>
  <div class="input-slider-container">
    <div
      ref="slider"
      class="input-slider"
      :class="{ [`slider-${type}`]: type }"
      :disabled="disabled"
    ></div>
  </div>
</template>

<script>
import noUiSlider from 'nouislider'

export default {
  name: 'BaseSlider',
  props: {
    value: {
      type: [String, Number],
      default: '',
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    range: {
      type: Object,
      default: () => ({
        min: 0,
        max: 100,
      }),
    },
    type: {
      type: String,
      default: '',
    },
    options: {
      type: Object,
      default: () => ({}),
    },
  },
  data() {
    return {
      slider: null,
    }
  },
  computed: {
    connect() {
      return Array.isArray(this.value) || [true, false]
    },
  },
  watch: {
    value(newValue) {
      this.$refs.slider.noUiSlider.set(newValue)
    },
    range(newValue) {
      this.$refs.slider.noUiSlider.updateOptions({ range: newValue })
    },
  },
  mounted() {
    this.createSlider()
  },
  methods: {
    createSlider() {
      noUiSlider.create(this.$refs.slider, {
        start: this.value,
        connect: this.connect,
        range: this.range,
        ...this.options,
      })

      const slider = this.$refs.slider.noUiSlider
      slider.on('set', values => this.$emit('input', values[0]))
      slider.on('change', values => this.$emit('change', values[0]))
      slider.on('slide', (values, handle, unencoded, tap) => {
        if (!tap) this.$emit('slide', [values[0], tap])
      })
      slider.on('end', values => this.$emit('end', values[0]))
    },
  },
}
</script>
