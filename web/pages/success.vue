<template>
  <div class="text-center">
    <img src="~/static/icon.png" width="200px" alt="Icon" />
    <Heading title="Thank You" class="mt-4" style="padding-bottom: 0 !important">
      ... for keeping the bot alive!
    </Heading>
    <p class="mb-4">
      Please join our support server to receive the rewards.
      <br />
      Also, let us know if you need help with the bot!
      <br />
      We'll be happy to help you. :)
    </p>
    <a target="_blank" href="/support">
      <BaseButton type="primary">Support Server</BaseButton>
    </a>
  </div>
</template>

<script>
export default {
  name: 'Success',
}
</script>
