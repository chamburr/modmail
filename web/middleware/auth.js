export default async ({ $axios, $fatal, store, redirect, route }) => {
  if (store.getters['user/isNull']) {
    const user = await $axios.$get('/users/@me').catch(err => {
      if (err.response.status !== 401) $fatal(err)
      else redirect(`/login?redirect=${encodeURIComponent(route.fullPath)}`)
    })
    store.commit('user/set', user || {})
  }

  if (store.getters['user/isGuildsNull']) {
    const guilds = await $axios.$get('/users/@me/guilds').catch(err => {
      if (err.response.status !== 401) $fatal(err)
      else redirect(`/login?redirect=${encodeURIComponent(route.fullPath)}`)
    })
    store.commit('user/setGuilds', guilds || [])
  }
}
