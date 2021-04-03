export default async ({ $axios, $fatal, store, route }) => {
  const id = route.params.id

  if (store.getters['guild/isNull'] || store.getters['guild/id'] !== id) {
    const guild = await $axios.$get(`/guilds/${id}`).catch($fatal)
    const config = await $axios.$get(`/guilds/${id}/settings`).catch($fatal)
    const player = await $axios.$get(`/guilds/${id}/player`).catch(err => {
      if (err.response.status !== 400) $fatal(err)
    })
    const queue = await $axios.$get(`/guilds/${id}/queue`).catch(err => {
      if (err.response.status !== 400) $fatal(err)
    })
    const permission = await $axios.$get(`/users/@me/guilds/${id}`).catch($fatal)

    store.commit('guild/set', guild)
    store.commit('guild/setConfig', config)
    store.commit('guild/setPlayer', player || {})
    store.commit('guild/setQueue', queue || [])
    store.commit('guild/setPermission', permission)
  }
}
