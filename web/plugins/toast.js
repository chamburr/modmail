import Vue from 'vue'

const instance = new Vue()

function showToast(title, description, variant) {
  instance.$bvToast.toast(description, {
    title,
    variant,
    autoHideDelay: 3000,
  })
}

export default (context, inject) => {
  inject('toast', {
    success(description) {
      if (process.server) return
      showToast('Success', description, 'success')
    },
    danger(description) {
      if (process.server) return
      showToast('An Error Occurred', description, 'danger')
    },
    successComplex(title, description) {
      if (process.server) return
      showToast(title, description, 'success')
    },
    dangerComplex(title, description) {
      if (process.server) return
      showToast(title, description, 'danger')
    },
  })
}
