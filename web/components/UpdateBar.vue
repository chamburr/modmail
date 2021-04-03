<template>
  <div class="mt-4 d-flex justify-content-between flex-wrap flex-md-nowrap">
    <div>
      <BaseButton type="success" @click="$emit('save', $event)">Save</BaseButton>
      <BaseButton v-if="changed" type="primary" @click="$emit('reset', $event)">
        Reset Changes
      </BaseButton>
    </div>
    <div v-if="changed" class="d-flex flex-column justify-content-center">
      <p class="mb-0 mt-2 mt-md-0 text-danger">You have unsaved changes.</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'UpdateAction',
  props: {
    changed: {
      type: Boolean,
    },
  },
}
</script>
