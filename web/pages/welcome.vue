<template>
  <div class="text-center">
    <img src="~/static/icon.png" width="200px" alt="Icon" />
    <Heading
      title="Thank you for adding ModMail!"
      class="mt-4"
      style="padding-bottom: 0 !important"
    >
      But before you go...
      <br />
      We would like to invite you to join our community.
    </Heading>
    <p class="mb-0">As a member of our community, you will be able to:</p>
    <div class="mb-2">
      <ul class="d-inline-block text-left">
        <li>Receive the latest announcements</li>
        <li>Subscribe to bot status updates</li>
        <li>Participate in regular giveaways</li>
        <li>Get support for the ModMail bot</li>
        <li>And more...</li>
      </ul>
    </div>
    <a target="_blank" href="/support">
      <BaseButton type="primary">Join Our Community Now</BaseButton>
    </a>
  </div>
</template>

<script>
export default {
  name: 'Welcome',
}
</script>
