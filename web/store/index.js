export const state = () => ({
  modules: [],
})

export const mutations = {
  setModules(state, modules) {
    state.modules = [...modules]
  },
}

export const getters = {
  modules(state) {
    return [...state.modules]
  },
}
