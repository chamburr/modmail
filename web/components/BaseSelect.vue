<template>
  <MultiSelect
    class="select-container"
    :value="realValue"
    :track-by="modelKey"
    :options="options"
    :label="label"
    v-bind="$attrs"
    @input="emitEvent"
    @search-change="$emit('search-change', $event)"
  >
    <template slot="noOptions">Oops! No result found.</template>
    <template slot="noResult">Oops! No result found.</template>
  </MultiSelect>
</template>

<script>
import MultiSelect from 'vue-multiselect'
import 'vue-multiselect/dist/vue-multiselect.min.css'

export default {
  name: 'BaseSelect',
  components: { MultiSelect },
  props: {
    modelKey: {
      type: String,
      default: '',
    },
    value: {
      type: [String, Number, Boolean, Array, Object],
      default: '',
    },
    options: {
      type: Array,
      default: () => [],
    },
    label: {
      type: String,
      default: '',
    },
  },
  computed: {
    realValue() {
      if (this.modelKey && this.value != null) {
        if (Array.isArray(this.value)) {
          return this.value.map(element => this.getRealValue(element))
        }
        return this.getRealValue(this.value)
      }
      return this.value
    },
  },
  methods: {
    emitEvent($event) {
      if (this.modelKey && $event != null) {
        if (Array.isArray($event)) {
          this.$emit(
            'input',
            $event.map(element => element[this.modelKey])
          )
        } else {
          this.$emit('input', $event[this.modelKey])
        }
      } else {
        this.$emit('input', $event)
      }
    },
    getRealValue(value) {
      const element = this.options.find(element => element[this.modelKey] === value)
      return {
        [this.label]: element ? element[this.label] : 'Unknown',
        [this.modelKey]: value,
      }
    },
  },
}
</script>

<style scoped lang="scss">
.select-container {
  /deep/ .multiselect__tags,
  /deep/ .multiselect__single,
  /deep/ .multiselect__input,
  /deep/ .multiselect__content,
  /deep/ .multiselect__option--selected {
    font-size: 1rem;
    background-color: $dark;
    color: white;
    border: none;
  }

  /deep/ .multiselect__tags {
    padding-top: 10px;
  }

  /deep/ .multiselect__tag {
    background-color: $primary;
  }

  /deep/ .multiselect__option--selected.multiselect__option--highlight {
    background-color: #ff6a6a;
  }

  /deep/ .multiselect__placeholder {
    padding-left: 5px;
    padding-top: 0;
    padding-bottom: 10px;
    margin-bottom: 0;
  }

  /deep/ .multiselect__content-wrapper {
    border: none;
    background-color: $dark;
  }

  /deep/ .multiselect__input::placeholder {
    color: $gray-600;
  }

  /deep/ .multiselect__tag-icon::after {
    color: white;
  }

  /deep/ .multiselect__tag-icon:hover {
    background-color: $danger;
  }

  /deep/ .multiselect__spinner {
    background-color: $gray-900;
    height: 90%;
  }
}
</style>
