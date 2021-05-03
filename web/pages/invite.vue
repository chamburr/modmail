<template>
  <div>
    <Heading title="Redirecting..." />
  </div>
</template>

<script>
export default {
  head: {
    title: 'Invite',
  },
  mounted() {
    window.location.href =
      'https://discord.com/oauth2/authorize?client_id=575252669443211264&permissions=268823640&response_type=code&redirect_uri=https%3A%2F%2Fmodmail.xyz%2Fwelcome&scope=bot+applications.commands'
  },
}
</script>
