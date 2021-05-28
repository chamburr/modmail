import Vue from 'vue'

const instance = new Vue()

function showModal(description, options) {
  return instance.$bvModal.msgBoxConfirm(description, {
    centered: true,
    hideHeaderClose: false,
    headerBgVariant: 'dark',
    bodyBgVariant: 'dark',
    footerBgVariant: 'dark',
    okVariant: 'success',
    cancelVariant: 'gray',
    ...options,
  })
}

export default (context, inject) => {
  inject('modal', (description, options) => {
    if (process.server) return
    return showModal(description, options)
  })
}
