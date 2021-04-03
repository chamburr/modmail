export default async ({ $getContent, store, route }) => {
  const modules = await $getContent('modules')
  const id = route.params.id

  modules.forEach(element => {
    if (element.link) {
      element.link = `/dashboard/${id}/${element.link.split('/').slice(-1)[0]}`
      if (element.link.endsWith('/')) {
        element.link = element.link.slice(0, -1)
      }
    }
  })

  store.commit('setModules', modules)
}
