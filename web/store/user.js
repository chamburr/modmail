export const state = () => ({
  user: {},
})

export const mutations = {
  set(state, user) {
    state.user = Object.assign({}, user)
  },
  reset(state) {
    state.user = {}
  },
}

export const getters = {
  get(state) {
    return {
      ...state.user,
    }
  },
  isNull(state) {
    return Object.keys(state.user).length === 0
  },
}
